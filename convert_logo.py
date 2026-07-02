import sys
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt

def convert_svg_to_png(svg_path, png_path):
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        print(f"Invalid SVG: {svg_path}")
        return False
    
    size = renderer.defaultSize()
    # scale up if it's too small
    if size.width() < 500:
        size.setWidth(size.width() * 4)
        size.setHeight(size.height() * 4)

    image = QImage(size.width(), size.height(), QImage.Format_ARGB32)
    image.fill(0x00ffffff) # Transparent
    
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    
    return image.save(png_path, "PNG")

if convert_svg_to_png("/Users/naufalrasydan/Downloads/BANK_BRI_logo_with_slogan.svg", "assets/icons/bri_excel_logo.png"):
    print("Logo converted successfully!")
else:
    print("Failed to convert logo!")
