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

        is_centered = (text_align == "center") or (node.get("name") in ["SOS", "Help instruction", "Cancel", "Swipe up anywhere to add details"]) or (chars_raw in ["SOS", "PRESS TO REQUEST HELP", "Cancel", "Swipe up anywhere to add details"])

        if is_centered:
            center_x = bounds["x"] + bounds["width"] / 2.0
            left_pct = (center_x - frame_x) / frame_w * 100.0
            pos_css = f"left:{left_pct:.3f}%; top:{top:.3f}%; transform:translateX(-50%); text-align:center;"
        else:
            pos_css = f"left:{left:.3f}%; top:{top:.3f}%; text-align:{text_align};"

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

def build_all():
    # Build prototype screens HTML
    all_screens_html = ""
    home_screen_inner = ""
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

        if screen_name == "home":
            home_screen_inner = inner_html

        display = "block" if first else "none"
        first = False

        screen_html = f"""
        <div id="{screen_name}" class="screen" style="display:{display}; width:100%; height:100%; position:absolute; top:0; left:0; background:{bg};">
            {inner_html}
        </div>
        """
        all_screens_html += screen_html

    # Read double diamond SVG
    with open("double_diamond.svg", "r", encoding="utf-8") as f:
        double_diamond_svg = f.read()

    prototype_url = "https://v1khyat.github.io/PayTm-Design-Task/"

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>Harbor · Superhero Emergency Alert App</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #08090d;
            --bg-card: rgba(18, 20, 29, 0.75);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-focus: rgba(239, 68, 68, 0.4);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-red: #ef4444;
            --accent-crimson: #e11d48;
            --accent-blue: #3b82f6;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}

        body {{
            background: var(--bg-dark);
            color: var(--text-primary);
            font-family: var(--font-main);
            overflow-x: hidden;
            min-height: 100vh;
        }}

        /* ==========================================================================
           PROTOTYPE VIEW MODE
           ========================================================================== */
        #prototype-viewport {{
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #000;
            overflow: hidden;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 100;
        }}

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

        /* ==========================================================================
           PRESENTATION MODE (High-End Scrolling Website)
           ========================================================================== */
        #presentation-viewport {{
            display: none;
            width: 100%;
            min-height: 100vh;
            background: var(--bg-dark);
            position: relative;
            z-index: 200;
            overflow-y: auto;
            scroll-behavior: smooth;
        }}

        /* Background atmospheric mesh glow */
        .ambient-mesh {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 0;
            background: 
                radial-gradient(circle at 15% 20%, rgba(225, 29, 72, 0.08) 0%, transparent 45%),
                radial-gradient(circle at 85% 65%, rgba(59, 130, 246, 0.06) 0%, transparent 50%),
                radial-gradient(circle at 50% 90%, rgba(239, 68, 68, 0.05) 0%, transparent 40%);
        }}

        /* Persistent Navigation / Brand Header */
        .pres-nav {{
            position: sticky;
            top: 0;
            width: 100%;
            padding: 1.25rem 2.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(8, 9, 13, 0.82);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-glass);
            z-index: 50;
        }}

        .pres-nav-brand {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }}

        .pres-logo-icon {{
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, var(--accent-crimson), #fb7185);
            border-radius: 7px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: 900;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(225, 29, 72, 0.35);
        }}

        .pres-nav-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: #fff;
            letter-spacing: -0.02em;
        }}

        .pres-nav-badge {{
            font-family: var(--font-mono);
            font-size: 0.72rem;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-secondary);
            border: 1px solid var(--border-glass);
        }}

        .pres-nav-actions {{
            display: flex;
            align-items: center;
            gap: 1.25rem;
        }}

        .btn-live-prototype {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(239, 68, 68, 0.12);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 0.5rem 1.15rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
        }}

        .btn-live-prototype:hover {{
            background: rgba(239, 68, 68, 0.22);
            border-color: rgba(239, 68, 68, 0.5);
            color: #fff;
            transform: translateY(-1px);
        }}

        .pulse-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #ef4444;
            box-shadow: 0 0 8px #ef4444;
            animation: pulse 1.8s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.85); }}
        }}

        /* Main Scrolling Content Area */
        .pres-container {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 3rem 2.5rem 6rem;
            position: relative;
            z-index: 10;
        }}

        /* Common Section Layout */
        .pres-section {{
            min-height: calc(100vh - 120px);
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 4.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            position: relative;
        }}

        .pres-section:last-of-type {{
            border-bottom: none;
        }}

        /* Kicker Label */
        .pres-kicker {{
            font-family: var(--font-mono);
            font-size: 0.8125rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #fb7185;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.65rem;
        }}

        .pres-kicker::before {{
            content: '';
            display: inline-block;
            width: 18px;
            height: 2px;
            background: #e11d48;
        }}

        /* Section Headings */
        .pres-title {{
            font-size: clamp(3.2rem, 6.5vw, 5.75rem);
            font-weight: 800;
            color: #fff;
            letter-spacing: -0.04em;
            line-height: 1.04;
            margin-bottom: 1.5rem;
        }}

        .pres-subline {{
            font-size: clamp(1.25rem, 2.2vw, 1.85rem);
            font-weight: 400;
            color: #cbd5e1;
            line-height: 1.45;
            max-width: 780px;
            letter-spacing: -0.015em;
            margin-bottom: 3.5rem;
        }}

        /* Running Footers */
        .pres-footer {{
            margin-top: auto;
            padding-top: 3.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.95rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-glass);
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .pres-footer a.prototype-link {{
            color: #38bdf8;
            text-decoration: none;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            transition: color 0.2s ease;
        }}

        .pres-footer a.prototype-link:hover {{
            color: #7dd3fc;
            text-decoration: underline;
        }}

        /* ==========================================================================
           SECTION 1: HERO / COVER
           ========================================================================== */
        .hero-grid {{
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 4rem;
            align-items: center;
            width: 100%;
        }}

        .hero-left {{
            display: flex;
            flex-direction: column;
        }}

        .hero-stats-row {{
            display: flex;
            gap: 2.5rem;
            margin-bottom: 2rem;
            padding: 1.5rem 0;
            border-top: 1px solid var(--border-glass);
            border-bottom: 1px solid var(--border-glass);
        }}

        .hero-stat-item {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .hero-stat-label {{
            font-family: var(--font-mono);
            font-size: 0.72rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .hero-stat-value {{
            font-size: 1.15rem;
            font-weight: 700;
            color: #f1f5f9;
        }}

        /* Phone Device Mockup Showcase */
        .hero-mockup-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }}

        .mockup-backdrop-glow {{
            position: absolute;
            width: 340px;
            height: 600px;
            background: radial-gradient(circle, rgba(225, 29, 72, 0.28) 0%, transparent 70%);
            filter: blur(54px);
            z-index: 1;
        }}

        .device-phone-chassis {{
            position: relative;
            z-index: 2;
            width: 360px;
            height: calc(360px * (1844 / 852));
            background: #111317;
            border-radius: 54px;
            padding: 10px;
            box-shadow: 
                0 32px 80px -15px rgba(0, 0, 0, 0.9),
                0 0 0 1px rgba(255, 255, 255, 0.14),
                inset 0 0 0 2px rgba(255, 255, 255, 0.08);
            transform: perspective(1200px) rotateY(-4deg) rotateX(2deg);
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.4s ease;
        }}

        .device-phone-chassis:hover {{
            transform: perspective(1200px) rotateY(0deg) rotateX(0deg) scale(1.02);
            box-shadow: 
                0 42px 100px -10px rgba(225, 29, 72, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.22);
        }}

        .device-screen-bezel {{
            position: relative;
            width: 100%;
            height: 100%;
            aspect-ratio: 852 / 1844;
            border-radius: 44px;
            overflow: hidden;
            background: rgb(250, 249, 247);
            container-type: size;
        }}

        .device-screen-bezel .screen {{
            display: block !important;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}

        /* ==========================================================================
           SECTION 2: THE BRIEF & REFRAME
           ========================================================================== */
        .brief-layout {{
            display: flex;
            flex-direction: column;
            gap: 3.5rem;
            width: 100%;
        }}

        .asked-vs-testing-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2.5rem;
            width: 100%;
        }}

        .comparison-col {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .col-header-pill {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-family: var(--font-mono);
            font-size: 0.8125rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            padding: 0.65rem 1.25rem;
            border-radius: 12px;
            width: fit-content;
        }}

        .col-left-pill {{
            background: rgba(148, 163, 184, 0.08);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.15);
        }}

        .col-right-pill {{
            background: rgba(59, 130, 246, 0.12);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.25);
        }}

        .brief-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 20px;
            padding: 2rem;
            backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            gap: 0.85rem;
            position: relative;
            transition: all 0.25s ease;
        }}

        .brief-card:hover {{
            border-color: rgba(255, 255, 255, 0.18);
            transform: translateY(-2px);
            background: rgba(26, 30, 44, 0.85);
        }}

        .brief-card-num {{
            font-family: var(--font-mono);
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--accent-red);
            letter-spacing: 0.1em;
        }}

        .brief-card-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #fff;
            letter-spacing: -0.02em;
            line-height: 1.3;
        }}

        .brief-card-desc {{
            font-size: 0.95rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }}

        /* The Reframe Callout (Punchline - Greatest Weight) */
        .reframe-banner-card {{
            position: relative;
            background: linear-gradient(135deg, rgba(225, 29, 72, 0.12) 0%, rgba(17, 24, 39, 0.85) 60%, rgba(8, 9, 13, 0.95) 100%);
            border: 1.5px solid rgba(225, 29, 72, 0.35);
            border-radius: 28px;
            padding: 3.5rem 3.5rem;
            overflow: hidden;
            box-shadow: 
                0 24px 60px rgba(225, 29, 72, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }}

        .reframe-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #fb7185;
            background: rgba(225, 29, 72, 0.15);
            border: 1px solid rgba(225, 29, 72, 0.3);
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            margin-bottom: 1.5rem;
        }}

        .reframe-punchline {{
            font-size: clamp(1.85rem, 3.4vw, 2.85rem);
            font-weight: 800;
            color: #ffffff;
            line-height: 1.22;
            letter-spacing: -0.03em;
            margin-bottom: 1.25rem;
        }}

        .reframe-punchline span.highlight {{
            background: linear-gradient(120deg, #fca5a5, #f43f5e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .reframe-subtext {{
            font-size: 1.15rem;
            color: #cbd5e1;
            line-height: 1.6;
            max-width: 820px;
        }}

        /* ==========================================================================
           SECTION 3: THE PROCESS & DOUBLE DIAMOND
           ========================================================================== */
        .process-layout {{
            display: flex;
            flex-direction: column;
            gap: 3.5rem;
            width: 100%;
        }}

        .caption-card {{
            display: flex;
            align-items: center;
            gap: 1.25rem;
            padding: 1.25rem 2rem;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            width: fit-content;
        }}

        .caption-icon {{
            font-size: 1.2rem;
        }}

        .caption-text {{
            font-size: 1.15rem;
            font-weight: 600;
            color: #f1f5f9;
            letter-spacing: -0.01em;
        }}

        .diamond-diagram-container {{
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 28px;
            padding: 3rem 2.5rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
        }}

        /* 7 Phases Breakdown Cards */
        .phases-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 1rem;
            width: 100%;
            margin-top: 2rem;
        }}

        .phase-step-card {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-glass);
            border-radius: 14px;
            padding: 1.15rem 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            transition: all 0.2s ease;
        }}

        .phase-step-card:hover {{
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }}

        .phase-num {{
            font-family: var(--font-mono);
            font-size: 0.72rem;
            font-weight: 700;
            color: #94a3b8;
        }}

        .phase-name {{
            font-size: 0.92rem;
            font-weight: 700;
            color: #fff;
            line-height: 1.25;
        }}

        .phase-type {{
            font-size: 0.75rem;
            color: #64748b;
        }}

        /* Floating Mode Switch Notification (Top right indicator) */
        .shortcut-badge {{
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: #94a3b8;
            padding: 0.35rem 0.75rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-glass);
            border-radius: 8px;
        }}

        /* ==========================================================================
           PRINT / PDF EXPORT STYLES
           ========================================================================== */
        @media print {{
            body, html {{
                background: #08090d !important;
                color: #fff !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}

            #prototype-viewport {{
                display: none !important;
            }}

            #presentation-viewport {{
                display: block !important;
                overflow: visible !important;
            }}

            .pres-nav {{
                display: none !important;
            }}

            .pres-section {{
                page-break-after: always !important;
                break-after: page !important;
                min-height: 100vh !important;
                height: 100vh !important;
                padding: 3rem 2rem !important;
                box-sizing: border-box !important;
            }}

            .device-phone-chassis {{
                transform: none !important;
                box-shadow: 0 0 0 1px #333 !important;
            }}
        }}

        /* Responsive breakpoints */
        @media (max-width: 1024px) {{
            .hero-grid {{
                grid-template-columns: 1fr;
                gap: 3rem;
            }}
            .asked-vs-testing-grid {{
                grid-template-columns: 1fr;
            }}
            .phases-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .pres-section {{
                min-height: auto;
                padding: 3rem 0;
            }}
        }}
    </style>
