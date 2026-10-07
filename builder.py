import json
import os

with open("figma_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

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
        return f"rgba({r},{g},{b},{a:.2f})"
    return f"rgb({r},{g},{b})"

def get_fill_css(node):
    fills = node.get("fills", [])
    if fills and len(fills) > 0 and fills[0].get("visible", True) != False:
        fill = fills[0]
        if fill["type"] == "SOLID":
            return rgba_to_css(fill["color"], fill.get("opacity", 1.0))
    return "transparent"

def get_stroke_css(node, frame_h):
    strokes = node.get("strokes", [])
    if strokes and len(strokes) > 0 and strokes[0].get("visible", True) != False:
        st = strokes[0]
        if st["type"] == "SOLID":
            color = rgba_to_css(st["color"], st.get("opacity", 1.0))
            weight = node.get("strokeWeight", 1.0)
            weight_cqh = (weight / frame_h) * 100
            return f"border: {weight_cqh:.3f}cqh solid {color}; box-sizing: border-box;"
    return ""

def collect_html(node, frame_x, frame_y, frame_w, frame_h, out_list):
    bounds = node.get("absoluteBoundingBox")
    if not bounds:
        for child in node.get("children", []):
            collect_html(child, frame_x, frame_y, frame_w, frame_h, out_list)
        return

    left = (bounds["x"] - frame_x) / frame_w * 100
    top = (bounds["y"] - frame_y) / frame_h * 100
    width = bounds["width"] / frame_w * 100
    height = bounds["height"] / frame_h * 100

    # Vectors & Shapes
    if node["type"] in ["VECTOR", "BOOLEAN_OPERATION", "STAR", "LINE", "ELLIPSE", "REGULAR_POLYGON"]:
        safe_id = node['id'].replace(':','_')
        if os.path.exists(f"svgs/{safe_id}.svg"):
            tag = f"<img id='{node['id']}' src='svgs/{safe_id}.svg' style='position:absolute; left:{left:.3f}%; top:{top:.3f}%; width:{width:.3f}%; height:{height:.3f}%; object-fit:contain;' />"
            out_list.append(tag)
        return

    # Text
    if node["type"] == "TEXT":
        style = node.get("style", {})
        font_size_px = style.get("fontSize", 16)
        font_size = (font_size_px / frame_h) * 100
        font_weight = style.get("fontWeight", 400)
        color = get_fill_css(node)
        text_align = style.get("textAlignHorizontal", "LEFT").lower()
        if text_align == "justified": text_align = "left"

        chars_raw = node.get("characters", "")
        chars = chars_raw.replace("\n", "<br>")

        lh_px = style.get("lineHeightPx", font_size_px * 1.15)
        lh_ratio = lh_px / font_size_px if font_size_px > 0 else 1.15

        # Check if text is centered in Figma design
        is_centered = (text_align == "center") or (node.get("name") in ["SOS", "Help instruction", "Cancel", "Swipe up anywhere to add details"]) or (chars_raw in ["SOS", "PRESS TO REQUEST HELP", "Cancel", "Swipe up anywhere to add details"])

        if is_centered:
            center_x = bounds["x"] + bounds["width"] / 2.0
            left_pct = (center_x - frame_x) / frame_w * 100.0
            pos_css = f"left:{left_pct:.3f}%; top:{top:.3f}%; transform:translateX(-50%); text-align:center;"
        else:
            pos_css = f"left:{left:.3f}%; top:{top:.3f}%; text-align:{text_align};"

        # Check wrapping: allow wrap only if height > 1.6 * fontSize and no manual newlines
        if bounds["height"] > font_size_px * 1.6 and "\n" not in chars_raw:
            wrap_css = f"width:{width:.3f}%; white-space:normal;"
        else:
            wrap_css = "width:max-content; white-space:nowrap;"

        css = f"position:absolute; {pos_css} {wrap_css} height:max-content; font-size:{font_size:.3f}cqh; font-weight:{font_weight}; color:{color}; line-height:{lh_ratio:.3f}; display:flex; flex-direction:column; overflow:visible;"

        out_list.append(f"<div style='{css}'><span>{chars}</span></div>")
        return

    # Frame / Rectangle
    if node["type"] not in ["DOCUMENT", "CANVAS"]:
        bg = get_fill_css(node)
        stroke_css = get_stroke_css(node, frame_h)
        radius = node.get("cornerRadius", 0)
        radius_cqh = (radius / frame_h) * 100

        if bg != "transparent" or radius_cqh > 0 or stroke_css:
            css_parts = [
                f"position:absolute;",
                f"left:{left:.3f}%;",
                f"top:{top:.3f}%;",
                f"width:{width:.3f}%;",
                f"height:{height:.3f}%;",
                f"pointer-events:none;"
            ]
            if bg != "transparent":
                css_parts.append(f"background:{bg};")
            if radius_cqh > 0:
                css_parts.append(f"border-radius:{radius_cqh:.3f}cqh;")
            if stroke_css:
                css_parts.append(stroke_css)

            out_list.append(f"<div style='{' '.join(css_parts)}'></div>")

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
            const target = document.getElementById(id);
            if (target) {
                target.style.display = 'block';
            }
        }

        function createOverlay(screenId, left, top, width, height, targetId) {
            const screen = document.getElementById(screenId);
            if (!screen) return;
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
            screen.appendChild(overlay);
        }

        // Home screen -> SOS button
        createOverlay('home', 4.5, 58.5, 91.0, 33.3, 'sending_alert');

        // Sending alert -> Cancel button
        createOverlay('sending_alert', 4.5, 82.1, 91.0, 9.8, 'home');

        // SOS Active -> Worse button
        createOverlay('sos_active', 51.4, 62.7, 44.0, 10.7, 'sos_situation_worse');

        // SOS Active -> Cancel SOS button
        createOverlay('sos_active', 4.5, 74.9, 91.0, 7.5, 'home');

        // SOS Active -> Swipe up anywhere (bottom area)
        createOverlay('sos_active', 0.0, 83.0, 100.0, 17.0, 'situation_category');

        // Situation Category -> Fire or smoke card
        createOverlay('situation_category', 4.5, 25.8, 44.0, 11.7, 'fire_details');

        // Fire Details -> Send details button
        createOverlay('fire_details', 5.1, 86.1, 89.7, 6.8, 'sos_situation_worse');

        // SOS Situation Worse -> Cancel SOS button
        createOverlay('sos_situation_worse', 4.5, 77.0, 91.0, 7.5, 'home');

        // Safe screen -> Done button
        createOverlay('safe', 4.5, 89.9, 91.0, 5.9, 'home');

        let timeoutId;
        function handleAutoTriggers(screenId) {
            clearTimeout(timeoutId);
            if (screenId === 'sending_alert') {
                timeoutId = setTimeout(() => showScreen('sos_active'), 2500);
            } else if (screenId === 'sos_situation_worse') {
                timeoutId = setTimeout(() => showScreen('safe'), 3200);
            }
        }
    });
    """

    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Harbor - Paytm Design Task</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }}
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }}
        /* Strictly lock aspect ratio to exact Figma frame proportions: 852 / 1844 */
        .phone-wrapper {{
            position: relative;
            aspect-ratio: 852 / 1844;
            width: min(100vw, calc(100vh * (852 / 1844)));
            height: min(100vh, calc(100vw * (1844 / 852)));
            max-width: 100vw;
            max-height: 100vh;
            margin: auto;
            overflow: hidden;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            container-type: size;
            user-select: none;
            box-shadow: 0 0 60px rgba(0, 0, 0, 0.9);
        }}
        .phone-wrapper * {{
            pointer-events: none;
        }}
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
    print("Successfully built exact pixel-accurate SPA in index.html")

if __name__ == "__main__":
    build()
