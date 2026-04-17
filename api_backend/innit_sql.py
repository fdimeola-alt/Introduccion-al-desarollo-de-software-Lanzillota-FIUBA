def init_db():
    import mysql.connector

    with open("prode_mundial.sql") as f:
        sql = f.read()

    conn = mysql.connector.connect(
        host="localhost",
        user="cuti",
        password="nueva123"
    )

    cursor = conn.cursor()
    for statement in sql.split(";"):
        if statement.strip():
            print(statement)
            cursor.execute(statement)
            conn.commit()
            print("Statement executed")

    cursor.close()
    conn.close()