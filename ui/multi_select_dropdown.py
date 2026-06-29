from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit,
    QScrollArea, QCheckBox, QLabel, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor, QColor

class MultiDropdownPopup(QWidget):
    items_selected = Signal(list)
    
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.items = items
        self.checkboxes = []
        
        self.init_ui()
        
    def init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(10, 10, 10, 10)
        
        self.container = QFrame(self)
        self.container.setStyleSheet("QFrame#container { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; }")
        self.container.setObjectName("container")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        self.container.setGraphicsEffect(shadow)
        
        lay = QVBoxLayout(self.container)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setFixedHeight(36)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #3B82F6;
                border-radius: 4px;
                padding: 0 12px;
                background: #FFFFFF;
                color: #334155;
            }
        """)
        self.search_bar.textChanged.connect(self.filter_items)
        lay.addWidget(self.search_bar)
        
        # Scroll Area for CheckBoxes
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.list_lay = QVBoxLayout(self.scroll_content)
        self.list_lay.setContentsMargins(0, 0, 0, 0)
        self.list_lay.setSpacing(4)
        
        # Add "Semua" checkbox
        self.cb_semua = QCheckBox("Semua")
        self.cb_semua.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._style_checkbox(self.cb_semua)
        self.cb_semua.stateChanged.connect(self._on_semua_changed)
        self.list_lay.addWidget(self.cb_semua)
        
        for text in self.items:
            cb = QCheckBox(text)
            cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._style_checkbox(cb)
            cb.stateChanged.connect(self._on_item_changed)
            self.list_lay.addWidget(cb)
            self.checkboxes.append(cb)
            
        self.list_lay.addStretch()
        self.scroll.setWidget(self.scroll_content)
        
        self.scroll.setMinimumHeight(150)
        self.scroll.setMaximumHeight(200)
        
        lay.addWidget(self.scroll)
        
        # Assign Button
        self.btn_assign = QPushButton("APPLY")
        self.btn_assign.setFixedHeight(40)
        self.btn_assign.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_assign.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1D4ED8;
            }
        """)
        self.btn_assign.clicked.connect(self.submit)
        lay.addWidget(self.btn_assign)
        
        main_lay.addWidget(self.container)
        self.setFixedWidth(260)
        
    def _style_checkbox(self, cb):
        cb.setStyleSheet("""
            QCheckBox {
                padding: 8px;
                border-radius: 4px;
                color: #475569;
                font-size: 13px;
            }
            QCheckBox:hover {
                background: #F8FAFC;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 2px solid #CBD5E1;
                background: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #3B82F6;
                background: #3B82F6;
            }
        """)
        
    def filter_items(self, text):
        search_term = text.lower()
        for cb in self.checkboxes:
            if search_term in cb.text().lower():
                cb.show()
            else:
                cb.hide()
                
    def _on_semua_changed(self, state):
        self.cb_semua.blockSignals(True)
        for cb in self.checkboxes:
            cb.blockSignals(True)
            cb.setChecked(state == Qt.CheckState.Checked.value)
            cb.blockSignals(False)
        self.cb_semua.blockSignals(False)
        
    def _on_item_changed(self, state):
        self.cb_semua.blockSignals(True)
        all_checked = all([cb.isChecked() for cb in self.checkboxes])
        self.cb_semua.setChecked(all_checked)
        self.cb_semua.blockSignals(False)

    def submit(self):
        current_selections = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        if self.cb_semua.isChecked() or len(current_selections) == len(self.checkboxes):
            current_selections = ["Semua"]
            
        self.items_selected.emit(current_selections)
        self.close()
        
    def set_selected(self, selections):
        if "Semua" in selections:
            self.cb_semua.setChecked(True)
        else:
            self.cb_semua.setChecked(False)
            for cb in self.checkboxes:
                cb.setChecked(cb.text() in selections)

class MultiSelectDropdown(QPushButton):
    itemsChanged = Signal(list)
    
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items
        self.current_selections = ["Semua"]
        
        self.setText("Semua   ▾")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 12px;
                color: #334155;
                font-size: 13px;
                text-align: left;
            }
            QPushButton:hover {
                border: 1px solid #94A3B8;
            }
        """)
        
        self.popup = MultiDropdownPopup(items)
        self.popup.items_selected.connect(self._on_items_selected)
        
        self.clicked.connect(self.show_popup)
        
    def show_popup(self):
        self.popup.set_selected(self.current_selections)
        self.popup.search_bar.setText("")
        
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self.popup.move(pos.x() - 10, pos.y() - 5)
        self.popup.show()
        
    def _on_items_selected(self, selections):
        if not selections:
            selections = ["Semua"]
            
        self.current_selections = selections
        
        if "Semua" in selections:
            self.setText("Semua   ▾")
        elif len(selections) == 1:
            self.setText(f"{selections[0]}   ▾")
        else:
            self.setText(f"{len(selections)} Terpilih   ▾")
            
        self.itemsChanged.emit(selections)
        
    def addItems(self, items):
        self.items = items
        self.popup.deleteLater()
        self.popup = MultiDropdownPopup(items)
        self.popup.items_selected.connect(self._on_items_selected)
        if items:
            self.setCurrentSelections(["Semua"])
            
    def currentSelections(self):
        return self.current_selections
        
    def setCurrentSelections(self, selections):
        self._on_items_selected(selections)
        
    def clear(self):
        self.addItems([])
