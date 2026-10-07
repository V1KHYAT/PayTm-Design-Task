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

    with open("double_diamond_light.svg", "r", encoding="utf-8") as f:
        double_diamond_svg = f.read()

    prototype_url = "https://v1khyat.github.io/PayTm-Design-Task/"

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>Harbor · Superhero Emergency Alert App</title>
    <!-- Distinctive, Human Editorial Typography -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --canvas-bg: #faf9f5;
            --canvas-subtle: #f3f1ea;
            --ink-primary: #121316;
            --ink-secondary: #4a4c54;
            --ink-muted: #71747e;
            --signal-red: #dc2626;
            --signal-crimson: #991b1b;
            --border-rule: #e5e3db;
            --border-dark: #121316;
            --font-editorial: 'Instrument Serif', Georgia, serif;
            --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}

        body {{
            background: var(--canvas-bg);
            color: var(--ink-primary);
            font-family: var(--font-sans);
            overflow-x: hidden;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
        }}

        /* ==========================================================================
           MODE 1: INTERACTIVE MOBILE PROTOTYPE VIEWPORT
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
            container-type: size;
            user-select: none;
            box-shadow: 0 0 60px rgba(0, 0, 0, 0.9);
        }}

        .phone-wrapper * {{
            pointer-events: none;
        }}

        /* ==========================================================================
           MODE 2: LIGHT-MODE EDITORIAL PRESENTATION (No AI Slop)
           ========================================================================== */
        #presentation-viewport {{
            display: none;
            width: 100%;
            min-height: 100vh;
            background: var(--canvas-bg);
            position: relative;
            z-index: 200;
            overflow-y: auto;
        }}

        /* Architectural Top Bar */
        .pres-nav {{
            position: sticky;
            top: 0;
            width: 100%;
            padding: 1.25rem 3rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(250, 249, 245, 0.94);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-rule);
            z-index: 50;
        }}

        .pres-nav-brand {{
            display: flex;
            align-items: baseline;
            gap: 1.25rem;
        }}

        .pres-nav-title {{
            font-family: var(--font-editorial);
            font-size: 1.6rem;
            font-weight: 400;
            color: var(--ink-primary);
            letter-spacing: -0.01em;
            line-height: 1;
        }}

        .pres-nav-badge {{
            font-family: var(--font-mono);
            font-size: 0.72rem;
            font-weight: 500;
            color: var(--ink-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .btn-live-prototype {{
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            background: var(--ink-primary);
            color: #fff;
            border: 1px solid var(--ink-primary);
            padding: 0.6rem 1.25rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .btn-live-prototype:hover {{
            background: var(--signal-red);
            border-color: var(--signal-red);
            transform: translateY(-1px);
        }}

        .pulse-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #fff;
        }}

        /* Container Layout */
        .pres-container {{
            max-width: 1180px;
            margin: 0 auto;
            padding: 2rem 3rem 6rem;
        }}

        /* Section Anatomy */
        .pres-section {{
            min-height: calc(100vh - 100px);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 5rem 0 3.5rem;
            border-bottom: 1px solid var(--border-rule);
        }}

        .pres-section:last-of-type {{
            border-bottom: none;
        }}

        /* Kicker */
        .pres-kicker {{
            font-family: var(--font-mono);
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: var(--signal-red);
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .pres-kicker::before {{
            content: '';
            width: 16px;
            height: 1.5px;
            background: var(--signal-red);
        }}

        /* Display Headings */
        .pres-title {{
            font-family: var(--font-editorial);
            font-size: clamp(3.75rem, 7.5vw, 6.75rem);
            font-weight: 400;
            color: var(--ink-primary);
            letter-spacing: -0.02em;
            line-height: 0.98;
            margin-bottom: 1.75rem;
        }}

        .pres-subline {{
            font-size: clamp(1.2rem, 2vw, 1.65rem);
            font-weight: 400;
            color: var(--ink-secondary);
            line-height: 1.45;
            max-width: 720px;
            letter-spacing: -0.01em;
            margin-bottom: 3rem;
        }}

        /* Editorial Running Footers */
        .pres-footer {{
            padding-top: 3rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9rem;
            font-family: var(--font-mono);
            color: var(--ink-muted);
            border-top: 1px solid var(--border-rule);
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .pres-footer a.prototype-link {{
            color: var(--signal-red);
            text-decoration: underline;
            text-underline-offset: 4px;
            font-weight: 600;
            transition: color 0.15s ease;
        }}

        .pres-footer a.prototype-link:hover {{
            color: var(--signal-crimson);
        }}

        /* ==========================================================================
           SECTION 1: HERO (COVER)
           ========================================================================== */
        .hero-layout {{
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 4.5rem;
            align-items: center;
            width: 100%;
            margin: auto 0;
        }}

        .hero-left {{
            display: flex;
            flex-direction: column;
        }}

        .hero-meta-table {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            padding: 1.75rem 0;
            margin-bottom: 2.5rem;
            border-top: 1px solid var(--border-rule);
            border-bottom: 1px solid var(--border-rule);
        }}

        .hero-meta-col {{
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }}

        .hero-meta-label {{
            font-family: var(--font-mono);
            font-size: 0.7rem;
            color: var(--ink-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .hero-meta-value {{
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--ink-primary);
        }}

        /* Clean Architectural Mockup */
        .hero-mockup-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        .device-phone-chassis {{
            position: relative;
            width: 350px;
            height: calc(350px * (1844 / 852));
            background: #18191c;
            border-radius: 52px;
            padding: 10px;
            box-shadow: 
                0 25px 60px -15px rgba(18, 19, 22, 0.18),
                0 0 0 1px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease;
        }}

        .device-phone-chassis:hover {{
            transform: translateY(-4px);
        }}

        .device-screen-bezel {{
            position: relative;
            width: 100%;
            height: 100%;
            aspect-ratio: 852 / 1844;
            border-radius: 42px;
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
           SECTION 2: THE BRIEF
           ========================================================================== */
        .brief-content {{
            display: flex;
            flex-direction: column;
            gap: 3.5rem;
            width: 100%;
            margin: auto 0;
        }}

        /* The 2-Column Comparison Table */
        .editorial-matrix {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            border-top: 1.5px solid var(--border-dark);
            width: 100%;
        }}

        .matrix-col {{
            display: flex;
            flex-direction: column;
        }}

        .matrix-col:first-child {{
            border-right: 1px solid var(--border-rule);
            padding-right: 3rem;
        }}

        .matrix-col:last-child {{
            padding-left: 3rem;
        }}

        .matrix-header {{
            padding: 1.5rem 0 1.25rem;
            font-family: var(--font-mono);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--ink-muted);
            border-bottom: 1px solid var(--border-rule);
        }}

        .matrix-header.highlight-header {{
            color: var(--signal-red);
        }}

        .matrix-row {{
            padding: 1.75rem 0;
            border-bottom: 1px solid var(--border-rule);
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }}

        .matrix-num {{
            font-family: var(--font-mono);
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--ink-muted);
            letter-spacing: 0.08em;
        }}

        .matrix-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--ink-primary);
            line-height: 1.3;
        }}

        .matrix-desc {{
            font-size: 0.95rem;
            color: var(--ink-secondary);
            line-height: 1.55;
        }}

        /* Central Reframe (Greatest Visual Weight) */
        .reframe-spotlight {{
            padding: 3rem 0;
            border-top: 2px solid var(--border-dark);
            border-bottom: 2px solid var(--border-dark);
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}

        .reframe-tag {{
            font-family: var(--font-mono);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: var(--signal-red);
        }}

        .reframe-statement {{
            font-family: var(--font-editorial);
            font-size: clamp(2.25rem, 4.2vw, 3.6rem);
            font-weight: 400;
            color: var(--ink-primary);
            line-height: 1.15;
            letter-spacing: -0.015em;
        }}

        .reframe-statement strong {{
            font-weight: 400;
            color: var(--signal-red);
            font-style: italic;
        }}

        .reframe-secondary {{
            font-size: 1.25rem;
            font-weight: 500;
            color: var(--ink-secondary);
            line-height: 1.5;
            max-width: 820px;
        }}

        /* ==========================================================================
           SECTION 3: THE PROCESS
           ========================================================================== */
        .process-content {{
            display: flex;
            flex-direction: column;
            gap: 3.5rem;
            width: 100%;
            margin: auto 0;
        }}

        .caption-banner {{
            display: flex;
            align-items: baseline;
            gap: 1rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-rule);
        }}

        .caption-tag {{
            font-family: var(--font-mono);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--signal-red);
            flex-shrink: 0;
        }}

        .caption-sentence {{
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--ink-primary);
            letter-spacing: -0.01em;
            line-height: 1.4;
        }}

        .diagram-art-frame {{
            padding: 2.5rem 1.5rem;
            background: #fff;
            border: 1px solid var(--border-rule);
            border-radius: 12px;
        }}

        /* 7 Phases Editorial Table */
        .phases-row {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            border-top: 1px solid var(--border-rule);
            border-bottom: 1px solid var(--border-rule);
            width: 100%;
        }}

        .phase-col {{
            padding: 1.25rem 0.85rem;
            border-right: 1px solid var(--border-rule);
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }}

        .phase-col:last-child {{
            border-right: none;
        }}

        .phase-idx {{
            font-family: var(--font-mono);
            font-size: 0.7rem;
            font-weight: 700;
            color: var(--ink-muted);
        }}

        .phase-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--ink-primary);
            line-height: 1.25;
        }}

        .phase-meta {{
            font-size: 0.75rem;
            color: var(--ink-secondary);
            line-height: 1.4;
        }}

        /* Print / PDF Styles */
        @media print {{
            body, html {{
                background: #fff !important;
                color: #000 !important;
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
                box-shadow: 0 0 0 1px #ccc !important;
            }}
        }}

        /* Responsive Breakpoints */
        @media (max-width: 1024px) {{
            .hero-layout {{
                grid-template-columns: 1fr;
                gap: 3rem;
            }}
            .editorial-matrix {{
                grid-template-columns: 1fr;
            }}
            .matrix-col:first-child {{
                border-right: none;
                border-bottom: 1px solid var(--border-rule);
                padding-right: 0;
                padding-bottom: 2rem;
            }}
            .matrix-col:last-child {{
                padding-left: 0;
                padding-top: 2rem;
            }}
            .phases-row {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .phase-col:nth-child(2n) {{
                border-right: none;
            }}
            .pres-section {{
                min-height: auto;
                padding: 4rem 0;
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
         MODE 2: LIGHT-MODE EDITORIAL PRESENTATION WEBSITE
         ========================================================================== -->
    <div id="presentation-viewport">

        <!-- Top Navigation -->
        <header class="pres-nav">
            <div class="pres-nav-brand">
                <span class="pres-nav-title">Harbor</span>
                <span class="pres-nav-badge">Paytm Design Internship 2027 · Design Task</span>
            </div>
            <button class="btn-live-prototype" onclick="togglePresentationMode(false)">
                <span class="pulse-dot"></span>
                <span>Switch to Interactive Prototype</span>
            </button>
        </header>

        <main class="pres-container">

            <!-- ------------------------------------------------------------------
                 SECTION 1: COVER
                 ------------------------------------------------------------------ -->
            <section class="pres-section" id="section-cover">
                <div>
                    <div class="pres-kicker">Paytm Design Internship 2027 · Design Task</div>
                </div>

                <div class="hero-layout">
                    <div class="hero-left">
                        <h1 class="pres-title">Harbor</h1>
                        <p class="pres-subline">A superhero emergency alert app. One tap, and the right help is moving.</p>

                        <div class="hero-meta-table">
                            <div class="hero-meta-col">
                                <span class="hero-meta-label">Primary Trigger</span>
                                <span class="hero-meta-value">Single Tap SOS</span>
                            </div>
                            <div class="hero-meta-col">
                                <span class="hero-meta-label">Product Stance</span>
                                <span class="hero-meta-value">Panic-First Sensory</span>
                            </div>
                            <div class="hero-meta-col">
                                <span class="hero-meta-label">Lifecycle</span>
                                <span class="hero-meta-value">5 Verified States</span>
                            </div>
                        </div>

                        <div>
                            <button class="btn-live-prototype" onclick="togglePresentationMode(false)" style="padding: 0.8rem 1.6rem; font-size: 0.95rem;">
                                <span>Launch Interactive Prototype ↗</span>
                            </button>
                        </div>
                    </div>

                    <!-- Visual: Large Home Screen Mockup -->
                    <div class="hero-mockup-wrapper">
                        <div class="device-phone-chassis">
                            <div class="device-screen-bezel">
                                <div style="width: 100%; height: 100%; position: relative; background: rgb(250, 249, 247);">
                                    {home_screen_inner}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer: First place reviewer sees the link -->
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
                <div>
                    <div class="pres-kicker">Objective &amp; Problem Reframe</div>
                    <h2 class="pres-title" style="font-size: clamp(3rem, 5.5vw, 5rem); margin-bottom: 0;">The brief</h2>
                </div>

                <div class="brief-content">
                    <!-- Visual: The "asked vs really testing" two-column -->
                    <div class="editorial-matrix">

                        <!-- Left Column: The 3 deliverables as written -->
                        <div class="matrix-col">
                            <div class="matrix-header">The Deliverables (As Written)</div>

                            <div class="matrix-row">
                                <span class="matrix-num">01 / DISPATCH &amp; LIFECYCLE</span>
                                <h3 class="matrix-title">Reach superheroes fast &amp; track request lifecycle</h3>
                                <p class="matrix-desc">Reach heroes fast; track full request stages: raised, verified, assigned, responded, resolved.</p>
                            </div>

                            <div class="matrix-row">
                                <span class="matrix-num">02 / EDGE CASE</span>
                                <h3 class="matrix-title">Include one critical edge case</h3>
                                <p class="matrix-desc">Identify an unpredictable crisis condition (e.g. escalating threat severity) and design resilient system handling.</p>
                            </div>

                            <div class="matrix-row">
                                <span class="matrix-num">03 / ARTIFACTS</span>
                                <h3 class="matrix-title">Deliver interactive prototype link + PDF</h3>
                                <p class="matrix-desc">Deliver a functional interactive prototype link accompanied by a PDF document detailing user flow, design decisions, and assumptions.</p>
                            </div>
                        </div>

                        <!-- Right Column: What each one is really testing -->
                        <div class="matrix-col">
                            <div class="matrix-header highlight-header">What Each One Is Really Testing</div>

                            <div class="matrix-row">
                                <span class="matrix-num" style="color: var(--signal-red);">EVALUATING STRESS UX</span>
                                <h3 class="matrix-title">Designing for panic</h3>
                                <p class="matrix-desc">Under mortal threat, cognitive load drops to zero and motor control degrades. Shaking hands cannot navigate forms. Speed must precede triage.</p>
                            </div>

                            <div class="matrix-row">
                                <span class="matrix-num" style="color: var(--signal-red);">EVALUATING SYSTEM TRANSPARENCY</span>
                                <h3 class="matrix-title">Legible dispatch</h3>
                                <p class="matrix-desc">Clear hero tier assignment, live distance ETA, and sensory certainty without information overload or panic-inducing ambiguity.</p>
                            </div>

                            <div class="matrix-row">
                                <span class="matrix-num" style="color: var(--signal-red);">EVALUATING PSYCHOLOGICAL SAFETY</span>
                                <h3 class="matrix-title">Calm while waiting</h3>
                                <p class="matrix-desc">The most vulnerable moments are during transit. The interface must provide protective stealth, discreet reporting, and actionable reassurance.</p>
                            </div>
                        </div>

                    </div>

                    <!-- Reframe Line: Greatest Weight on the Page -->
                    <div class="reframe-spotlight">
                        <div class="reframe-tag">The Reframe</div>
                        <h3 class="reframe-statement">
                            This is not a dispatch dashboard. It is a <strong>panic-first product</strong>.
                        </h3>
                        <p class="reframe-secondary">
                            Design for shaking hands, then earn trust while they wait.
                        </p>
                    </div>
                </div>

                <!-- Footer -->
                <footer class="pres-footer">
                    <div>Vikhyat Kaushik · October 2026</div>
                    <div>
                        <a href="{prototype_url}" class="prototype-link" target="_blank" onclick="event.preventDefault(); togglePresentationMode(false);">Interactive prototype link ↗</a>
                    </div>
                </footer>
            </section>


            <!-- ------------------------------------------------------------------
                 SECTION 3: THE PROCESS
                 ------------------------------------------------------------------ -->
            <section class="pres-section" id="section-process">
                <div>
                    <div class="pres-kicker">Design Methodology</div>
                    <h2 class="pres-title" style="font-size: clamp(3rem, 5.5vw, 5rem); margin-bottom: 0;">How this was designed</h2>
                </div>

                <div class="process-content">
                    <!-- Caption Line -->
                    <div class="caption-banner">
                        <span class="caption-tag">Guiding Principle</span>
                        <p class="caption-sentence">Breadth first, then depth. Dozens of concepts explored; one flow taken deep.</p>
                    </div>

                    <!-- Double Diamond Diagram Visual -->
                    <div class="diagram-art-frame">
                        {double_diamond_svg}
                    </div>

                    <!-- 7 Phases Row -->
                    <div class="phases-row">
                        <div class="phase-col">
                            <span class="phase-idx">01 · DIVERGE</span>
                            <h4 class="phase-title">Sense intent</h4>
                            <p class="phase-meta">Deconstructing prompt objectives</p>
                        </div>
                        <div class="phase-col">
                            <span class="phase-idx">02 · RESEARCH</span>
                            <h4 class="phase-title">Know context</h4>
                            <p class="phase-meta">Disaster realities &amp; hero tiers</p>
                        </div>
                        <div class="phase-col">
                            <span class="phase-idx">03 · EMPATHY</span>
                            <h4 class="phase-title">Know people</h4>
                            <p class="phase-meta">Physiology of terrified victims</p>
                        </div>
                        <div class="phase-col" style="background: var(--canvas-subtle);">
                            <span class="phase-idx" style="color: var(--signal-red);">04 · CONVERGE</span>
                            <h4 class="phase-title">Frame insights</h4>
                            <p class="phase-meta">The panic-first product pivot</p>
                        </div>
                        <div class="phase-col">
                            <span class="phase-idx">05 · DIVERGE</span>
                            <h4 class="phase-title">Explore concepts</h4>
                            <p class="phase-meta">Forms vs one-tap dispatch</p>
                        </div>
                        <div class="phase-col">
                            <span class="phase-idx">06 · ITERATE</span>
                            <h4 class="phase-title">Frame solution</h4>
                            <p class="phase-meta">Immediate alert + progressive details</p>
                        </div>
                        <div class="phase-col" style="background: #fef2f2;">
                            <span class="phase-idx" style="color: var(--signal-red);">07 · CONVERGE</span>
                            <h4 class="phase-title">Realise offer</h4>
                            <p class="phase-meta">Harbor interactive delivery</p>
                        </div>
                    </div>
                </div>

                <!-- Footer: Mirrored on the last page -->
                <footer class="pres-footer">
                    <div>Vikhyat Kaushik · October 2026</div>
                    <div>
                        <a href="{prototype_url}" class="prototype-link" target="_blank" onclick="event.preventDefault(); togglePresentationMode(false);">Interactive prototype link ↗</a>
                    </div>
                </footer>
            </section>

        </main>
    </div>

    <!-- ==========================================================================
         SCRIPT: NAVIGATION, OVERLAYS & KEYBOARD SHORTCUT 'P'
         ========================================================================== -->
    <script>
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
                if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
                togglePresentationMode();
            }} else if (e.key === 'Escape' && isPresentationMode) {{
                togglePresentationMode(false);
            }}
        }});

        // Prototype Overlay Routing
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

    print("Successfully built impeccable light-mode presentation & prototype!")

if __name__ == "__main__":
    build_all()
