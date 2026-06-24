import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal, QEasingCurve
from PySide6.QtGui import QPixmap, QColor, QPainter, QLinearGradient

class SplashScreen(QWidget):
    splash_finished = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 380)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Background Widget with dark blue gradient
        self.bg_widget = QWidget(self)
        self.bg_widget.setObjectName("splashBg")
        self.bg_widget.setStyleSheet("""
            QWidget#splashBg {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0F2A4A, stop:0.5 #1A3A5C, stop:1 #0D2240);
                border-radius: 16px;
            }
        """)

        self.bg_layout = QVBoxLayout(self.bg_widget)
        self.bg_layout.setContentsMargins(40, 40, 40, 30)

        # Top spacer
        self.bg_layout.addStretch(2)

        # Logo BRI
        self.logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "bri_logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                140, 140,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("BRI")
            self.logo_label.setStyleSheet("color: white; font-size: 56px; font-weight: bold;")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_layout.addWidget(self.logo_label)
        self.bg_layout.addSpacing(20)

        # App Title
        self.title_label = QLabel("SSA Dashboard")
        self.title_label.setStyleSheet("""
            color: white;
            font-size: 28px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_layout.addWidget(self.title_label)

        # Subtitle
        self.subtitle_label = QLabel("AH Gunsar · Jakarta Region")
        self.subtitle_label.setStyleSheet("color: #7B9CC0; font-size: 13px;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_layout.addWidget(self.subtitle_label)

        self.bg_layout.addStretch(3)

        # Status Label
        self.status_label = QLabel("Mempersiapkan sistem...")
        self.status_label.setStyleSheet("color: #5A8DB5; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_layout.addWidget(self.status_label)
        self.bg_layout.addSpacing(8)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563EB, stop:1 #60A5FA
                );
                border-radius: 2px;
            }
        """)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.bg_layout.addWidget(self.progress_bar)
        self.bg_layout.addSpacing(15)

        # Copyright
        copyright_label = QLabel("© 2026 Bank BRI — Semua Hak Dilindungi")
        copyright_label.setStyleSheet("color: #3D6080; font-size: 10px;")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_layout.addWidget(copyright_label)

        self.layout.addWidget(self.bg_widget)

        # Opacity Effect for Fade Out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

    def start_splash(self):
        self.counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(20)  # 20ms * 100 = 2 seconds

    def update_progress(self):
        self.counter += 1
        self.progress_bar.setValue(self.counter)

        if self.counter == 25:
            self.status_label.setText("Menginisialisasi modul...")
        elif self.counter == 50:
            self.status_label.setText("Memuat antarmuka...")
        elif self.counter == 75:
            self.status_label.setText("Menyiapkan dashboard...")
        elif self.counter == 95:
            self.status_label.setText("Siap")

        if self.counter >= 100:
            self.timer.stop()
            self.fade_out()

    def fade_out(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.finished.connect(self.on_fade_out_finished)
        self.anim.start()

    def on_fade_out_finished(self):
        self.splash_finished.emit()
        self.close()
