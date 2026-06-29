"""
confirm_popup.py — Popup konfirmasi custom (Hapus, Keluar, dsb).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCursor, QColor

class ConfirmPopup(QDialog):
    def __init__(self, parent=None, title: str = "", text: str = "",
                 action_text: str = "Ya", action_color: str = "#DC2626"):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self.setStyleSheet("QDialog { background: transparent; border: 0px solid transparent; outline: none; }")
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)
        
        self._card = QFrame(self)
        self._card.setObjectName("popupCard")
        self._card.setMinimumWidth(380)
        self._card.setStyleSheet("""
            QFrame#popupCard {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)

        main_lay.addWidget(self._card)

        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(15, 23, 42, 50))
        shadow.setOffset(0, 8)
        self._card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self._card)
        lay.setContentsMargins(32, 32, 32, 28)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Ikon Peringatan ─────────────────────────────────────────
        icon_frame = QFrame()
        icon_frame.setFixedSize(56, 56)
        bg_rgba = QColor(action_color)
        bg_rgba.setAlpha(20)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_rgba.name(QColor.NameFormat.HexArgb)};
                border-radius: 28px;
            }}
        """)
        ic_lbl = QLabel("!", icon_frame)
        ic_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic_lbl.setGeometry(0, 0, 56, 56)
        ic_lbl.setStyleSheet(
            f"font-size:26px; font-weight: bold; color:{action_color}; background:transparent;")

        # ── Judul ────────────────────────────────────────────────
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(
            "font-size:18px; font-weight:700; color:#0F172A; background: transparent;")

        # ── Sub-teks ─────────────────────────────────────────────
        lbl_sub = QLabel(text)
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("font-size:13px; color:#64748B; background: transparent;")

        # ── Tombol ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 8, 0, 0)
        btn_row.setSpacing(12)

        btn_cancel = QPushButton("Batal")
        btn_cancel.setFixedHeight(42)
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                color: #475569;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #F1F5F9; color: #1E293B; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_action = QPushButton(action_text)
        btn_action.setFixedHeight(42)
        btn_action.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {action_color};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {self._darken_color(action_color)}; }}
        """)
        btn_action.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_action)

        # Susun layout
        lay.addWidget(icon_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_sub)
        lay.addLayout(btn_row)

        self._anim_show()
        
    def _darken_color(self, hex_color: str) -> str:
        c = QColor(hex_color)
        return c.darker(115).name()

    def _anim_show(self):
        self.setWindowOpacity(0.0)
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(200)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def showEvent(self, event):
        self.adjustSize()
        pw = self.parentWidget()
        if pw:
            top_level = pw.window()
            pg = top_level.geometry()
            x = pg.x() + (pg.width() - self.width()) // 2
            y = pg.y() + (pg.height() - self.height()) // 2
            self.move(x, y)
        super().showEvent(event)

    @classmethod
    def ask(cls, parent, title: str, text: str, action_text: str = "Ya", action_color: str = "#DC2626") -> bool:
        dlg = cls(parent, title, text, action_text, action_color)
        return dlg.exec() == QDialog.DialogCode.Accepted
