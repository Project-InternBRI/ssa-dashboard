import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'ssa_local.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Create RKA table v2
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rka_data_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kc TEXT,
            tahun INTEGER,
            bulan TEXT,
            
            dpk_tabungan INTEGER DEFAULT 0,
            dpk_giro INTEGER DEFAULT 0,
            dpk_deposito INTEGER DEFAULT 0,
            dpk_casa INTEGER DEFAULT 0,
            
            korp_giro INTEGER DEFAULT 0,
            korp_deposito INTEGER DEFAULT 0,
            
            pinj_mikro INTEGER DEFAULT 0,
            pinj_small INTEGER DEFAULT 0,
            pinj_konsumer INTEGER DEFAULT 0,
            
            sml_mikro INTEGER DEFAULT 0,
            sml_mikro_pct TEXT DEFAULT '0,00',
            sml_small INTEGER DEFAULT 0,
            sml_small_pct TEXT DEFAULT '0,00',
            sml_konsumer INTEGER DEFAULT 0,
            sml_konsumer_pct TEXT DEFAULT '0,00',
            
            npl_mikro INTEGER DEFAULT 0,
            npl_mikro_pct TEXT DEFAULT '0,00',
            npl_small INTEGER DEFAULT 0,
            npl_small_pct TEXT DEFAULT '0,00',
            npl_konsumer INTEGER DEFAULT 0,
            npl_konsumer_pct TEXT DEFAULT '0,00',
            
            rec_mikro INTEGER DEFAULT 0,
            rec_small INTEGER DEFAULT 0,
            rec_konsumer INTEGER DEFAULT 0,
            
            UNIQUE(kc, tahun, bulan)
        )
    ''')
    conn.commit()
    conn.close()

def load_rka_record(kc: str, tahun: int, bulan: str) -> dict:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM rka_data_v2 
        WHERE kc = ? AND tahun = ? AND bulan = ?
    ''', (kc, tahun, bulan))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def save_rka_record(data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    cols = list(data.keys())
    vals = [data[c] for c in cols]
    
    placeholders = ", ".join(["?"] * len(cols))
    col_names = ", ".join(cols)
    updates = ", ".join([f"{c}=excluded.{c}" for c in cols if c not in ('kc', 'tahun', 'bulan')])
    
    query = f'''
        INSERT INTO rka_data_v2 ({col_names})
        VALUES ({placeholders})
        ON CONFLICT(kc, tahun, bulan) DO UPDATE SET
            {updates}
    '''
    cursor.execute(query, vals)
    conn.commit()
    conn.close()

# Initialize the database on import
init_db()
