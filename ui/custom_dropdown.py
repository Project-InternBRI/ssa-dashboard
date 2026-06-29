from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit,
    QScrollArea, QRadioButton, QButtonGroup, QLabel, QApplication, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor, QColor

class DropdownPopup(QWidget):
    item_selected = Signal(str)
    
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.items = items
        self.radio_buttons = []
        self.current_selection = items[0] if items else ""
        
        self.init_ui()
        
    def init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(10, 10, 10, 10)
        
        # Container to hold shadow
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
        
        # Scroll Area for Radio Buttons
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.list_lay = QVBoxLayout(self.scroll_content)
        self.list_lay.setContentsMargins(0, 0, 0, 0)
        self.list_lay.setSpacing(4)
        
        self.btn_group = QButtonGroup(self)
        
        for i, text in enumerate(self.items):
            rb = QRadioButton(text)
            rb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            rb.setStyleSheet("""
                QRadioButton {
                    padding: 8px;
                    border-radius: 4px;
                    color: #475569;
                    font-size: 13px;
                }
                QRadioButton:hover {
                    background: #F8FAFC;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid #CBD5E1;
                    background: #FFFFFF;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #3B82F6;
                    background: #3B82F6;
                    image: url(none); /* We use a pseudo-element for the inner circle if possible, but basic Qt radio is fine */
                }
                QRadioButton:checked {
                    background: #F1F5F9;
                    color: #1E293B;
                    font-weight: 500;
                }
            """)
            if i == 0:
                rb.setChecked(True)
            self.list_lay.addWidget(rb)
            self.radio_buttons.append(rb)
            self.btn_group.addButton(rb, i)
            
        self.list_lay.addStretch()
        self.scroll.setWidget(self.scroll_content)
        
        # Fixed height for scroll area to show ~5 items
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
        
    def filter_items(self, text):
        search_term = text.lower()
        for rb in self.radio_buttons:
            if search_term in rb.text().lower():
                rb.show()
            else:
                rb.hide()
                
    def submit(self):
        checked_btn = self.btn_group.checkedButton()
        if checked_btn:
            self.current_selection = checked_btn.text()
            self.item_selected.emit(self.current_selection)
        self.close()
        
    def set_selected(self, text):
        for rb in self.radio_buttons:
            if rb.text() == text:
                rb.setChecked(True)
                break

    def update_items(self, new_items):
        self.items = new_items
        
        # Remove old radio buttons
        for rb in self.radio_buttons:
            self.list_lay.removeWidget(rb)
            self.btn_group.removeButton(rb)
            rb.deleteLater()
            
        self.radio_buttons.clear()
        
        # Add new radio buttons
        for i, text in enumerate(self.items):
            rb = QRadioButton(text)
            rb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            rb.setStyleSheet("""
                QRadioButton {
                    padding: 8px;
                    border-radius: 4px;
                    color: #475569;
                    font-size: 13px;
                }
                QRadioButton:hover {
                    background: #F8FAFC;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid #CBD5E1;
                    background: #FFFFFF;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #3B82F6;
                    background: #3B82F6;
                    image: url(none);
                }
                QRadioButton:checked {
                    background: #F1F5F9;
                    color: #1E293B;
                    font-weight: 500;
                }
            """)
            if i == 0:
                rb.setChecked(True)
            self.list_lay.insertWidget(i, rb)
            self.radio_buttons.append(rb)
            self.btn_group.addButton(rb, i)
        
        self.current_selection = self.items[0] if self.items else ""

class CustomDropdown(QPushButton):
    currentTextChanged = Signal(str)
    
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items
        self.current_text = items[0] if items else "Select Option"
        
        self.setText(f"{self.current_text}   ▾")
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
        
        self.popup = DropdownPopup(items)
        self.popup.item_selected.connect(self._on_item_selected)
        
        self.clicked.connect(self.show_popup)
        
    def show_popup(self):
        self.popup.set_selected(self.current_text)
        self.popup.search_bar.setText("")
        
        # Position popup below the button
        pos = self.mapToGlobal(QPoint(0, self.height()))
        
        # Adjust for the popup's layout margins so it aligns nicely
        self.popup.move(pos.x() - 10, pos.y() - 5)
        self.popup.show()
        
    def clear(self):
        self.items = []
        self.popup.update_items(self.items)
        self.current_text = "Select Option"
        self.setText(f"{self.current_text}   ▾")

    def addItem(self, item):
        self.items.append(item)
        self.popup.update_items(self.items)
        if len(self.items) == 1:
            self.current_text = item
            self.setText(f"{self.current_text}   ▾")
            
    def addItems(self, items):
        self.items.extend(items)
        self.popup.update_items(self.items)
        if self.current_text == "Select Option" and self.items:
            self.current_text = self.items[0]
            self.setText(f"{self.current_text}   ▾")
        
    def _on_item_selected(self, text):
        self.current_text = text
        self.setText(f"{text}   ▾")
        self.currentTextChanged.emit(text)
        
    def addItems(self, items):
        # Full rebuild of the popup isn't strictly necessary if we don't dynamically update,
        # but if we do, we need to rebuild the radio buttons.
        self.items = items
        self.popup.deleteLater()
        self.popup = DropdownPopup(items)
        self.popup.item_selected.connect(self._on_item_selected)
        if items:
            self.setCurrentText(items[0])
            
    def currentText(self):
        return self.current_text
        
    def setCurrentText(self, text):
        if text in self.items:
            self._on_item_selected(text)
            
    def clear(self):
        self.addItems([])
