import json
import os

with open("figma_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# The mapping from node ID to screen ID
screens = {
    "21:250": "home",
    "21:3525": "sending_alert",
    "21:3541": "sos_active",
    "21:3587": "situation_category",
    "21:3664": "fire_details",
    "21:3754": "sos_situation_worse",
    "21:3806": "safe"
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
        
        chars = node.get("characters", "").replace("\n", "<br>")
        
        css = f"position:absolute; left:{left}%; top:{top}%; width:{width}%; height:{height}%; font-size:{font_size}cqh; font-weight:{font_weight}; color:{color}; text-align:{text_align}; line-height: 1.15; display:flex; flex-direction:column; justify-content:{'center' if text_align=='center' else 'flex-start'}; white-space:pre-wrap; overflow:visible;"
        
        out_list.append(f"<div style='{css}'><span>{chars}</span></div>")
        return

    # Frame / Rectangle
    if node["type"] != "DOCUMENT" and node["type"] != "CANVAS":
        bg = get_fill_css(node)
        radius = node.get("cornerRadius", 0)
        radius_cqh = (radius / frame_h) * 100
        
        if bg != "transparent" or radius_cqh > 0:
            css = f"position:absolute; left:{left}%; top:{top}%; width:{width}%; height:{height}%; pointer-events:none;"
            if bg != "transparent":
                css += f" background:{bg};"
            if radius_cqh > 0:
                css += f" border-radius:{radius_cqh}cqh;"
            out_list.append(f"<div style='{css}'></div>")
    
    for child in node.get("children", []):
        collect_html(child, frame_x, frame_y, frame_w, frame_h, out_list)

def build():
    all_screens_html = ""
    first = True
    
    for node_id, screen_name in screens.items():
        node = data["nodes"][node_id]["document"]
        bounds = node["absoluteBoundingBox"]
        frame_x, frame_y = bounds["x"], bounds["y"]
        frame_w, frame_h = bounds["width"], bounds["height"]
        
        bg = get_fill_css(node)
        
        out_list = []
        collect_html(node, frame_x, frame_y, frame_w, frame_h, out_list)
        inner_html = "\n".join(out_list)
        
        display = "block" if first else "none"
        first = False
        
        screen_html = f"""
        <div id="{screen_name}" class="screen" style="display:{display}; width:100%; height:100%; position:absolute; top:0; left:0; background:{bg};">
            {inner_html}
        </div>
        """
        all_screens_html += screen_html

    js_code = """
    document.addEventListener("DOMContentLoaded", () => {
        function showScreen(id) {
            document.querySelectorAll('.screen').forEach(s => s.style.display = 'none');
            document.getElementById(id).style.display = 'block';
        }

        function createOverlay(screenId, left, top, width, height, targetId) {
            const overlay = document.createElement('div');
            overlay.style.position = 'absolute';
            overlay.style.left = left + '%';
            overlay.style.top = top + '%';
            overlay.style.width = width + '%';
            overlay.style.height = height + '%';
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '9999';
            overlay.style.pointerEvents = 'auto';
            
            overlay.onclick = () => {
                showScreen(targetId);
                handleAutoTriggers(targetId);
            };
            document.getElementById(screenId).appendChild(overlay);
        }

        // Home
        createOverlay('home', 5, 50, 90, 40, 'sending_alert');
        
        // Sending Alert
        createOverlay('sending_alert', 5, 80, 90, 15, 'home');
        
        // SOS Active
        createOverlay('sos_active', 5, 87, 90, 10, 'situation_category');
        createOverlay('sos_active', 50, 60, 45, 10, 'sos_situation_worse');
        createOverlay('sos_active', 5, 70, 90, 10, 'home');
        
        // Situation Category
        createOverlay('situation_category', 5, 20, 45, 15, 'fire_details');
        
        // Fire Details
        createOverlay('fire_details', 5, 85, 90, 10, 'sos_situation_worse');
        
        // Safe
        createOverlay('safe', 5, 85, 90, 10, 'home');
        
        let timeoutId;
        function handleAutoTriggers(screenId) {
            clearTimeout(timeoutId);
            if (screenId === 'sending_alert') {
                timeoutId = setTimeout(() => showScreen('sos_active'), 2500);
            } else if (screenId === 'sos_situation_worse') {
                timeoutId = setTimeout(() => showScreen('safe'), 3000);
            }
        }
    });
    """

    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harbor SPA</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        body {{ margin:0; padding:0; background:#000; display:flex; justify-content:center; align-items:center; height:100vh; overflow:hidden; }}
        .phone-wrapper {{ position:relative; width:100%; height:100%; max-height:100vh; max-width:calc(100vh * (852 / 1844)); overflow:hidden; font-family:'Inter', sans-serif; container-type: size; user-select:none; margin: 0 auto; aspect-ratio: 852/1844; }}
        .phone-wrapper * {{ pointer-events: none; }}
    </style>
</head>
<body>
    <div class="phone-wrapper">
        {all_screens_html}
        <script>
            {js_code}
        </script>
    </div>
</body>
</html>'''

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
        
    print(f"Generated SPA in index.html.")

if __name__ == "__main__":
    build()
