import os
import urllib.request
from PySide6.QtGui import QImage, QPainter, QColor, QPainterPath
from PySide6.QtCore import Qt, QRectF
from PySide6.QtSvg import QSvgRenderer

def create_kpi_icon(svg_url, output_path, bg_color_hex, icon_scale=0.55):
    # Download SVG
    req = urllib.request.Request(svg_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        svg_data = response.read()
    
    # We want to make the SVG white. 
    # Instead of parsing XML, PySide6 QSvgRenderer just renders it.
    # FontAwesome SVGs default to black fill. We can render it and then tint it.
    
    renderer = QSvgRenderer(svg_data)
    
    # Create the final image (e.g. 128x128)
    size = 128
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw smooth circle
    bg_color = QColor(bg_color_hex)
    painter.setBrush(bg_color)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    
    # Draw the SVG in the center
    # First, render the SVG into a separate transparent image so we can tint it white
    icon_size = int(size * icon_scale)
    icon_img = QImage(icon_size, icon_size, QImage.Format_ARGB32)
    icon_img.fill(Qt.transparent)
    
    icon_painter = QPainter(icon_img)
    icon_painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(icon_painter)
    icon_painter.end()
    
    # Tint icon_img white
    for y in range(icon_img.height()):
        for x in range(icon_img.width()):
            pixel = icon_img.pixelColor(x, y)
            if pixel.alpha() > 0:
                icon_img.setPixelColor(x, y, QColor(255, 255, 255, pixel.alpha()))
                
    # Paste the tinted icon onto the circle
    x_offset = (size - icon_size) // 2
    y_offset = (size - icon_size) // 2
    painter.drawImage(x_offset, y_offset, icon_img)
    
    painter.end()
    
    # Save the final image
    img.save(output_path, "PNG")
    print(f"Created {output_path}")

icons = [
    ("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/users.svg", "assets/icons/kpi_dpk.png", "#002060"),
    ("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/sack-dollar.svg", "assets/icons/kpi_tab.png", "#002060"),
    ("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/landmark.svg", "assets/icons/kpi_gir.png", "#FF6600"),
    ("https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/database.svg", "assets/icons/kpi_dep.png", "#008000")
]

for url, out, color in icons:
    create_kpi_icon(url, out, color)

