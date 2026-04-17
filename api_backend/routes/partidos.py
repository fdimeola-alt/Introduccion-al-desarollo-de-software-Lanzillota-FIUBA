from flask import request, jsonify, Blueprint
from config import FASES_VALIDAS, connect_db, hacer_error, paginar

partidos_bp = Blueprint('partidos', __name__)

BASE_URL_PARTIDOS = "/partidos"

'''

---------------------RUTAS PARA PARTIDOS-------------------

'''

@partidos_bp.route("/partidos", methods=["GET"])
def listar_partidos():
    #parámetros de paginacion
    limit  = request.args.get("_limit",  10,  type=int)
    offset = request.args.get("_offset",  0,  type=int)
 
    #filtros opcionales
    equipo = request.args.get("equipo")
    fecha  = request.args.get("fecha")
    fase   = request.args.get("fase")
 
    # validar fase si viene
    if fase and fase not in FASES_VALIDAS:
        return hacer_error("FASE_INVALIDA", f"La fase debe ser una de: {FASES_VALIDAS}", 400)
 
    #construir cláusula WHERE dinámicamente
    condiciones = []
    params      = []
 
    if equipo:
        condiciones.append("(equipo_local = %s OR equipo_visitante = %s)")
        params.extend([equipo, equipo])
    if fecha:
        condiciones.append("fecha = %s")
        params.append(fecha)
    if fase:
        condiciones.append("fase = %s")
        params.append(fase)
 
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
 
    conn   = connect_db()
    cursor = conn.cursor(dictionary=True)
 
    # total para los links HATEOAS
    cursor.execute(f"SELECT COUNT(*) AS total FROM partidos {where}", params)
    total = cursor.fetchone()["total"]
    
    # si no hay partidos que mostrar devuelve 204 No Content
    if total == 0:
        cursor.close()
        conn.close()
        return "", 204
 
    # página pedida
    cursor.execute(
        f"""SELECT id, equipo_local, equipo_visitante, fecha, fase
            FROM partidos {where}
            ORDER BY id
            LIMIT %s OFFSET %s""",
        params + [limit, offset]
    )
    partidos = cursor.fetchall()
    cursor.close()
    conn.close()
 
    # serializar fechas a string
    for p in partidos:
        if p["fecha"]:
            p["fecha"] = str(p["fecha"])
 
    links = paginar(total, partidos, BASE_URL_PARTIDOS, limit, offset)
 
    return jsonify({"partidos": partidos, "_links": links}), 200


@partidos_bp.route("/partidos", methods=["POST"])
def crear_partido():
    info = request.get_json()

    if not info:
        return hacer_error("BODY_REQUERIDO", "El body no puede estar vacío", 400)

    # validamos que vengan todos los campos obligatorios
    for campo in ["equipo_local", "equipo_visitante", "fecha", "fase"]:
        if not info[campo]:
            # si el campo no existe devuelve None en vez de lanzar excepción
            return hacer_error("FALTA_INFORMACION", f"Falta información para el '{campo}'", 400)

    if info["fase"] not in FASES_VALIDAS:
        return hacer_error("FASE_INVALIDA", f"La fase debe ser una de: {FASES_VALIDAS}", 400)

    conn   = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO partidos (equipo_local, equipo_visitante, fecha, fase)
        VALUES (%s, %s, %s, %s)
    """, (info["equipo_local"], info["equipo_visitante"], info["fecha"], info["fase"]))


    conn.commit()
    cursor.close()
    conn.close()

 
    return "", 201


@partidos_bp.route("/partidos/<int:partido_id>", methods=["PUT"])
def remplazar_partido(partido_id):
    datos = request.get_json()

    if not datos:
        return hacer_error("BODY_REQUERIDO", "El body no puede estar vacío", 400)

    for campo in ["equipo_local", "equipo_visitante", "fecha", "fase"]:
        if not datos[campo]:
            return hacer_error("FALTA_INFORMACION", f"Falta información para el '{campo}'", 400)

    if datos["fase"] not in FASES_VALIDAS:
        return hacer_error("FASE_INVALIDA", f"La fase debe ser una de: {FASES_VALIDAS}", 400)

    conn   = connect_db()
    cursor = conn.cursor()

    cursor.execute(""" SELECT id FROM partidos WHERE id = %s""", (partido_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return hacer_error("PARTIDO_NO_EXISTE", "No se encontro el id del partido", 404)

    cursor.execute("""
        UPDATE partidos
        SET equipo_local = %s, equipo_visitante = %s, fecha = %s, fase = %s
        WHERE id = %s
    """, (datos["equipo_local"], datos["equipo_visitante"], datos["fecha"], datos["fase"], partido_id))

    conn.commit()
    cursor.close()
    conn.close()
    return "", 204



@partidos_bp.route("/partidos/<int:partido_id>", methods=["GET"])
def detalle_partido(partido_id):

    conn   = connect_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, equipo_local, equipo_visitante, fecha, fase, gol_local, gol_visitante
        FROM partidos
        WHERE id = %s""", (partido_id,))

    partido = cursor.fetchone()
    cursor.close()
    conn.close()

    if not partido:
        return hacer_error("PARTIDO_NO_EXISTE", "No se encontro el id del partido", 404)

    # el resultado solo existe si los goles ya fueron cargados
    resultado = None
    if partido["gol_local"] is not None and partido["gol_visitante"] is not None:
        resultado = {
            "local":     partido["gol_local"],
            "visitante": partido["gol_visitante"]
        }
    
    return jsonify ({
        "id": partido["id"],
        "equipo_local": partido["equipo_local"],
        "equipo_visitante": partido["equipo_visitante"],
        "fecha": partido["fecha"],
        "fase": partido["fase"],
        "resultado": resultado
    })


