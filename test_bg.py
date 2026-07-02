from PIL import Image

def color_to_alpha_white(img_path, out_path):
    img = Image.open(img_path).convert("RGBA")
    data = img.load()
    w, h = img.size
    
    # We detect the actual background color by looking at the top-left corner
    # because it might be 253 or 254 instead of 255
    bg_r, bg_g, bg_b, _ = data[0,0]
    
    for y in range(h):
        for x in range(w):
            r, g, b, a = data[x, y]
            
            # Distance from the background color
            # We assume the background is white-ish
            # Simple color to alpha for white:
            # Alpha is based on how dark the pixel is.
            # a_new = 255 - min(r, g, b)
            
            # Since bg is not exactly 255, let's normalize
            norm_r = r / bg_r if bg_r > 0 else 1.0
            norm_g = g / bg_g if bg_g > 0 else 1.0
            norm_b = b / bg_b if bg_b > 0 else 1.0
            
            min_val = min(norm_r, norm_g, norm_b)
            if min_val >= 1.0:
                data[x, y] = (bg_r, bg_g, bg_b, 0)
            else:
                a_new = int((1.0 - min_val) * 255)
                # Recover original color
                # P = F * A + B * (1-A)
                # F = (P - B * (1-A)) / A
                A = a_new / 255.0
                fr = int(max(0, min(255, (r - bg_r * (1 - A)) / A)))
                fg = int(max(0, min(255, (g - bg_g * (1 - A)) / A)))
                fb = int(max(0, min(255, (b - bg_b * (1 - A)) / A)))
                data[x, y] = (fr, fg, fb, a_new)
                
    img.save(out_path)

color_to_alpha_white("assets/illust_dash_wait.png", "assets/illust_dash_wait_alpha.png")
color_to_alpha_white("assets/illust_dash_done.png", "assets/illust_dash_done_alpha.png")
print("Done")
