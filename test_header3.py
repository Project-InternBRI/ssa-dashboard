from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1900, 160
bg_path = 'assets/background_header_excel_dashboard.png'

# 1. Base Canvas
base_color = (2, 55, 142, 255)
canvas = Image.new("RGBA", (W, H), base_color)

# 2. Right-side Background
if os.path.exists(bg_path):
    orig_bg = Image.open(bg_path).convert("RGBA")
    
    piece_w = 1000
    piece_h = int(orig_bg.height * (piece_w / orig_bg.width))
    piece = orig_bg.resize((piece_w, piece_h), Image.Resampling.LANCZOS)
    
    y_offset = (piece_h - H) // 2
    piece = piece.crop((0, y_offset, piece_w, y_offset + H))
    
    mask = Image.new("L", (piece_w, H), 255)
    fade_width = 500
    for x in range(fade_width):
        alpha = int(255 * (x / fade_width))
        for y in range(H):
            mask.putpixel((x, y), alpha)
            
    piece.putalpha(mask)
    canvas.paste(piece, (W - piece_w, 0), piece)

# 3. Logo
logo_path = 'assets/icons/bri_logo.png'
if os.path.exists(logo_path):
    orig_logo = Image.open(logo_path).convert("RGBA")
    alpha = orig_logo.split()[3]
    white_logo = Image.new("RGBA", orig_logo.size, (255, 255, 255, 255))
    white_logo.putalpha(alpha)
    logo = white_logo
    
    lh = 80
    lw = int(logo.width * (lh / logo.height))
    logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
    canvas.paste(logo, (50, (H - lh)//2), logo)
    text_x = 50 + lw + 40

    draw = ImageDraw.Draw(canvas)
    draw.line([(text_x - 20, 30), (text_x - 20, H - 30)], fill="white", width=3)
else:
    text_x = 50
    draw = ImageDraw.Draw(canvas)

# 4. Text
try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
except:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

draw.text((text_x, (H//2) - 45), "DASHBOARD TABUNGAN, GIRO & DEPOSITO", font=font_title, fill="white")
draw.text((text_x, (H//2) + 10), "📅 Data per 28 Jun 2026 WIB", font=font_sub, fill="white")

canvas.save("test_header3.png")