# actuliza el resultado por completo de un partido dado su id utilizando PUT
#solo se pueden cargar resultados de partidos ya existentes
@partidos_bp.route("/partidos/<int:partido_id>/resultado", methods=["PUT"])
def remplazar_resultado(partido_id):
    datos=request.get_json()

    if not datos:
        return hacer_error("BODY_REQUERIDO", "El body no puede estar vacío", 400)
    
    conn   = connect_db()
    cursor = conn.cursor()

    #busca el id del partido, si no existe devuelve error
    cursor.execute(""" SELECT id FROM partidos WHERE id = %s""", (partido_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return hacer_error("PARTIDO_NO_EXISTE", "No se encontro el id del partido", 404)
    
    #se usa el mismo error para validar que vengan ambos goles, si no existe el campo o es null devuelve error
    for campo in ["gol_local", "gol_visitante"]:
        if  datos[campo] is None:
            return hacer_error("CAMPO_REQUERIDO", f"El campo '{campo}' es obligatorio", 400)
        
    cursor.execute("""
        UPDATE partidos
        SET gol_local = %s, gol_visitante = %s
        WHERE id = %s
    """, (datos["gol_local"], datos["gol_visitante"], partido_id))

    conn.commit()
    cursor.close()
    conn.close()
    return "", 204


@partidos_bp.route('/partidos/<int:id>', methods=['PATCH'])
def actualizar_parcial_partido(id):
    datos = request.get_json()

    campos_validos = ['equipo_local', 'equipo_visitante', 'fecha', 'fase']

    if not datos or not any(campo in datos for campo in campos_validos):
        return hacer_error("CAMPO_REQUERIDO",
            'Debes enviar al menos uno de los campos: equipo_local, equipo_visitante, fecha, fase', 400
        )
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM partidos WHERE id = %s", (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return hacer_error("PARTIDO_NO_EXISTE", "No se encontro el id del partido", 404)
    
    cursor.execute("""
        UPDATE partidos
        SET equipo_local = COALESCE(%s, equipo_local),
            equipo_visitante = COALESCE(%s, equipo_visitante),
            fecha = COALESCE(%s, fecha),
            fase = COALESCE(%s, fase)
        WHERE id = %s
    """, (datos.get('equipo_local'), datos.get('equipo_visitante'), datos.get('fecha'), datos.get('fase'), id))

    conn.commit()
    cursor.close()
    conn.close()
    return '', 204

@partidos_bp.route('/partidos/<int:id>', methods=['DELETE'])
def eliminar_partido(id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM partidos WHERE id = %s", (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return hacer_error("PARTIDO_NO_EXISTE", "No se encontro el id del partido", 404)

    cursor.execute("DELETE FROM partidos WHERE id = %s", (id,))

    conn.commit()
    cursor.close()
    conn.close()
    return '', 204

@partidos_bp.route("/partidos/<int:id>/prediccion", methods=["POST"])
def crear_prediccion(id):
    datos = request.get_json()
 
    if not datos:
        return hacer_error("BODY_REQUERIDO", "El body no puede estar vacío", 400)
 
    for campo in ["id_usuario", "gol_local", "gol_visitante"]:
        if datos.get(campo) is None:
            return hacer_error("CAMPO_REQUERIDO", f"El campo '{campo}' es obligatorio", 400)
 
    conn   = connect_db()
    cursor = conn.cursor(dictionary=True)
 
    # verificar que el partido existe
    cursor.execute("SELECT id, gol_local FROM partidos WHERE id = %s", (id,))
    partido = cursor.fetchone()
    if not partido:
        cursor.close()
        conn.close()
        return hacer_error("NO_ENCONTRADO", "Partido no encontrado", 404)

    
        # no se puede predecir un partido ya jugado
    if partido["gol_local"] is not None:
        cursor.close()
        conn.close()
        return hacer_error("PARTIDO_YA_JUGADO", "El partido ya tiene resultado cargado", 400)
 
    # verificar que el usuario existe
    cursor.execute("SELECT id FROM usuarios WHERE id = %s", (datos["id_usuario"],))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return hacer_error("USUARIO_NO_EXISTE", "No se encontró el id del usuario", 404)
 
    # verificar que no haya predicción duplicada para ese usuario+partido
    cursor.execute(
        "SELECT id FROM predicciones WHERE id_partido = %s AND id_usuario = %s",
        (id, datos["id_usuario"])
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return hacer_error("PREDICCION_DUPLICADA",
            "El usuario ya tiene una predicción para este partido", 409)
 
    cursor.execute("""
        INSERT INTO predicciones (id_partido, id_usuario, gol_local, gol_visitante)
        VALUES (%s, %s, %s, %s)
    """, (id, datos["id_usuario"], datos["gol_local"], datos["gol_visitante"]))

    conn.commit()
    cursor.close()
    conn.close()
    return '', 204
