import mysql.connector
from flask import request, jsonify, Blueprint
from config import connect_db, hacer_error, paginar

usuarios_bp = Blueprint('usuarios', __name__)

BASE_URL_USUARIOS = "/usuarios"

'''
---------------------PARTE DE LOS USUARIOS-------------------

'''

# mismo que get /partidos pero para usuarios, no tiene filtros opcionales, solo paginación
@usuarios_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    limit  = request.args.get("_limit",  10, type=int)
    offset = request.args.get("_offset",  0, type=int)
 
    conn   = connect_db()
    cursor = conn.cursor(dictionary=True)
 
    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
    total = cursor.fetchone()["total"]
 
    if total == 0:
        cursor.close()
        conn.close()
        return "", 204
 
    cursor.execute(
        "SELECT id, nombre FROM usuarios ORDER BY id LIMIT %s OFFSET %s",
        (limit, offset)
    )
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
 
    links = paginar(total, usuarios, BASE_URL_USUARIOS, limit, offset)
 
    return jsonify({"usuarios": usuarios, "_links": links}), 200




#crea un nuevo usuario utilizando POST
@usuarios_bp.route("/usuarios", methods=["POST"])
def crear_usuario():
    info = request.get_json()

    if not info:
        return hacer_error("BODY_REQUERIDO", "El body no puede estar vacío", 400)

    # validamos que vengan todos los campos obligatorios
    for campo in ["nombre", "email"]:
        if not info[campo]:
            # si el campo no existe devuelve None en vez de lanzar excepción
            return hacer_error("FALTA_INFORMACION", f"Falta información para el '{campo}'", 400)

    conn   = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usuarios (nombre, email)
        VALUES (%s, %s)
    """, (info["nombre"], info["email"]))

    conn.commit()
    cursor.close()
    conn.close()

    return "", 201

#devuelve el detalle de un usuario dado su id utilizando GET
@usuarios_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def detalle_usuario(usuario_id):

    conn   = connect_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, nombre, email
        FROM usuarios
        WHERE id = %s""", (usuario_id,))

    usuario = cursor.fetchone()
    cursor.close()
    conn.close()

    if not usuario:
        return hacer_error("USUARIO_NO_EXISTE", "No se encontro el id del usuario", 404)

    
    return jsonify ({
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "email": usuario["email"]   
    })

#remplaza un usuario dado su id utilizando PUT
@usuarios_bp.route("/usuarios/<int:id>", methods=["PUT"])
def remplazar_usuario(id):
    datos = request.get_json()

    if not datos:
        return hacer_error("BODY_REQUERIDO", "El body no puede estar vacío", 400)

    for campo in ["nombre", "email"]:
        if not datos[campo]:
            return hacer_error("FALTA_INFORMACION", f"Falta información para el '{campo}'", 400)

    conn   = connect_db()
    cursor = conn.cursor()

    #busca que exista el usuario a remplazar, si no existe devuelve error 404
    cursor.execute(""" SELECT id FROM usuarios WHERE id = %s""", (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return hacer_error("USUARIO_NO_EXISTE", "No se encontro el id del usuario", 404)

    cursor.execute("""
        UPDATE usuarios
        SET nombre = %s, email = %s
        WHERE id = %s
    """, (datos["nombre"], datos["email"], id))

    conn.commit()
    cursor.close()
    conn.close()
    return "", 204

#elimina un usuario dado su id utilizando DELETE
@usuarios_bp.route('/usuarios/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):

    conn = connect_db()
    cursor = conn.cursor()

    #usa fetchone para verificar que el usuario a eliminar existe, si no existe devuelve error 404
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return hacer_error("USUARIO_NO_EXISTE", "No se encontro el id del usuario", 404)

    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))

    conn.commit()
    cursor.close()
    conn.close()
    return '', 204

