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
        # Unified Countdown Ring on sending_alert screen
        if node.get("id") == "21:3533":
            svg_tag = f'''<svg id="countdown-svg" viewBox="0 0 680 690" style="position:absolute; left:{left:.3f}%; top:{top:.3f}%; width:{width:.3f}%; height:{height:.3f}%; pointer-events:none; overflow:visible;" fill="none">
    <path d="M340 20C516.457 20 660 165.231 660 345C660 524.769 516.457 670 340 670C163.543 670 20 524.769 20 345C20 165.231 163.543 20 340 20Z" stroke="#EBE9E6" stroke-width="40"/>
    <path id="countdown-progress-ring" pathLength="100" d="M340 20C516.457 20 660 165.231 660 345C660 524.769 516.457 670 340 670C163.543 670 20 524.769 20 345C20 165.231 163.543 20 340 20Z" stroke="#D83B30" stroke-width="40" stroke-linecap="round" stroke-dasharray="100" stroke-dashoffset="0"/>
</svg>'''
            out_list.append(svg_tag)
            return

        if node.get("id") == "21:3534":
            # Skip separate countdown progress vector since it is now rendered directly inside countdown-svg!
            return

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

        extra_attr = ""
        if node.get("id") == "21:3535" or node.get("name") == "Seconds remaining":
            extra_attr = ' id="countdown-seconds"'
            chars = "3"

        css = f"position:absolute; {pos_css} {wrap_css} height:max-content; font-size:{font_size:.3f}cqh; font-weight:{font_weight}; color:{color}; line-height:{lh_ratio:.3f}; display:flex; flex-direction:column; overflow:visible;"

        out_list.append(f"<div{extra_attr} style='{css}'><span>{chars}</span></div>")
        return

    # Bento response cards inside sos_active (21:3541)
    if node.get("id") in ["21:3553", "21:3559", "21:3565"]:
        card_num = "1" if node["id"] == "21:3553" else ("2" if node["id"] == "21:3559" else "3")
        if card_num == "1":
            tips_html = '''<div id="bento-tips-container" style="position:absolute; left:7.277%; top:15.500%; width:85.446%; height:38.500%; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; pointer-events:none; z-index:5; transition:opacity 0.4s ease, transform 0.4s ease;">
    <div style="display:inline-flex; align-items:center; gap:0.8cqh; background:rgba(34,197,94,0.14); border:1px solid rgba(34,197,94,0.32); border-radius:999px; padding:0.5cqh 1.6cqh; margin-bottom:2cqh;">
        <span class="live-ping-dot" style="width:0.8cqh; height:0.8cqh; border-radius:50%; background:#22c55e;"></span>
        <span style="font-size:1.15cqh; font-weight:700; color:#86efac; letter-spacing:0.08em; text-transform:uppercase;">Broadcasting SOS · Seeking Heroes</span>
    </div>
    <div class="calm-breath-orb" style="width:7.5cqh; height:7.5cqh; border-radius:50%; background:radial-gradient(circle, rgba(52,211,153,0.3) 0%, rgba(16,185,129,0.06) 70%, transparent 100%); border:1.5px solid rgba(52,211,153,0.45); display:flex; align-items:center; justify-content:center; margin-bottom:2.2cqh;">
        <div style="width:2.8cqh; height:2.8cqh; border-radius:50%; background:#34d399; opacity:0.9;"></div>
    </div>
    <div id="bento-tip-text-box" style="display:flex; flex-direction:column; align-items:center; gap:0.7cqh; max-width:85%; transition:opacity 0.3s ease;">
        <div id="bento-tip-title" style="font-size:1.95cqh; font-weight:700; color:#f3f4f6; line-height:1.3; text-wrap:balance;">Breathe in a 1-2 Pattern to remain calm.</div>
        <div id="bento-tip-subtitle" style="font-size:1.3cqh; font-weight:400; color:#9ca3af; line-height:1.35;">Inhale 4s · Exhale 8s to steady your heart rate</div>
    </div>
</div>'''
            out_list.append(tips_html)

        sub_list = []
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
            sub_list.append(f"<div style='{' '.join(css_parts)}'></div>")

        for child in node.get("children", []):
            collect_html(child, frame_x, frame_y, frame_w, frame_h, sub_list)

        inner_card = "\n".join(sub_list)
        out_list.append(f'<div id="update-card-{card_num}" class="update-card" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none;">\n{inner_card}\n</div>')
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
        let countdownAnimId = null;

        function startCountdown() {
            if (countdownAnimId) {
                cancelAnimationFrame(countdownAnimId);
                countdownAnimId = null;
            }

            const ring = document.getElementById('countdown-progress-ring');
            const secondsEl = document.getElementById('countdown-seconds');
            if (!ring || !secondsEl) return;

            ring.style.strokeDashoffset = '0';
            secondsEl.innerHTML = '<span>3</span>';

            const duration = 3000;
            const startTime = performance.now();

            function tick(now) {
                const elapsed = now - startTime;
                const progress = Math.min(1, elapsed / duration);

                // Smoothly drain the stroke from full (0) to empty (100)
                ring.style.strokeDashoffset = (progress * 100).toFixed(2);

                // Countdown numbers: 3 -> 2 -> 1
                const remaining = Math.max(1, Math.ceil(3 - (elapsed / 1000)));
                secondsEl.innerHTML = `<span>${remaining}</span>`;

                if (progress < 1) {
                    countdownAnimId = requestAnimationFrame(tick);
                } else {
                    countdownAnimId = null;
                    showScreen('sos_active');
                    handleAutoTriggers('sos_active');
                }
            }

            countdownAnimId = requestAnimationFrame(tick);
        }

        function stopCountdown() {
            if (countdownAnimId) {
                cancelAnimationFrame(countdownAnimId);
                countdownAnimId = null;
            }
            const ring = document.getElementById('countdown-progress-ring');
            const secondsEl = document.getElementById('countdown-seconds');
            if (ring) ring.style.strokeDashoffset = '0';
            if (secondsEl) secondsEl.innerHTML = '<span>3</span>';
        }

        let sosTimeouts = [];

        function clearSosActiveUpdates() {
            sosTimeouts.forEach(t => clearTimeout(t));
            sosTimeouts = [];

            const tipsEl = document.getElementById('bento-tips-container');
            if (tipsEl) {
                tipsEl.style.opacity = '1';
                tipsEl.style.transform = 'translateY(0)';
            }
            const textBox = document.getElementById('bento-tip-text-box');
            if (textBox) {
                textBox.style.opacity = '1';
            }
            const tipTitle = document.getElementById('bento-tip-title');
            const tipSub = document.getElementById('bento-tip-subtitle');
            if (tipTitle) tipTitle.textContent = "Breathe in a 1-2 Pattern to remain calm.";
            if (tipSub) tipSub.textContent = "Inhale 4s · Exhale 8s to steady your heart rate";

            for (let i = 1; i <= 3; i++) {
                const card = document.getElementById(`update-card-${i}`);
                if (card) {
                    card.classList.remove('visible');
                }
            }
        }

        function startSosActiveUpdates() {
            clearSosActiveUpdates();

            const tipsEl = document.getElementById('bento-tips-container');
            const textBox = document.getElementById('bento-tip-text-box');
            const tipTitle = document.getElementById('bento-tip-title');
            const tipSub = document.getElementById('bento-tip-subtitle');

            const card1 = document.getElementById('update-card-1');
            const card2 = document.getElementById('update-card-2');
            const card3 = document.getElementById('update-card-3');

            // Switch to Tip 2 after 1.8s
            sosTimeouts.push(setTimeout(() => {
                if (textBox && tipTitle && tipSub) {
                    textBox.style.opacity = '0';
                    setTimeout(() => {
                        tipTitle.textContent = "Stay low and keep your device silent.";
                        tipSub.textContent = "Live audio & coordinates streaming to dispatch";
                        textBox.style.opacity = '1';
                    }, 250);
                }
            }, 1800));

            // Fade out tips container & slide in Card 1 at ~3.6s
            sosTimeouts.push(setTimeout(() => {
                if (tipsEl) {
                    tipsEl.style.opacity = '0';
                    tipsEl.style.transform = 'translateY(-1cqh)';
                }
                if (card1) card1.classList.add('visible');
            }, 3600));

            // Slide in Card 2 at ~5.6s (2.0s after Card 1)
            sosTimeouts.push(setTimeout(() => {
                if (card2) card2.classList.add('visible');
            }, 5600));

            // Slide in Card 3 at ~7.6s (2.0s after Card 2)
            sosTimeouts.push(setTimeout(() => {
                if (card3) card3.classList.add('visible');
            }, 7600));
        }

        function showScreen(id) {
            document.querySelectorAll('.screen').forEach(s => s.style.display = 'none');
            const target = document.getElementById(id);
            if (target) {
                target.style.display = 'block';
            }

            if (id === 'sending_alert') {
                startCountdown();
            } else {
                stopCountdown();
            }

            if (id === 'sos_active') {
                startSosActiveUpdates();
            } else {
                clearSosActiveUpdates();
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

        let worseTimeoutId;
        function handleAutoTriggers(screenId) {
            clearTimeout(worseTimeoutId);
            if (screenId === 'sos_situation_worse') {
                worseTimeoutId = setTimeout(() => showScreen('safe'), 3200);
            }
        }

        clearSosActiveUpdates();
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

        /* Sequential responder cards animation */
        .update-card {{
            opacity: 0;
            transform: translateY(1.8cqh);
            transition: opacity 0.55s cubic-bezier(0.16, 1, 0.3, 1), transform 0.55s cubic-bezier(0.16, 1, 0.3, 1);
            pointer-events: none;
        }}
        .update-card.visible {{
            opacity: 1;
            transform: translateY(0);
        }}

        /* Calming breathing orb animation */
        @keyframes calmBreath {{
            0%, 100% {{
                transform: scale(0.92);
                opacity: 0.75;
                box-shadow: 0 0 14px rgba(52, 211, 153, 0.2);
            }}
            50% {{
                transform: scale(1.15);
                opacity: 1;
                box-shadow: 0 0 30px rgba(52, 211, 153, 0.5);
            }}
        }}
        .calm-breath-orb {{
            animation: calmBreath 4s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }}

        /* Live dispatch beacon ping animation */
        @keyframes livePing {{
            0%, 100% {{
                opacity: 1;
                transform: scale(1);
            }}
            50% {{
                opacity: 0.35;
                transform: scale(0.8);
            }}
        }}
        .live-ping-dot {{
            animation: livePing 1.8s ease-in-out infinite;
        }}

        @media (prefers-reduced-motion: reduce) {{
            .update-card {{
                transition: opacity 0.2s ease;
                transform: none !important;
            }}
            .calm-breath-orb, .live-ping-dot {{
                animation: none !important;
            }}
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
