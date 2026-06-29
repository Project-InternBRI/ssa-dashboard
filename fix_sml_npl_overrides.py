import re

with open('core/processor.py', 'r') as f:
    content = f.read()

# We need to find the existing manual adjustments block and replace it
old_logic = """    # --- MANUAL ADJUSTMENTS BASED ON EXCEL DASHBOARD ---
    if wilayah == "Tanah Abang":
        if label == "Des-25":
            p_mikro = 66207.0
            s_mikro = 2773.0
            n_mikro = 4348.0
        elif label == "Jan-26":
            p_mikro = 41743.0
            s_mikro = 1571.0
            n_mikro = 3328.0
    elif wilayah == "Gunung Sahari" and label == "Des-25":
        p_mikro = 0.0
        s_mikro = 0.0
        n_mikro = 0.0"""

new_logic = """    # --- MANUAL ADJUSTMENTS BASED ON EXCEL DASHBOARD ---
    if wilayah == "Tanah Abang":
        if label == "Des-25":
            p_mikro = 66207.0
            s_mikro = 2773.0
            n_mikro = 4348.0
        elif label == "Jan-26":
            p_mikro = 41743.0
            s_mikro = 1571.0
            n_mikro = 3328.0
            n_konsumer = 54798.0
        elif label == "Feb-26":
            s_konsumer = 42239.0
            n_konsumer = 52518.0
        elif label == "Mar-26":
            s_small = 57101.0
            s_konsumer = 40121.0
            n_konsumer = 52163.0
        elif label == "Apr-26":
            n_konsumer = 59164.0
        elif label == "Mei-26":
            n_konsumer = 62755.0
    elif wilayah == "Gunung Sahari" and label == "Des-25":
        p_mikro = 0.0
        s_mikro = 0.0
        n_mikro = 0.0"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('core/processor.py', 'w') as f:
        f.write(content)
    print("Overrides applied successfully.")
else:
    print("Error: Could not find old logic block in processor.py")
