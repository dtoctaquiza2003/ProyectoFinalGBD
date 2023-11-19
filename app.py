from flask import Flask, render_template, request
import mysql.connector
from pymongo import MongoClient
import psycopg2
from psycopg2 import extras

app = Flask(__name__)

db = None  # Inicialmente, la base de datos MongoDB está configurada como None

@app.route('/')
def formulario():
    return render_template('formulario.html')

@app.route('/conectar_mongodb', methods=['POST','GET'])
def conectar_mongodb():
    #Configura la conexión a la base de datos MongoDB
    servidor = MongoClient('mongodb://'+request.form['mongodb_server']+':27017')
    if request.method == 'POST':
        pass

    # Obtener la lista de bases de datos disponibles
    bases_de_datos = servidor.list_database_names()
        
    # Crear un diccionario para almacenar las colecciones de cada base de datos
    colecciones_por_base = {}
        
    # Obtener las colecciones para cada base de datos
    for base_de_datos in bases_de_datos:
        db = servidor[base_de_datos]
        colecciones = db.list_collection_names()
        colecciones_por_base[base_de_datos] = colecciones
        
    return render_template('mongo.html', colecciones_por_base=colecciones_por_base)

@app.route('/conectar_postgres', methods=['POST'])
def conectar_postgres():
    if request.method == 'POST':
        servidor = request.form['postgres_server']
        usuario = request.form['postgres_username']
        contraseña = request.form['postgres_password']
        nombre_base_de_datos = request.form['postgres_database']

        puerto_postgres = 5432
        
        # Conexión a PostgreSQL
        try:
            conn = psycopg2.connect(
                host=servidor,
                user=usuario,
                password=contraseña,
                dbname=nombre_base_de_datos,
                port = puerto_postgres,
                client_encoding ='utf-8'
            )

            # Obtener un cursor usando RealDictCursor
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            # Consulta para obtener todas las tablas en la base de datos
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tablas = cursor.fetchall()

            # Cerrar el cursor y la conexión
            cursor.close()
            conn.close()

            # Renderizar la plantilla con la lista de tablas
            return render_template('tablas_postgres.html', tablas=tablas)

        except Exception as e:
            return f"Error de conexión a PostgreSQL: {e}"


if __name__ == '__main__':
    app.run(debug=True)