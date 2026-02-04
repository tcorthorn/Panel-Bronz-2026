import sqlite3

# Ruta a tu base de datos
ruta_db = r'C:\Users\tcort\OneDrive\BRONZ\Django\BRONZ.db'

# Lista de tablas que quieres ELIMINAR completamente
tablas_a_eliminar = [
    'invEP',
    'invVP',
    'invEP_VP',
    #'inventario'
    # Añade más nombres de tablas aquí
]

conn = sqlite3.connect(ruta_db)
cursor = conn.cursor()

# Comprobar las tablas existentes
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tablas_existentes = set(row[0] for row in cursor.fetchall())

for tabla in tablas_a_eliminar:
    if tabla in tablas_existentes:
        cursor.execute(f'DROP TABLE "{tabla}";')
        print(f"[OK] Tabla '{tabla}' eliminada completamente.")
    else:
        print(f"[ADVERTENCIA] La tabla '{tabla}' NO existe y no puede ser eliminada.")

conn.commit()
conn.close()
print("¡Las tablas seleccionadas han sido eliminadas completamente!")