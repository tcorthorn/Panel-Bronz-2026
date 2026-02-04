import sqlite3

# Ruta a tu base de datos
ruta_db = r'C:\Users\tcort\OneDrive\BRONZ\Django\BRONZ.db'

conn = sqlite3.connect(ruta_db)
cursor = conn.cursor()

# Obtener todas las tablas (solo las del usuario, no las del sistema)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tablas = [row[0] for row in cursor.fetchall()]

for tabla in tablas:
    cursor.execute(f'DELETE FROM "{tabla}";')
    print(f"[OK] Borrados todos los valores de la tabla: {tabla}")

conn.commit()
conn.close()
print("¡Base de datos vaciada! (Las tablas siguen intactas)")