
from flask import Flask
from routes.partidos import partidos_bp
from routes.usuarios import usuarios_bp
import innit_sql
from routes.ranking import ranking_bp


try:
    innit_sql.init_db()
except Exception as e:
    print("Error al inicializar la base de datos:", e)

app = Flask(__name__)

app.register_blueprint(ranking_bp,)
app.register_blueprint(partidos_bp,)
app.register_blueprint(usuarios_bp,)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
