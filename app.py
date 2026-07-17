"""
app.py
Backend Flask de la plataforma de monitoreo IoT.
- Arranca el hilo del simulador en segundo plano al iniciar.
- Expone la API REST que consume el dashboard.
- Sirve el dashboard (templates/index.html).
"""

from flask import Flask, jsonify, render_template

from database import inicializar_base_datos, get_connection
from simulator import iniciar_simulador_en_hilo, forzar_falla

app = Flask(__name__)

# --- Inicializacion al arrancar la app ---
inicializar_base_datos()
iniciar_simulador_en_hilo(intervalo_segundos=5)  # actualiza los 5 nodos cada 5 segundos


# --- Ruta que sirve el dashboard ---
@app.route("/")
def index():
    return render_template("index.html")


# --- API: lista de todos los nodos con su estado actual ---
@app.route("/api/nodos", methods=["GET"])
def obtener_nodos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nodos ORDER BY id")
    nodos = [dict(fila) for fila in cursor.fetchall()]
    conn.close()
    return jsonify(nodos)


# --- API: detalle de un nodo especifico ---
@app.route("/api/nodos/<int:nodo_id>", methods=["GET"])
def obtener_nodo(nodo_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nodos WHERE id = ?", (nodo_id,))
    fila = cursor.fetchone()
    conn.close()

    if fila is None:
        return jsonify({"error": "Nodo no encontrado"}), 404

    return jsonify(dict(fila))


# --- API: historial de un nodo, para la grafica ---
@app.route("/api/historial/<int:nodo_id>", methods=["GET"])
def obtener_historial(nodo_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT temperatura, cpu, timestamp
        FROM historial
        WHERE nodo_id = ?
        ORDER BY id DESC
        LIMIT 20
    """, (nodo_id,))
    filas = [dict(fila) for fila in cursor.fetchall()]
    conn.close()

    filas.reverse()  # para que la grafica se vea de mas antiguo a mas reciente
    return jsonify(filas)


# --- API: fuerza una falla en un nodo especifico (boton "Simular Falla") ---
@app.route("/api/simular_falla/<int:nodo_id>", methods=["POST"])
def simular_falla(nodo_id):
    estado, temperatura = forzar_falla(nodo_id)
    return jsonify({
        "nodo_id": nodo_id,
        "estado": estado,
        "temperatura": temperatura,
        "mensaje": f"Temperatura critica: {temperatura}°C"
    })


# --- API: lista solo los nodos en Advertencia o Falla ---
@app.route("/api/alertas", methods=["GET"])
def obtener_alertas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM nodos
        WHERE estado IN ('Advertencia', 'Falla')
        ORDER BY id
    """)
    alertas = [dict(fila) for fila in cursor.fetchall()]
    conn.close()
    return jsonify(alertas)


if __name__ == "__main__":
    app.run(debug=True)