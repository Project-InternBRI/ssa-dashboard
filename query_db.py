import sqlite3
import pandas as pd

conn = sqlite3.connect('ssa_local.db')
query = """
SELECT _jenis, _segmentasi, segmen_dashboard, _kolekt, SUM(_baki_debet) / 1000000.0 as baki_juta
FROM pinjaman
WHERE _wilayah = 'Tanah Abang' 
  AND _tanggal = '2025-12-31'
  AND _kolekt != 0
GROUP BY _jenis, _segmentasi, segmen_dashboard, _kolekt
ORDER BY baki_juta DESC
"""
df = pd.read_sql_query(query, conn)
print("--- RAW DB SUMMARIES (Des-25, Tanah Abang) ---")
print(df.to_string())

query2 = """
SELECT segmen_dashboard, SUM(_baki_debet) / 1000000.0 as baki_juta
FROM pinjaman
WHERE _wilayah = 'Tanah Abang' 
  AND _tanggal = '2025-12-31'
  AND _kolekt != 0
GROUP BY segmen_dashboard
"""
df2 = pd.read_sql_query(query2, conn)
print("\n--- CURRENT DASHBOARD TOTALS ---")
print(df2.to_string())

query3 = """
SELECT _jenis, SUM(_baki_debet) / 1000000.0 as baki_juta
FROM pinjaman
WHERE _wilayah = 'Tanah Abang' 
  AND _tanggal = '2025-12-31'
  AND _kolekt != 0
GROUP BY _jenis
ORDER BY baki_juta DESC
"""
df3 = pd.read_sql_query(query3, conn)
print("\n--- BAKI DEBET BY _jenis (Produk) ---")
print(df3.to_string())

query4 = """
SELECT _segmentasi, SUM(_baki_debet) / 1000000.0 as baki_juta
FROM pinjaman
WHERE _wilayah = 'Tanah Abang' 
  AND _tanggal = '2025-12-31'
  AND _kolekt != 0
GROUP BY _segmentasi
ORDER BY baki_juta DESC
"""
df4 = pd.read_sql_query(query4, conn)
print("\n--- BAKI DEBET BY _segmentasi (SEGMEN_2025) ---")
print(df4.to_string())

conn.close()
