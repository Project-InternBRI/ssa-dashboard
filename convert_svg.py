import sys
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

def convert_svg_to_png(svg_path, png_path, size=128):
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        print(f"Invalid SVG: {svg_path}")
        return False
    
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(0x00ffffff) # Transparent
    
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    
    return image.save(png_path, "PNG")

files = [
    ("/Users/naufalrasydan/Downloads/total_dpk.svg", "assets/icons/kpi_dpk.png"),
    ("/Users/naufalrasydan/Downloads/tabungan.svg", "assets/icons/kpi_tab.png"),
    ("/Users/naufalrasydan/Downloads/giro.svg", "assets/icons/kpi_gir.png"),
    ("/Users/naufalrasydan/Downloads/deposito.svg", "assets/icons/kpi_dep.png")
]

for src, dst in files:
    if convert_svg_to_png(src, dst):
        print(f"Converted {src} to {dst}")
    else:
        print(f"Failed to convert {src}")
