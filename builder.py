import json
import os

with open("figma_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

screens = {
    "21:250": "index.html",
    "21:3525": "sending_alert.html",
    "21:3541": "sos_active.html",
    "21:3587": "situation_category.html",
    "21:3664": "fire_details.html",
    "21:3754": "sos_situation_worse.html",
    "21:3806": "safe.html"
}

def rgba_to_css(color, opacity=1.0):
    r = round(color['r'] * 255)
    g = round(color['g'] * 255)
    b = round(color['b'] * 255)
    a = color.get('a', 1.0) * opacity
    if a < 1.0:
        return f"rgba({r},{g},{b},{a})"
    return f"rgb({r},{g},{b})"

def get_fill_css(node):
    fills = node.get("fills", [])
    if fills and len(fills) > 0 and fills[0].get("visible", True) != False:
        fill = fills[0]
        if fill["type"] == "SOLID":
            return rgba_to_css(fill["color"], fill.get("opacity", 1.0))
    return "transparent"

def has_text_descendant(node):
    if node["type"] == "TEXT":
        return True
    for child in node.get("children", []):
        if has_text_descendant(child):
            return True
    return False

def contains_vector(n):
    if n["type"] == "VECTOR": return True
    if "children" in n:
        return any(contains_vector(c) for c in n["children"])
    return False

# We will collect a flat list of HTML snippets
def collect_html(node, frame_x, frame_y, frame_w, frame_h, out_list):
    is_pure_graphic = (not has_text_descendant(node)) and contains_vector(node)
    
    bounds = node.get("absoluteBoundingBox")
    if not bounds:
        # If no bounds, just process children
        for child in node.get("children", []):
            collect_html(child, frame_x, frame_y, frame_w, frame_h, out_list)
        return

    left = (bounds["x"] - frame_x) / frame_w * 100
    top = (bounds["y"] - frame_y) / frame_h * 100
    width = bounds["width"] / frame_w * 100
    height = bounds["height"] / frame_h * 100

    if is_pure_graphic:
        tag = f"<img id='{node['id']}' src='svgs/{node['id'].replace(':','_')}.svg' style='position:absolute; left:{left}%; top:{top}%; width:{width}%; height:{height}%; object-fit:contain;' />"
        out_list.append(tag)
        return

    if node["type"] == "TEXT":
        style = node.get("style", {})
        font_size = (style.get("fontSize", 16) / frame_h) * 100
        font_weight = style.get("fontWeight", 400)
        color = get_fill_css(node)
        text_align = style.get("textAlignHorizontal", "LEFT").lower()
        if text_align == "justified": text_align = "left"
        
        # Use white-space: pre-wrap so explicit newlines in Figma are honored
        chars = node.get("characters", "").replace("\n", "<br>")
        
        # The line height in Figma might be specified. If not, 1.2 is safe.
        css = f"position:absolute; left:{left}%; top:{top}%; width:{width}%; height:{height}%; font-size:{font_size}cqh; font-weight:{font_weight}; color:{color}; text-align:{text_align}; line-height: 1.15; display:flex; flex-direction:column; justify-content:{'center' if text_align=='center' else 'flex-start'}; white-space:pre-wrap; overflow:visible;"
        
        # In Figma, text bounding box might exactly fit the text.
        # But in HTML, web fonts might clip. We allow overflow:visible.
        out_list.append(f"<div style='{css}'><span>{chars}</span></div>")
        return

    # Frame / Rectangle
    if node["type"] != "DOCUMENT" and node["type"] != "CANVAS":
        bg = get_fill_css(node)
        radius = node.get("cornerRadius", 0)
        radius_cqh = (radius / frame_h) * 100
        
        # We only render the background div if it actually has a visible background or radius
        if bg != "transparent" or radius_cqh > 0:
            css = f"position:absolute; left:{left}%; top:{top}%; width:{width}%; height:{height}%; pointer-events:none;"
            if bg != "transparent":
                css += f" background:{bg};"
            if radius_cqh > 0:
                css += f" border-radius:{radius_cqh}cqh;"
            out_list.append(f"<div style='{css}'></div>")
    
    # Process children
    for child in node.get("children", []):
        collect_html(child, frame_x, frame_y, frame_w, frame_h, out_list)


def build():
    for node_id, filename in screens.items():
        node = data["nodes"][node_id]["document"]
        bounds = node["absoluteBoundingBox"]
        frame_x, frame_y = bounds["x"], bounds["y"]
        frame_w, frame_h = bounds["width"], bounds["height"]
        
        bg = get_fill_css(node)
        
        out_list = []
        collect_html(node, frame_x, frame_y, frame_w, frame_h, out_list)
        inner_html = "\n".join(out_list)
        
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harbor</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        body {{ margin:0; padding:0; background:#000; display:flex; justify-content:center; align-items:center; height:100vh; overflow:hidden; }}
        .phone-wrapper {{ position:relative; width:100%; height:100%; max-height:100vh; max-width:calc(100vh * (852 / 1844)); background:{bg}; overflow:hidden; font-family:'Inter', sans-serif; container-type: size; user-select:none; margin: 0 auto; aspect-ratio: 852/1844; }}
        .phone-wrapper * {{ pointer-events: none; }} /* Let overlays handle clicks */
    </style>
</head>
<body>
    <div class="phone-wrapper">
        {inner_html}
        <script src="interactions.js"></script>
    </div>
</body>
</html>'''
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_template)
            
    print(f"Generated {len(screens)} HTML files.")

if __name__ == "__main__":
    build()
