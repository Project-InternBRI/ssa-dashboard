import sqlite3
from core.db_manager import init_db, DB_PATH
from core.processor import process_files
from core.exporter import export_to_excel
import openpyxl

init_db()
result = process_files(
    ['data_dummy/Simpanan/Data_Simpanan_Dump.csv'],
    ['data_dummy/Pinjaman/Data_Pinjaman_Dump.csv'],
)

export_to_excel(result, 'test_export_fix.xlsx')

wb = openpyxl.load_workbook("test_export_fix.xlsx", data_only=False)
ws = wb['Tanah Abang']
for row in range(1, 20):
    c = ws.cell(row=row, column=2)
    if c.value == "Pinjaman":
        print("Success!")
        break
