from PIL import Image, ImageDraw

def add_circle_bg(input_path, output_path, bg_color):
    try:
        icon = Image.open(input_path).convert("RGBA")
        
        # Colorize the icon to white (assuming it is mostly black/dark)
        # We can extract the alpha channel, create a solid white image, and put the alpha back
        alpha = icon.split()[3]
        white_icon = Image.new("RGBA", icon.size, (255, 255, 255, 255))
        white_icon.putalpha(alpha)
        
        # Resize if necessary to a standard size for the icon
        white_icon.thumbnail((40, 40))
        
        # Create a new image with a transparent background
        size = 64
        new_img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        
        # Draw the colored circle
        draw = ImageDraw.Draw(new_img)
        draw.ellipse((0, 0, size, size), fill=bg_color)
        
        # Calculate position to center the icon
        paste_pos = ((size - white_icon.width) // 2, (size - white_icon.height) // 2)
        
        # Paste the white icon using its alpha channel as a mask
        new_img.paste(white_icon, paste_pos, white_icon)
        
        new_img.save(output_path)
        print(f"Success: {output_path}")
    except Exception as e:
        print(f"Error {input_path}: {e}")

# We need to process from the original SVGs again, or the user's latest PNGs?
# Since we overwrote them in the previous script, they already have a circle background!
# If we do it again, it'll apply white to the entire circle and draw a new circle behind it.
