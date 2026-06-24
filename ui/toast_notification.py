"""
toast_notification.py — Sistem toast notification di pojok kanan bawah.
Mendukung tipe: success, error, info, warning.
Stack otomatis jika ada beberapa toast sekaligus.
"""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                               QPushButton, QGraphicsOpacityEffect,
                               QApplication)
from PySide6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve,
                            QPoint, QRect)
from PySide6.QtGui import QCursor


_STYLES = {
    "success": {
        "bg": "#ECFDF5", "border": "#6EE7B7",
        "icon": "✓",    "icon_bg": "#059669",
        "text": "#065F46",
    },
    "error": {
        "bg": "#FEF2F2", "border": "#FCA5A5",
        "icon": "✕",    "icon_bg": "#DC2626",
        "text": "#991B1B",
    },
    "info": {
        "bg": "#EFF6FF", "border": "#93C5FD",
        "icon": "i",    "icon_bg": "#2563EB",
        "text": "#1E40AF",
    },
    "warning": {
        "bg": "#FFFBEB", "border": "#FCD34D",
        "icon": "!",    "icon_bg": "#D97706",
        "text": "#92400E",
    },
}


class ToastNotification(QWidget):
    """Satu toast notification dengan animasi slide-up dan fade-out."""

    def __init__(self, message: str, toast_type: str = "info",
                 duration_ms: int = 4000, parent: QWidget | None = None):
        super().__init__(parent,
                         Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint |
                         Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedWidth(400)

        style = _STYLES.get(toast_type, _STYLES["info"])
        self._build(message, style)
        self.adjustSize()

        if duration_ms > 0:
            QTimer.singleShot(duration_ms, self.dismiss)

    # ── UI ─────────────────────────────────────────────────────

    def _build(self, message: str, s: dict) -> None:
        """Bangun tampilan toast."""
        box = QWidget(self)
        box.setStyleSheet(f"""
            QWidget {{
                background-color: {s['bg']};
                border: 1px solid {s['border']};
                border-radius: 10px;
            }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 6)   # 6px shadow space di bawah
        root.addWidget(box)

        lay = QHBoxLayout(box)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(12)

        # Icon
        ic = QLabel(s["icon"])
        ic.setFixedSize(28, 28)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(f"""
            QLabel {{
                background-color: {s['icon_bg']};
                color: white;
                border-radius: 14px;
                font-size: 13px;
                font-weight: bold;
                border: none;
            }}
        """)

        # Message
        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"""
            QLabel {{
                color: {s['text']};
                font-size: 13px;
                background: transparent;
                border: none;
            }}
        """)

        # Close button
        close = QPushButton("✕")
        close.setFixedSize(22, 22)
        close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {s['text']};
                font-size: 11px;
                border: none;
                border-radius: 11px;
            }}
            QPushButton:hover {{ background: rgba(0,0,0,0.08); }}
        """)
        close.clicked.connect(self.dismiss)

        lay.addWidget(ic)
        lay.addWidget(msg, 1)
        lay.addWidget(close)

    # ── Show / Dismiss ─────────────────────────────────────────

    def show_animated(self) -> None:
        """Tampilkan toast dengan animasi slide-up dari bawah."""
        self.show()
        self.raise_()

        start = self.pos() + QPoint(0, 20)
        end   = self.pos()
        self._anim_pos = QPropertyAnimation(self, b"pos")
        self._anim_pos.setDuration(300)
        self._anim_pos.setStartValue(start)
        self._anim_pos.setEndValue(end)
        self._anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_pos.start()

    def dismiss(self) -> None:
        """Sembunyikan toast dengan animasi fade-out."""
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        self._anim_fade = QPropertyAnimation(eff, b"opacity")
        self._anim_fade.setDuration(200)
        self._anim_fade.setStartValue(1.0)
        self._anim_fade.setEndValue(0.0)
        self._anim_fade.setEasingCurve(QEasingCurve.Type.InQuad)
        self._anim_fade.finished.connect(self.close)
        self._anim_fade.start()


class ToastManager:
    """
    Kelola stack toast di pojok kanan bawah parent window.

    Usage:
        ToastManager.show(parent_widget, "Berhasil!", "success")
    """
    _active: list[ToastNotification] = []

    @classmethod
    def show(cls, parent: QWidget, message: str,
             toast_type: str = "info", duration_ms: int = 4000) -> None:
        """Tampilkan toast baru. Stack ke atas jika ada yang aktif."""
        # Bersihkan referensi yang sudah ditutup
        cls._active = [t for t in cls._active if t.isVisible()]

        toast = ToastNotification(message, toast_type, duration_ms)

        # Posisi dasar: pojok kanan bawah parent (atau layar)
        if parent and parent.isVisible():
            geo = parent.geometry()
            base_x = geo.right()  - toast.width() - 24
            base_y = geo.bottom() - toast.height() - 24
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            base_x = screen.right()  - toast.width() - 24
            base_y = screen.bottom() - toast.height() - 24

        # Stack ke atas setiap toast yang masih aktif
        offset_y = 0
        for t in cls._active:
            offset_y += t.height() + 8

        toast.move(base_x, base_y - offset_y)
        toast.show_animated()
        cls._active.append(toast)
