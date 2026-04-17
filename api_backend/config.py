import mysql.connector
from flask import jsonify


DB_CONFIG= {
    "host": "localhost",
    "user": "cuti",
    "password": "nueva123",
    "database": "prode_mundial"
}

FASES_VALIDAS = ["grupos", "deciseis", "octavos", "cuartos", "semis", "final"]

'''
------------FUNCIONES DE CONFIGURACION Y UTILIDAD----------------
'''
def connect_db():
    return mysql.connector.connect(**DB_CONFIG)


def hacer_error(code, message, status):
    #funcion para crear codigos de error
    return jsonify({"error": [{
        "code": code,
        "message": message,
        "level": "error"

        }]
    }), status

def paginar(query_total, query_paginada, base_url, limit, offset):
    """
    query_total: resultado de COUNT(*) con los filtros aplicados
    query_paginada: lista de resultados ya con LIMIT y OFFSET
    base_url: URL base del endpoint (sin query params)
    """
    total = query_total
    limit = max(1, limit)   # mínimo 1
    offset = max(0, offset) # mínimo 0

    # Última página: el offset del último "bloque"
    if total == 0:
        last_offset = 0
    else:
        last_offset = ((total - 1) // limit) * limit

    links = {
        "_first": {"href": f"{base_url}?_limit={limit}&_offset=0"},
        "_last":  {"href": f"{base_url}?_limit={limit}&_offset={last_offset}"},
    }

    if offset > 0:
        prev_offset = max(0, offset - limit)
        links["_prev"] = {"href": f"{base_url}?_limit={limit}&_offset={prev_offset}"}

    if offset + limit < total:
        links["_next"] = {"href": f"{base_url}?_limit={limit}&_offset={offset + limit}"}

    return links