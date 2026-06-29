import sys
from PySide6.QtWidgets import QApplication
from ui.success_popup import SuccessPopup

app = QApplication(sys.argv)
# stats mock
stats = {
    'has_historis_simpanan': False,
    'has_historis_pinjaman': False,
    'baris_simpanan_berjalan': 1000,
    'baris_pinjaman_berjalan': 2000,
    'jumlah_kc': 15,
    'jumlah_periode': 2
}
popup = SuccessPopup(stats=stats, elapsed=1.5)
popup.show()
sys.exit(app.exec())
