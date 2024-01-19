from flask import Flask, render_template, request, jsonify, session
import mysql.connector
from pymongo import MongoClient
import psycopg2
from psycopg2 import extras, sql
from bson import json_util
app = Flask(_name_)
app.secret_key = 'david2003'

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

            # Almacenar la información de conexión en la sesión
            session['conexion_mysql'] = {
                'servidor': servidor,
                'usuario': usuario,
                'contraseña': contraseña
            }

            # Renderizar el template con la información obtenida
            return render_template('resultado.html', bases_y_tablas=diccionario_tablas)
        except mysql.connector.Error as err:
            return jsonify({'error': f"Error de conexión a MySQL: {err}"}), 500

@app.route('/consultar_mysql', methods=['POST'])
def consultar_mysql():
    if request.method == 'POST':
        # Recuperar la información de conexión desde la sesión
        info_conexion = session.get('conexion_mysql', None)

        # Verificar si la información de conexión está disponible
        if info_conexion:
            servidor = info_conexion['servidor']
            usuario = info_conexion['usuario']
            contraseña = info_conexion['contraseña']
            consulta_sql = request.form['consulta_sql']

            try:
                conn = mysql.connector.connect(
                    host=servidor,
                    user=usuario,
                    password=contraseña,
                )

                cursor = conn.cursor()

                # Ejecutar la consulta SQL
                cursor.execute(consulta_sql)

                # Si la consulta es un SELECT, obtener resultados
                if consulta_sql.strip().upper().startswith('SELECT'):
                    resultados = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    return jsonify(resultados)
                else:
                    # Para consultas que no son SELECT (como INSERT), realizar commit
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return jsonify({'mensaje': 'Operación de inserción exitosa'})

            except mysql.connector.Error as err:
                return jsonify({'error': f"Error al ejecutar la consulta SQL: {err}"}), 500
        else:
            return jsonify({'error': 'No se encontró información de conexión en la sesión'}), 500

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

    session['conexion_mongo'] = {
        'servidor' : request.form['mongodb_server']
    }
        
    return render_template('resultado.html', bases_y_tablas=colecciones_por_base)

@app.route('/consultar_mongodb', methods=['POST', 'GET'])
def consultar_mongodb():
    # Función para hacer consultas en MongoDB
    info_conexion = session.get('conexion_mongo', None)
    servidor = MongoClient('mongodb://' + info_conexion['servidor'] + ':27017')

    db_nombre = request.form['base']
    db = servidor[db_nombre]

    consulta_mongo = request.form['consulta_sql']

    try:
        # Realizar la consulta de manera segura utilizando métodos de pymongo
        resultado = list(eval(consulta_mongo))
    except Exception as e:
        # Manejar posibles errores en la consulta
        return jsonify({'error': str(e)})

    # Convertir ObjectId a cadenas antes de devolver el resultado JSON
    resultado_json = json_util.dumps(resultado)
    print(resultado)
    # Devolver el resultado como JSON
    return jsonify({'respuesta': resultado_json})


def obtener_tablas_pg(servidor, usuario, contraseña, nombre_base):
    # Función para obtener las tablas de una base de datos específica en PostgreSQL

    # Conexión a PostgreSQL especificando el servidor, usuario, contraseña y base de datos
    conn = psycopg2.connect(
        host=servidor,
        user=usuario,
        password=contraseña,
        database=nombre_base
    )

    # Crear un cursor para ejecutar consultas SQL
    cursor = conn.cursor()

    # Obtener las tablas de la base de datos actual
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tablas = cursor.fetchall()

    # Convertir el resultado a una lista de nombres de tablas
    lista_de_tablas = [tabla[0] for tabla in tablas]

    # Cerrar el cursor y la conexión
    cursor.close()
    conn.close()

    return lista_de_tablas

@app.route('/conectar_postgres', methods=['POST'])
def conectar_postgres():
    if request.method == 'POST':
        servidor = request.form['postgres_server']
        usuario = request.form['postgres_username']
        contraseña = request.form['postgres_password']

        try:
            # Conexión a PostgreSQL sin especificar la base de datos
            conn = psycopg2.connect(
                host=servidor,
                user=usuario,
                password=contraseña
            )

            # Crear un cursor para ejecutar consultas SQL
            cursor = conn.cursor()

            # Obtener todas las bases de datos
            cursor.execute("SELECT datname FROM pg_database")
            bases_de_datos = cursor.fetchall()

            # Inicializar un diccionario para almacenar las tablas de cada base de datos
            diccionario_tablas = {}

            for db in bases_de_datos:
                nombre_base = db[0]

                # Filtrar bases de datos del sistema
                if not nombre_base.startswith(('postgres', 'template', 'template1', 'template0')):
                    # Obtener las tablas utilizando la función auxiliar
                    lista_de_tablas = obtener_tablas_pg(servidor, usuario, contraseña, nombre_base)

                    # Almacenar las tablas en el diccionario
                    diccionario_tablas[nombre_base] = lista_de_tablas

            # Cerrar el cursor y la conexión
            cursor.close()
            conn.close()

            # Almacenar la información de conexión en la sesión
            session['conexion_postgres'] = {
                'servidor': servidor,
                'usuario': usuario,
                'contraseña': contraseña
            }

            # Renderizar el template con la información obtenida
            return render_template('resultado.html', bases_y_tablas=diccionario_tablas)
        except psycopg2.Error as err:
            return jsonify({'error': f"Error de conexión a PostgreSQL: {err}"}), 500

@app.route('/consultar_postgres', methods=['POST'])
def consultar_postgres():
    if request.method == 'POST':
        # Recuperar la información de conexión desde la sesión
        info_conexion = session.get('conexion_postgres', None)

        # Verificar si la información de conexión está disponible
        if info_conexion:
            servidor = info_conexion['servidor']
            usuario = info_conexion['usuario']
            contraseña = info_conexion['contraseña']
            base = request.form['base']
            consulta_sql = request.form['consulta_sql']

            try:
                conn = psycopg2.connect(
                    host=servidor,
                    user=usuario,
                    password=contraseña,
                    dbname=base
                )

                cursor = conn.cursor()

                # Ejecutar la consulta SQL
                cursor.execute(consulta_sql)

                # Si la consulta es un SELECT, obtener resultados
                if consulta_sql.strip().startswith('SELECT') or consulta_sql.strip.startswith('select'):
                    resultados = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    return jsonify(resultados)
                else:
                    # Para consultas que no son SELECT (como INSERT), realizar commit
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return jsonify({'mensaje': 'Operación de inserción/actualización/extracción exitosa'})

            except Exception as e:
                print(e)
                return jsonify({'error': f"Error inesperado: {e}"}), 500
        else:
            return jsonify({'error': 'No se encontró información de conexión en la sesión'}), 500

if _name_ == "_main_":
    app.run(host='0.0.0.0', port=5000)
