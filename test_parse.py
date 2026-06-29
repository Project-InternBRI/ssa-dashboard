import pandas as pd
from core.processor import parse_baki_debet

tests = ['Rp 1.000.000', '1,234,567.89', '242592783', '-1234', 'Rp. 50.000', 'nan', '', '0']
for t in tests:
    print(f"{t:20s} -> {parse_baki_debet(t)}")
