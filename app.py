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

def obtener_tablas(servidor, usuario, contraseña, nombre_base):
    # Función para obtener las tablas de una base de datos específica

    # Conexión a MySQL especificando el servidor, usuario, contraseña y base de datos
    conn = mysql.connector.connect(
        host=servidor,
        user=usuario,
        password=contraseña,
        database=nombre_base
    )

    # Crear un cursor para ejecutar consultas SQL
    cursor = conn.cursor()

    # Obtener las tablas de la base de datos actual
    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()

    # Convertir el resultado a una lista de nombres de tablas
    lista_de_tablas = [tabla[0] for tabla in tablas]

    # Cerrar el cursor y la conexión
    cursor.close()
    conn.close()

    return lista_de_tablas

@app.route('/conectar_mysql', methods=['POST'])
def conectar_mysql():
    if request.method == 'POST':
        servidor = request.form['mysql_server']
        usuario = request.form['mysql_username']
        contraseña = request.form['mysql_password']

        try:
            # Conexión a MySQL sin especificar la base de datos
            conn = mysql.connector.connect(
                host=servidor,
                user=usuario,
                password=contraseña
            )

            # Crear un cursor para ejecutar consultas SQL
            cursor = conn.cursor()

            # Obtener todas las bases de datos
            cursor.execute("SHOW DATABASES")
            bases_de_datos = cursor.fetchall()

            # Inicializar un diccionario para almacenar las tablas de cada base de datos
            diccionario_tablas = {}

            for db in bases_de_datos:
                nombre_base = db[0]

                # Filtrar bases de datos del sistema
                if not nombre_base.startswith(('mysql', 'information_schema', 'performance_schema')):
                    # Obtener las tablas utilizando la función auxiliar
                    lista_de_tablas = obtener_tablas(servidor, usuario, contraseña, nombre_base)

                    # Almacenar las tablas en el diccionario
                    diccionario_tablas[nombre_base] = lista_de_tablas

            # Cerrar el cursor y la conexión
            cursor.close()
            conn.close()

            # Renderizar el template con la información obtenida
            return render_template('mysql.html', bases_y_tablas=diccionario_tablas)
        except mysql.connector.Error as err:
            return jsonify({'error': f"Error de conexión a MySQL: {err}"}), 500


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