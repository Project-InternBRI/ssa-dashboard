from PIL import Image, ImageDraw, ImageFont
import urllib.request
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import Qt
from PySide6.QtSvg import QSvgRenderer
import tempfile

def generate_header(bg_path, logo_path, title, subtitle, out_path):
    # Banner size
    W, H = 1600, 90
    
    # 1. Base Image
    if bg_path:
        try:
            bg = Image.open(bg_path).convert("RGBA")
            bg = bg.resize((W, H), Image.Resampling.LANCZOS)
        except:
            bg = Image.new("RGBA", (W, H), "#002060")
    else:
        bg = Image.new("RGBA", (W, H), "#002060")
        
    # 2. Draw Logo
    # Instead of reading the blue bri_logo.png which looks bad, let's just use the blue one for now
    # BUT wait, the user's background is dark blue! A blue logo on a blue background is invisible!
    # They said "jika belum saya dapat mendownloadkannya". I will just use the logo they have, 
    # but I'll make the dark blue pixels white!
    try:
        logo = Image.open(logo_path).convert("RGBA")
        # Tint logo white
        data = logo.getdata()
        new_data = []
        for item in data:
            # If pixel is not transparent, make it white
            if item[3] > 0:
                new_data.append((255, 255, 255, item[3]))
            else:
                new_data.append(item)
        logo.putdata(new_data)
        
        # Resize logo to fit height
        lh = 50
        lw = int(logo.width * (lh / logo.height))
        logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        
        bg.paste(logo, (30, (H - lh)//2), logo)
        text_x = 30 + lw + 30
        
        # Draw a vertical separator line
        draw = ImageDraw.Draw(bg)
        draw.line([(text_x - 15, 20), (text_x - 15, H - 20)], fill="white", width=2)
        
    except Exception as e:
        text_x = 30

    # 3. Draw Text
    draw = ImageDraw.Draw(bg)
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    draw.text((text_x, 20), title, font=font_title, fill="white")
    draw.text((text_x, 55), subtitle, font=font_sub, fill="white")
    
    bg.save(out_path)

if __name__ == "__main__":
    generate_header(
        "assets/background_header_excel_dashboard.png",
        "assets/icons/bri_logo.png",
        "DASHBOARD TABUNGAN, GIRO & DEPOSITO",
        "Data per 28 Juni 2026 10:19 WIB",
        "test_header.png"
    )
