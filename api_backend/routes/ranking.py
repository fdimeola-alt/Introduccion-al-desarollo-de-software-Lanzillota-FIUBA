from flask import request, jsonify, Blueprint
from config import connect_db, hacer_error, paginar

ranking_bp = Blueprint('ranking', __name__)

BASE_URL_RANKING = "/ranking"

'''
---------------------RANKING-------------------
Criterio de puntos:
  - Resultado exacto (mismo marcador)  → 3 puntos
  - Ganador/empate correcto, marcador distinto → 1 punto
  - Resultado incorrecto               → 0 puntos

Solo se consideran partidos que ya tienen resultado cargado
(gol_local y gol_visitante NOT NULL).
'''


@ranking_bp.route("/ranking", methods=["GET"])
def obtener_ranking():
    limit  = request.args.get("_limit",  10, type=int)
    offset = request.args.get("_offset",  0, type=int)

    conn   = connect_db()
    cursor = conn.cursor(dictionary=True)

    #  puntos por predicción
    # Resultado exacto     → 3 pts
    # Ganador correcto     → 1 pt  (sign de diferencia de goles coincide)
    # Incorrecto           → 0 pts
    sql_puntos = """
        SELECT
            pr.id_usuario,
            SUM(
                CASE
                    -- marcador exacto
                    WHEN pr.gol_local     = pa.gol_local
                     AND pr.gol_visitante = pa.gol_visitante
                    THEN 3
                    -- ganador / empate correcto pero marcador distinto
                    WHEN SIGN(pr.gol_local - pr.gol_visitante)
                       = SIGN(pa.gol_local  - pa.gol_visitante)
                    THEN 1
                    ELSE 0
                END
            ) AS puntos
        FROM predicciones pr
        JOIN partidos pa ON pr.id_partido = pa.id
        WHERE pa.gol_local IS NOT NULL
          AND pa.gol_visitante IS NOT NULL
        GROUP BY pr.id_usuario
    """

    # total de usuarios con al menos una predicción evaluable
    cursor.execute(f"SELECT COUNT(*) AS total FROM ({sql_puntos}) AS sub")
    total = cursor.fetchone()["total"]

    if total == 0:
        cursor.close()
        conn.close()
        return "", 204

    # resultado paginado, ordenado por puntos desc, id_usuario asc (desempate)
    cursor.execute(
        f"""SELECT id_usuario, puntos
            FROM ({sql_puntos}) AS ranking
            ORDER BY puntos DESC, id_usuario ASC
            LIMIT %s OFFSET %s""",
        (limit, offset)
    )
    ranking = cursor.fetchall()
    cursor.close()
    conn.close()

    links = paginar(total, ranking, BASE_URL_RANKING, limit, offset)

    return jsonify({"ranking": ranking, "_links": links}), 200
