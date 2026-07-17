"""
database.py
Crea y administra la base de datos SQLite del proyecto.
Tablas:
  - nodos: estado actual de cada Nodo IoT virtual
  - historial: lecturas pasadas de cada nodo (para graficar tendencias)
"""

import sqlite3
from datetime import datetime

DB_NAME = "database.db"

# Nombres fijos de los 5 nodos que va a tener la plataforma
NOMBRES_NODOS = ["Nodo 1", "Nodo 2", "Nodo 3", "Nodo 4", "Nodo 5"]


def get_connection():
    """Abre y devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # permite acceder a las columnas por nombre
    return conn


def crear_tablas():
    """Crea las tablas 'nodos' e 'historial' si todavia no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Activo',
            temperatura REAL NOT NULL DEFAULT 25.0,
            latencia REAL NOT NULL DEFAULT 10.0,
            cpu REAL NOT NULL DEFAULT 20.0,
            memoria REAL NOT NULL DEFAULT 30.0,
            usuarios_conectados INTEGER NOT NULL DEFAULT 0,
            ultima_actualizacion TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nodo_id INTEGER NOT NULL,
            temperatura REAL NOT NULL,
            cpu REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (nodo_id) REFERENCES nodos (id)
        )
    """)

    conn.commit()
    conn.close()
    print("Tablas 'nodos' e 'historial' verificadas/creadas correctamente.")


def poblar_nodos_iniciales():
    """
    Inserta los 5 nodos base solo si la tabla 'nodos' esta vacia.
    Esto evita duplicar nodos cada vez que se reinicia la app.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM nodos")
    total = cursor.fetchone()["total"]

    if total == 0:
        ahora = datetime.now().isoformat(timespec="seconds")
        for nombre in NOMBRES_NODOS:
            cursor.execute("""
                INSERT INTO nodos (nombre, estado, temperatura, latencia, cpu, memoria,
                                    usuarios_conectados, ultima_actualizacion)
                VALUES (?, 'Activo', 25.0, 10.0, 20.0, 30.0, 0, ?)
            """, (nombre, ahora))
        conn.commit()
        print(f"Se insertaron {len(NOMBRES_NODOS)} nodos iniciales.")
    else:
        print(f"La tabla 'nodos' ya tiene {total} registros, no se insertan datos nuevos.")

    conn.close()


def inicializar_base_datos():
    """Funcion de conveniencia: crea tablas y siembra los nodos iniciales."""
    crear_tablas()
    poblar_nodos_iniciales()


if __name__ == "__main__":
    # Permite ejecutar "python database.py" directamente para inicializar todo
    inicializar_base_datos()
    