"""
simulator.py
Genera datos simulados para los 5 Nodos IoT.
- Modo normal: valores aleatorios dentro de rangos "sanos" (para que la demo se vea estable).
- Modo forzado: permite poner un nodo especifico en estado de Falla al instante (boton "Simular Falla").
"""

import random
import time
import threading
from datetime import datetime

from database import get_connection


def calcular_estado(temperatura, cpu):
    """Determina el estado del nodo segun reglas simples de temperatura y cpu."""
    if temperatura > 75 or cpu > 90:
        return "Falla"
    elif temperatura > 60 or cpu > 75:
        return "Advertencia"
    else:
        return "Activo"


def generar_valores_normales():
    """Genera una lectura aleatoria dentro de rangos normales (sin falla)."""
    temperatura = round(random.uniform(25, 45), 1)
    latencia = round(random.uniform(5, 40), 1)
    cpu = round(random.uniform(15, 50), 1)
    memoria = round(random.uniform(20, 60), 1)
    usuarios = random.randint(0, 50)
    return temperatura, latencia, cpu, memoria, usuarios


def generar_valores_falla():
    """Genera una lectura con valores criticos, para forzar el estado de Falla."""
    temperatura = round(random.uniform(80, 95), 1)
    latencia = round(random.uniform(100, 200), 1)
    cpu = round(random.uniform(90, 99), 1)
    memoria = round(random.uniform(85, 99), 1)
    usuarios = random.randint(0, 50)
    return temperatura, latencia, cpu, memoria, usuarios


def actualizar_nodo(nodo_id, temperatura, latencia, cpu, memoria, usuarios):
    """
    Actualiza el estado actual del nodo en la tabla 'nodos'
    y agrega una fila nueva en 'historial'. Devuelve el estado calculado.
    """
    conn = get_connection()
    cursor = conn.cursor()

    estado = calcular_estado(temperatura, cpu)
    ahora = datetime.now().isoformat(timespec="seconds")

    cursor.execute("""
        UPDATE nodos
        SET estado = ?, temperatura = ?, latencia = ?, cpu = ?, memoria = ?,
            usuarios_conectados = ?, ultima_actualizacion = ?
        WHERE id = ?
    """, (estado, temperatura, latencia, cpu, memoria, usuarios, ahora, nodo_id))

    cursor.execute("""
        INSERT INTO historial (nodo_id, temperatura, cpu, timestamp)
        VALUES (?, ?, ?, ?)
    """, (nodo_id, temperatura, cpu, ahora))

    conn.commit()
    conn.close()
    return estado


def obtener_ids_nodos():
    """Devuelve la lista de ids de todos los nodos existentes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM nodos")
    ids = [row["id"] for row in cursor.fetchall()]
    conn.close()
    return ids


def actualizar_todos_los_nodos():
    """Genera y guarda una nueva lectura normal para cada nodo existente."""
    for nodo_id in obtener_ids_nodos():
        temperatura, latencia, cpu, memoria, usuarios = generar_valores_normales()
        actualizar_nodo(nodo_id, temperatura, latencia, cpu, memoria, usuarios)


def forzar_falla(nodo_id):
    """
    Fuerza que un nodo especifico pase a estado critico de inmediato.
    Se usara desde el boton 'Simular Falla' del dashboard (Dia 3).
    Devuelve (estado, temperatura) para poder mostrar el mensaje de alerta.
    """
    temperatura, latencia, cpu, memoria, usuarios = generar_valores_falla()
    estado = actualizar_nodo(nodo_id, temperatura, latencia, cpu, memoria, usuarios)
    return estado, temperatura


def ciclo_simulacion(intervalo_segundos=5):
    """Bucle infinito: actualiza todos los nodos cada 'intervalo_segundos'."""
    while True:
        actualizar_todos_los_nodos()
        time.sleep(intervalo_segundos)


def iniciar_simulador_en_hilo(intervalo_segundos=5):
    """
    Lanza 'ciclo_simulacion' en un hilo en segundo plano (daemon),
    para que Flask (Dia 3) pueda seguir atendiendo peticiones normalmente.
    """
    hilo = threading.Thread(target=ciclo_simulacion, args=(intervalo_segundos,), daemon=True)
    hilo.start()
    return hilo


if __name__ == "__main__":
    # Prueba manual: no lanza el hilo infinito, solo corre un ciclo una vez.
    from database import inicializar_base_datos

    inicializar_base_datos()

    print("Actualizando los 5 nodos con valores normales...")
    actualizar_todos_los_nodos()
    print("Listo. Revisa database.db para ver los nuevos valores.\n")

    print("Forzando una falla en el Nodo 3 (id=3)...")
    estado, temperatura = forzar_falla(3)
    print(f"Nodo 3 -> estado: {estado}, temperatura: {temperatura}°C")