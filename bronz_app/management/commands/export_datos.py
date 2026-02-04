from django.core.management.base import BaseCommand
import sqlite3
import pandas as pd
import xlwings as xw
from tkinter import Tk, filedialog

class Command(BaseCommand):
    help = 'Exporta datos desde SQLite a un archivo Excel usando xlwings (con selección gráfica del archivo).'

    def handle(self, *args, **options):
        # ----- Configura tu archivo Excel -----
        excel_path = r'C:\Users\tcort\OneDrive\BRONZ\Django\Otros\GestionBronzX.xlsm'
        sheet_name = 'Datos'

        # 1. Selecciona la base de datos SQLite gráficamente
        Tk().withdraw()
        db_path = filedialog.askopenfilename(
            title="Selecciona tu archivo SQLite",
            filetypes=[("Archivos SQLite", "*.sqlite *.db")]
        )
        if not db_path:
            self.stdout.write(self.style.ERROR("No seleccionaste ningún archivo."))
            return

        # 2. Conéctate a la base SQLite y extrae los datos como DataFrames
        conn = sqlite3.connect(db_path)
        queries = {
            'union_debitos': "SELECT fecha, cta_debito, monto_debito FROM union_debitos;",
            'union_creditos': "SELECT fecha, cta_credito, monto_credito FROM union_creditos;",
            'suma_debitos': "SELECT cuenta_debito, total_debito FROM suma_debitos;",
            'suma_creditos': "SELECT cuenta_credito, total_credito FROM suma_creditos;"
        }

        df_debitos = pd.read_sql_query(queries['union_debitos'], conn)
        df_debitos['monto_debito'] = df_debitos['monto_debito'].round().astype('Int64')

        df_creditos = pd.read_sql_query(queries['union_creditos'], conn)
        df_creditos['monto_credito'] = df_creditos['monto_credito'].round().astype('Int64')

        df_suma_debitos = pd.read_sql_query(queries['suma_debitos'], conn)
        df_suma_debitos['total_debito'] = df_suma_debitos['total_debito'].round().astype('Int64')

        df_suma_creditos = pd.read_sql_query(queries['suma_creditos'], conn)
        df_suma_creditos['total_credito'] = df_suma_creditos['total_credito'].round().astype('Int64')

        # 3. Abre el libro Excel y la hoja con xlwings (manteniendo macros y botones)
        app = xw.App(visible=False)
        wb = xw.Book(excel_path)
        ws = wb.sheets[sheet_name]

        # 4. Limpia los datos anteriores (dejando los encabezados)
        for col in ['A', 'B', 'C', 'E', 'F', 'G', 'J', 'K', 'L', 'M']:
            ws.range(f'{col}2:{col}1048576').clear_contents()  # hasta el final de la hoja

        # 5. Escribe encabezados (opcional)
        """
        ws['A1'].value = 'Fecha'
        ws['B1'].value = 'Cuenta Débito'
        ws['C1'].value = 'Débito'
        ws['E1'].value = 'Fecha'
        ws['F1'].value = 'Cuenta Crédito'
        ws['G1'].value = 'Crédito'
        ws['J1'].value = 'Cuenta Débito'
        ws['K1'].value = 'Total Débito'
        ws['L1'].value = 'Cuenta Crédito'
        ws['M1'].value = 'Total Crédito'
        """

        # 6. Pega los datos (comenzando en la fila 2)
        if not df_debitos.empty:
            ws.range('A2').options(index=False, header=False).value = df_debitos
        if not df_creditos.empty:
            ws.range('E2').options(index=False, header=False).value = df_creditos
        if not df_suma_debitos.empty:
            ws.range('J2').options(index=False, header=False).value = df_suma_debitos
        if not df_suma_creditos.empty:
            ws.range('L2').options(index=False, header=False).value = df_suma_creditos
        """
        # 7. Da formato de número entero a las columnas de montos
        for col in ['C', 'G', 'K', 'M']:
            ws.range(f'{col}2:{col}1048576').number_format = '0'
        """
        wb.save()
        wb.close()
        app.quit()
        self.stdout.write(self.style.SUCCESS("Datos exportados correctamente y las macros/botones se mantienen intactos."))