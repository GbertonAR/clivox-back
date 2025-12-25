## dump_estructura.py# -*- coding: utf-8 -*-
# Script para volcar la estructura de una base de datos SQLite a un archivo de texto

import os
import sqlite3

DB_PATH = "clivox.db"
OUTPUT_FILE = "estructura_db.txt"

def dump_estructura(db_path, output_file):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("📋 ESTRUCTURA DE LA BASE DE DATOS\n\n")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tablas = cursor.fetchall()

        for tabla in tablas:
            nombre_tabla = tabla[0]
            f.write(f"🧱 Tabla: {nombre_tabla}\n")
            cursor.execute(f"PRAGMA table_info({nombre_tabla});")
            columnas = cursor.fetchall()
            for col in columnas:
                cid, name, tipo, notnull, default_value, pk = col
                pk_str = " [PK]" if pk else ""
                f.write(f"   - {name} ({tipo}){pk_str}\n")
            f.write("\n")

    conn.close()
    print(f"Estructura guardada en: {output_file}")

if __name__ == "__main__":
    dump_estructura(DB_PATH, OUTPUT_FILE)
