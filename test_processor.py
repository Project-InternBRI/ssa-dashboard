import traceback
from core.processor_uker import process_uker_from_df
import pandas as pd

try:
    df_s_all = pd.DataFrame({
        "Nama Uker": ["KCP A", "UNIT B", ""],
        "Jenis Produk": ["Tabungan", "Giro", "Deposito"],
        "Segmentasi BPR": ["Ritel", "Wholesale", "Ritel"],
        "Saldo": ["1000", "2000", "3000"],
        "Month, Day, Year of Posisi": ["10/24", "10/24", "10/24"],
        "Nama Cabang": ["KC A", "KC A", "KC A"]
    })
    
    df_p_all = pd.DataFrame({
        "Nama Cabang": ["KC A", "KC A", "KC A"],
        "Nama Uker": ["KCP A", "UNIT B", ""],
        "Month, Day, Year of Periode": ["10/24", "10/24", "10/24"],
        "Baki Debet": ["1000", "2000", "3000"],
        "Kolektabilitas One Obligor": ["1", "2", "3"],
        "Produk": ["Kupedes", "KUR", "Briguna"],
        "SEGMEN_2025": ["Mikro", "Mikro", "Konsumer"]
    })

    res = process_uker_from_df(df_s_all, df_p_all)
    print("SUCCESS")
except Exception as e:
    traceback.print_exc()
