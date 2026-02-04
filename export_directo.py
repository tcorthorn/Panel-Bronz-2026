import pandas as pd
import pyodbc
import sqlite3

# === CONFIGURACIÓN ===
ACCESS_PATH = r'C:\Users\tcort\OneDrive\BRONZ\BRONZ 2025V2.accdb'
SQLITE_PATH = r'C:\Users\tcort\OneDrive\BRONZ\Django\BRONZX.db'

# Mapeo Access -> SQLite
TABLAS = {
    "Catalogo de productos": "Catalogo",
    "Asientos contables": "asientos_contables",
    "Cuentas ajuste inicial": "balance_inicial",
    "Entrada de productos": "entrada_productos",
    "Ingreso_Bodegas_Tiendas": "envíos",
    "Inventario Inicial Total": "inventario_inicial",
    "Otros gastos": "otros_gastos",
    "Sueldos y honorarios": "sueldos",
    "Ventas": "ventas",
}

# Conexión Access
conn_access = pyodbc.connect(
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;' % ACCESS_PATH
)

# Conexión SQLite
conn_sqlite = sqlite3.connect(SQLITE_PATH)

for access_name, sqlite_name in TABLAS.items():
    print(f'Exportando: {access_name}  ➔  {sqlite_name}')
    # Si la tabla tiene dos destinos (como "Consulta Cuenta Crédito diaria"), puedes filtrar aquí según columna si lo necesitas
    df = pd.read_sql(f"SELECT * FROM [{access_name}]", conn_access)

    df.to_sql(sqlite_name, conn_sqlite, if_exists='replace', index=False)

# (Aquí) Imprime los nombres de las columnas para detectar duplicados
    print(f"Columnas en {access_name}: {list(df.columns)}")
    
    # (Aquí) Soluciona columnas duplicadas (las elimina)
    if df.columns.duplicated().any():
        print(f"Corrigiendo columnas duplicadas en {access_name}…")
        df = df.loc[:, ~df.columns.duplicated()]

conn_access.close()
conn_sqlite.close()
print('¡Exportación completa! Ahora puedes definir relaciones en DB Browser for SQLite.')