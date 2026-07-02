from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1900, 135
bg_path = 'assets/background_header_excel_dashboard.png'

canvas = Image.new("RGBA", (W, H), (2, 55, 142, 255))

if os.path.exists(bg_path):
    orig_bg = Image.open(bg_path).convert("RGBA")
    
    # 1. Resize background so it fits height fully, no cropping!
    piece_h = H
    piece_w = int(orig_bg.width * (piece_h / orig_bg.height))
    piece = orig_bg.resize((piece_w, piece_h), Image.Resampling.LANCZOS)
    
    # 2. Smooth gradient on the left edge
    mask = Image.new("L", (piece_w, piece_h), 255)
    fade_width = 150 # smooth transition
    for x in range(fade_width):
        alpha = int(255 * ((x / fade_width) ** 2)) # Quadratic fade for smoother look
        for y in range(piece_h):
            mask.putpixel((x, y), alpha)
            
    piece.putalpha(mask)
    canvas.paste(piece, (W - piece_w, 0), piece)

# Print piece dimensions
print("piece_w:", piece_w, "piece_h:", piece_h)

# Check logo
logo_path = 'assets/icons/bri_logo.png'
if os.path.exists(logo_path):
    orig_logo = Image.open(logo_path).convert("RGBA")
    alpha = orig_logo.split()[3]
    white_logo = Image.new("RGBA", orig_logo.size, (255, 255, 255, 255))
    white_logo.putalpha(alpha)
    logo = white_logo
    print("Logo size:", logo.width, logo.height)