</head>
<body>

    <!-- ==========================================================================
         MODE 1: INTERACTIVE MOBILE PROTOTYPE
         ========================================================================== -->
    <div id="prototype-viewport">
        <div class="phone-wrapper">
            {all_screens_html}
        </div>
    </div>

    <!-- ==========================================================================
         MODE 2: HIGH-END EDITORIAL PRESENTATION WEBSITE
         ========================================================================== -->
    <div id="presentation-viewport">
        <div class="ambient-mesh"></div>

        <!-- Sticky Top Navigation Bar -->
        <header class="pres-nav">
            <div class="pres-nav-brand">
                <div class="pres-logo-icon">H</div>
                <span class="pres-nav-title">Harbor</span>
                <span class="pres-nav-badge">Paytm Design Internship 2027</span>
            </div>
            <div class="pres-nav-actions">
                <button class="btn-live-prototype" onclick="togglePresentationMode(false)">
                    <span class="pulse-dot"></span>
                    <span>Switch to Interactive Prototype</span>
                </button>
            </div>
        </header>

        <main class="pres-container">

            <!-- ------------------------------------------------------------------
                 SECTION 1: COVER / HERO
                 ------------------------------------------------------------------ -->
            <section class="pres-section" id="section-cover">
                <div class="hero-grid">
                    <div class="hero-left">
                        <div class="pres-kicker">Paytm Design Internship 2027 · Design Task</div>
                        <h1 class="pres-title">Harbor</h1>
                        <p class="pres-subline">A superhero emergency alert app. One tap, and the right help is moving.</p>

                        <div class="hero-stats-row">
                            <div class="hero-stat-item">
                                <span class="hero-stat-label">Response Trigger</span>
                                <span class="hero-stat-value">1-Tap Immediate</span>
                            </div>
                            <div class="hero-stat-item">
                                <span class="hero-stat-label">Interface Paradigm</span>
                                <span class="hero-stat-value">Panic-First Sensory</span>
                            </div>
                            <div class="hero-stat-item">
                                <span class="hero-stat-label">Core Lifecycle</span>
                                <span class="hero-stat-value">5 Dynamic States</span>
                            </div>
                        </div>

                        <div style="display: flex; gap: 1rem; align-items: center;">
                            <button class="btn-live-prototype" onclick="togglePresentationMode(false)" style="padding: 0.75rem 1.5rem; font-size: 0.95rem;">
                                <span class="pulse-dot"></span>
                                <span>Launch Interactive Prototype ↗</span>
                            </button>
                        </div>
                    </div>

                    <!-- Right Visual: Large, Authentic Home Screen Mockup -->
                    <div class="hero-mockup-wrapper">
                        <div class="mockup-backdrop-glow"></div>
                        <div class="device-phone-chassis">
                            <div class="device-screen-bezel">
                                <div style="width: 100%; height: 100%; position: relative; background: rgb(250, 249, 247);">
                                    {home_screen_inner}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer Mirror 1 -->
                <footer class="pres-footer">
                    <div>Vikhyat Kaushik · October 2026</div>
                    <div>
                        <a href="{prototype_url}" class="prototype-link" target="_blank" onclick="event.preventDefault(); togglePresentationMode(false);">Interactive prototype link ↗</a>
                    </div>
                </footer>
            </section>


            <!-- ------------------------------------------------------------------
                 SECTION 2: THE BRIEF
                 ------------------------------------------------------------------ -->
            <section class="pres-section" id="section-brief">
                <div class="brief-layout">
                    <div>
                        <div class="pres-kicker">Problem Framing &amp; Objectives</div>
                        <h2 class="pres-title" style="font-size: clamp(2.5rem, 4.5vw, 4rem);">The brief</h2>
                    </div>

                    <!-- Visual: The "asked vs really testing" Two-Column -->
                    <div class="asked-vs-testing-grid">

                        <!-- Left Column: Deliverables As Written -->
                        <div class="comparison-col">
                            <div class="col-header-pill col-left-pill">
                                <span>Deliverables as Written</span>
                            </div>

                            <div class="brief-card">
                                <span class="brief-card-num">DELIVERABLE 01</span>
                                <h3 class="brief-card-title">Reach superheroes fast &amp; track request lifecycle</h3>
                                <p class="brief-card-desc">Full lifecycle tracking: raised, verified, assigned, responded, resolved with real-time updates.</p>
                            </div>

                            <div class="brief-card">
                                <span class="brief-card-num">DELIVERABLE 02</span>
                                <h3 class="brief-card-title">Include one critical edge case</h3>
                                <p class="brief-card-desc">Identify an unpredictable crisis condition (e.g. escalating threat severity, powers out of control) and build resilient system handling.</p>
                            </div>

                            <div class="brief-card">
                                <span class="brief-card-num">DELIVERABLE 03</span>
                                <h3 class="brief-card-title">Deliver interactive prototype link + PDF note</h3>
                                <p class="brief-card-desc">A functional, testable user flow accompanied by documented design rationale and clear behavioral assumptions.</p>
                            </div>
                        </div>

                        <!-- Right Column: What Each One Is Really Testing -->
                        <div class="comparison-col">
                            <div class="col-header-pill col-right-pill">
                                <span>What Each One Is Really Testing</span>
                            </div>

                            <div class="brief-card" style="border-left: 3px solid #3b82f6;">
                                <span class="brief-card-num" style="color: #60a5fa;">EVALUATING UX UNDER ADVERSITY</span>
                                <h3 class="brief-card-title">Designing for panic</h3>
                                <p class="brief-card-desc">When a user is under mortal threat, cognitive bandwidth drops to zero. Fine motor control degrades. Shaking hands cannot navigate dropdowns.</p>
                            </div>

                            <div class="brief-card" style="border-left: 3px solid #a855f7;">
                                <span class="brief-card-num" style="color: #c084fc;">EVALUATING SYSTEM CLARITY</span>
                                <h3 class="brief-card-title">Legible dispatch</h3>
                                <p class="brief-card-desc">Transparent hero routing that provides absolute certainty without sensory overload: showing hero tiers, ETA distance, and live location sharing.</p>
                            </div>

                            <div class="brief-card" style="border-left: 3px solid #22c55e;">
                                <span class="brief-card-num" style="color: #4ade80;">EVALUATING EMOTIONAL ANCHOR</span>
                                <h3 class="brief-card-title">Calm while waiting</h3>
                                <p class="brief-card-desc">The most dangerous window is the gap between alert and arrival. The interface must provide safety protocols and non-revealing stealth modes.</p>
                            </div>
                        </div>

                    </div>

                    <!-- The Reframe Line: Greatest Visual Weight -->
                    <div class="reframe-banner-card">
                        <div class="reframe-badge">The Central Reframe</div>
                        <h3 class="reframe-punchline">
                            This is not a dispatch dashboard. It is a <span class="highlight">panic-first product</span>.
                        </h3>
                        <p class="reframe-subtext">
                            Design for shaking hands, then earn trust while they wait.
                        </p>
                    </div>

                    <!-- Footer -->
                    <footer class="pres-footer" style="padding-top: 2rem;">
                        <div>Vikhyat Kaushik · October 2026</div>
                        <div>
                            <a href="{prototype_url}" class="prototype-link" target="_blank" onclick="event.preventDefault(); togglePresentationMode(false);">Interactive prototype link ↗</a>
                        </div>
                    </footer>
                </div>
            </section>


            <!-- ------------------------------------------------------------------
                 SECTION 3: THE PROCESS
                 ------------------------------------------------------------------ -->
            <section class="pres-section" id="section-process">
                <div class="process-layout">
                    <div>
                        <div class="pres-kicker">Methodology &amp; Double Diamond</div>
                        <h2 class="pres-title" style="font-size: clamp(2.5rem, 4.5vw, 4rem);">How this was designed</h2>
                    </div>

                    <!-- Caption Line Card -->
                    <div class="caption-card">
                        <span class="caption-icon">⚡</span>
                        <span class="caption-text">Breadth first, then depth. Dozens of concepts explored; one flow taken deep.</span>
                    </div>

                    <!-- Double Diamond Diagram Visual -->
                    <div class="diamond-diagram-container">
                        {double_diamond_svg}
                    </div>

                    <!-- 7 Phases Structured Breakdown -->
                    <div class="phases-grid">
                        <div class="phase-step-card">
                            <span class="phase-num">01 · DIVERGE</span>
                            <span class="phase-name">Sense intent</span>
                            <span class="phase-type">Deconstructing core objectives &amp; constraints</span>
                        </div>
                        <div class="phase-step-card">
                            <span class="phase-num">02 · RESEARCH</span>
                            <span class="phase-name">Know context</span>
                            <span class="phase-type">Disaster zones &amp; superhero dynamics</span>
                        </div>
                        <div class="phase-step-card">
                            <span class="phase-num">03 · EMPATHY</span>
                            <span class="phase-name">Know people</span>
                            <span class="phase-type">Physiological state during acute terror</span>
                        </div>
                        <div class="phase-step-card" style="border-color: rgba(168, 85, 247, 0.4); background: rgba(168, 85, 247, 0.05);">
                            <span class="phase-num" style="color: #c084fc;">04 · CONVERGE</span>
                            <span class="phase-name">Frame insights</span>
                            <span class="phase-type">The panic-first reframe pivot</span>
                        </div>
                        <div class="phase-step-card">
                            <span class="phase-num">05 · DIVERGE</span>
                            <span class="phase-name">Explore concepts</span>
                            <span class="phase-type">Voice vs button, triage vs instant dispatch</span>
                        </div>
                        <div class="phase-step-card">
                            <span class="phase-num">06 · ITERATE</span>
                            <span class="phase-name">Frame solution</span>
                            <span class="phase-type">Immediate SOS + progressive enrichment</span>
                        </div>
                        <div class="phase-step-card" style="border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.05);">
                            <span class="phase-num" style="color: #4ade80;">07 · CONVERGE</span>
                            <span class="phase-name">Realise offer</span>
                            <span class="phase-type">Harbor interactive prototype delivery</span>
                        </div>
                    </div>

                    <!-- Exact Mirrored Footer on Last Page -->
                    <footer class="pres-footer" style="padding-top: 2rem;">
                        <div>Vikhyat Kaushik · October 2026</div>
                        <div>
                            <a href="{prototype_url}" class="prototype-link" target="_blank" onclick="event.preventDefault(); togglePresentationMode(false);">Interactive prototype link ↗</a>
                        </div>
                    </footer>
                </div>
            </section>

        </main>
    </div>

    <!-- ==========================================================================
         SCRIPT: NAVIGATION, OVERLAYS & KEYBOARD SHORTCUT 'P'
         ========================================================================== -->
    <script>
        // Global toggle between Prototype and Presentation Mode
        let isPresentationMode = false;

        function togglePresentationMode(show) {{
            if (typeof show === 'boolean') {{
                isPresentationMode = show;
            }} else {{
                isPresentationMode = !isPresentationMode;
            }}

            const protoEl = document.getElementById('prototype-viewport');
            const presEl = document.getElementById('presentation-viewport');

            if (isPresentationMode) {{
                protoEl.style.display = 'none';
                presEl.style.display = 'block';
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }} else {{
                presEl.style.display = 'none';
                protoEl.style.display = 'flex';
            }}
        }}

        // Listen for keyboard press 'P' or 'p' to toggle presentation mode
        window.addEventListener('keydown', (e) => {{
            if (e.key === 'p' || e.key === 'P') {{
                // Ignore if user is currently typing in an input or textarea
                if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
                togglePresentationMode();
            }} else if (e.key === 'Escape' && isPresentationMode) {{
                togglePresentationMode(false);
            }}
        }});

        // Screen switching for Prototype
        document.addEventListener("DOMContentLoaded", () => {{
            function showScreen(id) {{
                document.querySelectorAll('#prototype-viewport .screen').forEach(s => s.style.display = 'none');
                const target = document.getElementById(id);
                if (target) {{
                    target.style.display = 'block';
                }}
            }}

            function createOverlay(screenId, left, top, width, height, targetId) {{
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
                overlay.onclick = () => {{
                    showScreen(targetId);
                    handleAutoTriggers(targetId);
                }};
                screen.appendChild(overlay);
            }}

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
            function handleAutoTriggers(screenId) {{
                clearTimeout(timeoutId);
                if (screenId === 'sending_alert') {{
                    timeoutId = setTimeout(() => showScreen('sos_active'), 2500);
                }} else if (screenId === 'sos_situation_worse') {{
                    timeoutId = setTimeout(() => showScreen('safe'), 3200);
                }}
            }}
        }});
    </script>
</body>
</html>'''

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Successfully built index.html with interactive prototype & scrolling high-end presentation deck!")

if __name__ == "__main__":
    build_all()
