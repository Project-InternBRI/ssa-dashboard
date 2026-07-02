from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1600, 72
bg_path = 'assets/background_header_excel_dashboard.png'

# 1. Base Canvas
base_color = (2, 55, 142, 255)
canvas = Image.new("RGBA", (W, H), base_color)

# 2. Right-side Background
if os.path.exists(bg_path):
    orig_bg = Image.open(bg_path).convert("RGBA")
    
    # We want it to cover the right 800 pixels
    piece_w = 800
    piece_h = int(orig_bg.height * (piece_w / orig_bg.width))
    piece = orig_bg.resize((piece_w, piece_h), Image.Resampling.LANCZOS)
    
    # Crop vertical center to fit H
    y_offset = (piece_h - H) // 2
    piece = piece.crop((0, y_offset, piece_w, y_offset + H))
    
    # Create alpha gradient mask for blending
    mask = Image.new("L", (piece_w, H), 255)
    fade_width = 300 # Pixels to fade
    for x in range(fade_width):
        alpha = int(255 * (x / fade_width))
        for y in range(H):
            mask.putpixel((x, y), alpha)
            
    piece.putalpha(mask)
    
    # Paste onto right side of canvas
    canvas.paste(piece, (W - piece_w, 0), piece)

# Save to check
canvas.save("test_header2_base.png")
