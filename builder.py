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
            weight_cqh = (weight / 1844.0) * 100
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

    # Step 1 progress bar track & fill
    if node.get("id") == "21:3596":
        tag = f'''<div id="progress-bar-step1-track" style="position:absolute; left:{left:.3f}%; top:{top:.3f}%; width:{width:.3f}%; height:{height:.3f}%; background:rgb(24,28,30); border-radius:999px; overflow:hidden; pointer-events:none;">
    <div id="progress-bar-step1-fill" style="width:50%; height:100%; background:#fff; border-radius:999px; transition:width 0.35s cubic-bezier(0.16,1,0.3,1);"></div>
</div>'''
        out_list.append(tag)
        return

    if node.get("id") == "21:3597":
        # Skip static rectangle as it's now dynamically animated inside progress-bar-step1-track
        return

    # Step 2 progress bar track & fill
    if node.get("id") == "21:3674":
        tag = f'''<div id="progress-bar-step2-track" style="position:absolute; left:{left:.3f}%; top:{top:.3f}%; width:{width:.3f}%; height:{height:.3f}%; background:rgb(24,28,30); border-radius:999px; overflow:hidden; pointer-events:none;">
    <div id="progress-bar-step2-fill" style="width:75%; height:100%; background:#fff; border-radius:999px; transition:width 0.4s cubic-bezier(0.16,1,0.3,1), background-color 0.3s ease;"></div>
</div>'''
        out_list.append(tag)
        return

    if node.get("id") == "21:3675":
        # Skip static rectangle as it's now dynamically animated inside progress-bar-step2-track
        return

    # Medical team route map box on safe screen (21:3806) - Clip map vectors inside the container
    if node.get("id") == "21:3837":
        radius = node.get("cornerRadius", 28.0)
        radius_cqh = (radius / 1844.0) * 100
        sub_list = []
        for child in node.get("children", []):
            collect_html(child, bounds["x"], bounds["y"], bounds["width"], bounds["height"], sub_list)
        inner_map = "\n".join(sub_list)
        out_list.append(f'''<div id="medical-team-route-box" style="position:absolute; left:{left:.3f}%; top:{top:.3f}%; width:{width:.3f}%; height:{height:.3f}%; background:#f5f4f0; border-radius:{radius_cqh:.3f}cqh; overflow:hidden; pointer-events:none;">\n{inner_map}\n</div>''')
        return

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
        font_size = (font_size_px / 1844.0) * 100
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
            tips_html = '''<div id="bento-tips-container" style="position:absolute; left:7.277%; top:15.500%; width:85.446%; height:38.500%; display:flex; justify-content:center; align-items:center; text-align:center; pointer-events:none; z-index:5; transition:opacity 0.4s ease, transform 0.4s ease;">
    <div id="bento-tip-text" style="font-size:1.6cqh; font-weight:500; color:#9ca3af; line-height:1.45; max-width:82%; text-wrap:balance; transition:opacity 0.3s ease;">
        Breathe in a 1-2 Pattern to remain calm.
    </div>
</div>'''
            out_list.append(tips_html)

        sub_list = []
        bg = get_fill_css(node)
        stroke_css = get_stroke_css(node, frame_h)
        radius = node.get("cornerRadius", 0)
        radius_cqh = (radius / 1844.0) * 100
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

    # Bento response cards inside sos_situation_worse (21:3754)
    if node.get("id") in ["21:3766", "21:3772", "21:3779", "21:3784"]:
        card_num = "1" if node["id"] == "21:3766" else ("2" if node["id"] == "21:3772" else ("3" if node["id"] == "21:3779" else "4"))
        if card_num == "1":
            worse_msg_html = '''<div id="worse-message-container" style="position:absolute; left:6.808%; top:13.341%; width:86.385%; height:45.336%; display:flex; justify-content:center; align-items:center; text-align:center; pointer-events:none; z-index:5; transition:opacity 0.4s ease, transform 0.4s ease;">
    <div id="worse-message-text" style="font-size:1.6cqh; font-weight:500; color:#9ca3af; line-height:1.45; max-width:82%; text-wrap:balance;">
        Senior Heroes are on their way.
    </div>
</div>'''
            out_list.append(worse_msg_html)

        sub_list = []
        bg = get_fill_css(node)
        stroke_css = get_stroke_css(node, frame_h)
        radius = node.get("cornerRadius", 0)
        radius_cqh = (radius / 1844.0) * 100
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
        out_list.append(f'<div id="worse-card-{card_num}" class="update-card worse-card" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none;">\n{inner_card}\n</div>')
        return

    # Frame / Rectangle
    if node["type"] not in ["DOCUMENT", "CANVAS"]:
        bg = get_fill_css(node)
        stroke_css = get_stroke_css(node, frame_h)
        radius = node.get("cornerRadius", 0)
        radius_cqh = (radius / 1844.0) * 100

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

        active_cls = " active" if first else ""
        first = False

        screen_html = f"""
        <div id="{screen_name}" class="screen{active_cls}" style="width:100%; height:100%; position:absolute; top:0; left:0; background:{bg};">
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
            const tipText = document.getElementById('bento-tip-text');
            if (tipText) {
                tipText.style.opacity = '1';
                tipText.textContent = "Breathe in a 1-2 Pattern to remain calm.";
            }

            for (let i = 1; i <= 3; i++) {
                const card = document.getElementById(`update-card-${i}`);
                if (card) {
                    card.classList.remove('visible');
                }
            }
        }

        function setSosActiveCardsImmediately() {
            clearSosActiveUpdates();
            const tipsEl = document.getElementById('bento-tips-container');
            if (tipsEl) {
                tipsEl.style.opacity = '0';
                tipsEl.style.pointerEvents = 'none';
            }
            for (let i = 1; i <= 3; i++) {
                const card = document.getElementById(`update-card-${i}`);
                if (card) {
                    card.classList.add('visible');
                }
            }
        }

        function startSosActiveUpdates() {
            clearSosActiveUpdates();

            const tipsEl = document.getElementById('bento-tips-container');
            const tipText = document.getElementById('bento-tip-text');

            const card1 = document.getElementById('update-card-1');
            const card2 = document.getElementById('update-card-2');
            const card3 = document.getElementById('update-card-3');

            // Switch to Tip 2 after 1.8s
            sosTimeouts.push(setTimeout(() => {
                if (tipText) {
                    tipText.style.opacity = '0';
                    setTimeout(() => {
                        tipText.textContent = "Stay in safe cover and keep the line open.";
                        tipText.style.opacity = '1';
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

        let worseTimeouts = [];

        function clearWorseUpdates() {
            worseTimeouts.forEach(t => clearTimeout(t));
            worseTimeouts = [];

            const msgEl = document.getElementById('worse-message-container');
            if (msgEl) {
                msgEl.style.opacity = '1';
                msgEl.style.transform = 'translateY(0)';
            }

            for (let i = 1; i <= 4; i++) {
                const card = document.getElementById(`worse-card-${i}`);
                if (card) {
                    card.classList.remove('visible');
                }
            }
        }

        function startWorseUpdates() {
            clearWorseUpdates();

            const msgEl = document.getElementById('worse-message-container');
            const card1 = document.getElementById('worse-card-1');
            const card2 = document.getElementById('worse-card-2');
            const card3 = document.getElementById('worse-card-3');
            const card4 = document.getElementById('worse-card-4');

            // Senior Heroes message initially displayed
            // At ~2.0s: fade out message & slide in Card 1
            worseTimeouts.push(setTimeout(() => {
                if (msgEl) {
                    msgEl.style.opacity = '0';
                    msgEl.style.transform = 'translateY(-1cqh)';
                }
                if (card1) card1.classList.add('visible');
            }, 2000));

            // At ~3.8s: slide in Card 2
            worseTimeouts.push(setTimeout(() => {
                if (card2) card2.classList.add('visible');
            }, 3800));

            // At ~5.6s: slide in Card 3 (Tatsumaki)
            worseTimeouts.push(setTimeout(() => {
                if (card3) card3.classList.add('visible');
            }, 5600));

            // At ~7.4s: slide in Card 4 (Genos updated)
            worseTimeouts.push(setTimeout(() => {
                if (card4) card4.classList.add('visible');
            }, 7400));

            // Wait longer (~14s total) before smoothly transitioning to You're Safe screen
            worseTimeouts.push(setTimeout(() => {
                showScreen('safe');
            }, 14000));
        }

        function showScreen(id, options = {}) {
            document.querySelectorAll('.screen').forEach(s => {
                if (s.id !== id) {
                    s.classList.remove('active');
                }
            });

            const target = document.getElementById(id);
            if (target) {
                target.classList.add('active');
            }

            if (id === 'sending_alert') {
                startCountdown();
            } else {
                stopCountdown();
            }

            if (id === 'sos_active') {
                if (options.cardsReady) {
                    setSosActiveCardsImmediately();
                } else {
                    startSosActiveUpdates();
                }
            } else {
                clearSosActiveUpdates();
            }

            if (id === 'sos_situation_worse') {
                startWorseUpdates();
            } else {
                clearWorseUpdates();
            }
        }

        // Interactive selectable item creation helper
        function createSelectable({ screenId, left, top, width, height, radius = '1.5cqh', group = null, selected = false, onClick = null }) {
            const screen = document.getElementById(screenId);
            if (!screen) return null;
            const el = document.createElement('div');
            el.className = 'selectable-item' + (selected ? ' selected' : '');
            if (group) el.setAttribute('data-group', group);
            el.style.position = 'absolute';
            el.style.left = left + '%';
            el.style.top = top + '%';
            el.style.width = width + '%';
            el.style.height = height + '%';
            el.style.borderRadius = radius;
            el.style.zIndex = '9999';

            el.onclick = (e) => {
                e.stopPropagation();
                if (group) {
                    screen.querySelectorAll(`[data-group="${group}"]`).forEach(item => item.classList.remove('selected'));
                    el.classList.add('selected');
                } else {
                    el.classList.toggle('selected');
                }
                if (onClick) onClick(el);
            };

            screen.appendChild(el);
            return el;
        }

        // Interactive button helper
        function createButton({ screenId, left, top, width, height, radius = '1.5cqh', onClick }) {
            const screen = document.getElementById(screenId);
            if (!screen) return null;
            const el = document.createElement('div');
            el.className = 'interactive-btn';
            el.style.position = 'absolute';
            el.style.left = left + '%';
            el.style.top = top + '%';
            el.style.width = width + '%';
            el.style.height = height + '%';
            el.style.borderRadius = radius;
            el.style.zIndex = '9999';
            el.onclick = (e) => {
                e.stopPropagation();
                if (onClick) onClick(el);
            };
            screen.appendChild(el);
            return el;
        }

        // ==========================================
        // SCREEN INTERACTIONS & CONTROLS
        // ==========================================

        // 1. Home screen -> SOS button
        createButton({
            screenId: 'home',
            left: 4.5, top: 58.5, width: 91.0, height: 33.3, radius: '3cqh',
            onClick: () => showScreen('sending_alert')
        });

        // 2. Sending alert -> Cancel button
        createButton({
            screenId: 'sending_alert',
            left: 4.5, top: 82.1, width: 91.0, height: 9.8, radius: '2cqh',
            onClick: () => showScreen('home')
        });

        // 3. SOS Active screen
        // Vibrate toggle
        createSelectable({
            screenId: 'sos_active',
            left: 85.0, top: 8.5, width: 8.5, height: 4.5, radius: '50%', selected: true
        });

        // Better button
        createSelectable({
            screenId: 'sos_active',
            left: 4.577, top: 62.690, width: 44.014, height: 10.738, radius: '1.7cqh', group: 'sos_active_status'
        });

        // Worse button -> triggers Worse flow
        createButton({
            screenId: 'sos_active',
            left: 51.408, top: 62.690, width: 44.014, height: 10.738, radius: '1.7cqh',
            onClick: () => showScreen('sos_situation_worse')
        });

        // Cancel SOS button
        createButton({
            screenId: 'sos_active',
            left: 4.577, top: 74.946, width: 90.845, height: 7.484, radius: '2cqh',
            onClick: () => showScreen('home')
        });

        // Swipe up anywhere (bottom area) -> opens situation_category form
        createButton({
            screenId: 'sos_active',
            left: 0.0, top: 83.0, width: 100.0, height: 17.0,
            onClick: () => showScreen('situation_category')
        });

        // 4. Situation Category (Step 1 of 2)
        // Dismiss top area
        createButton({
            screenId: 'situation_category',
            left: 0.0, top: 0.0, width: 100.0, height: 7.0,
            onClick: () => showScreen('sos_active', { cardsReady: true })
        });

        // Category options (Fire or smoke + other 8 categories)
        // Fire or smoke option
        createSelectable({
            screenId: 'situation_category',
            left: 3.286, top: 25.108, width: 45.305, height: 11.714,
            radius: '1.735cqh', group: 'categories', selected: true,
            onClick: () => {
                const p1 = document.getElementById('progress-bar-step1-fill');
                if (p1) p1.style.width = '100%';
                setTimeout(() => showScreen('fire_details'), 280);
            }
        });

        const otherCategories = [
            { left: 51.408, top: 25.108, w: 45.305, h: 11.714 },
            { left: 3.286, top: 38.124, w: 45.305, h: 11.714 },
            { left: 51.408, top: 38.124, w: 45.305, h: 11.714 },
            { left: 3.286, top: 51.139, w: 45.305, h: 11.714 },
            { left: 51.408, top: 51.139, w: 45.305, h: 11.714 },
            { left: 3.286, top: 64.154, w: 45.305, h: 11.714 },
            { left: 51.408, top: 64.154, w: 45.305, h: 11.714 },
            { left: 3.286, top: 77.169, w: 93.427, h: 9.653 }
        ];
        otherCategories.forEach(pos => {
            createSelectable({
                screenId: 'situation_category',
                left: pos.left, top: pos.top, width: pos.w, height: pos.h,
                radius: '1.735cqh', group: 'categories',
                onClick: () => {
                    const p1 = document.getElementById('progress-bar-step1-fill');
                    if (p1) p1.style.width = '100%';
                    setTimeout(() => showScreen('fire_details'), 280);
                }
            });
        });

        // 5. Fire Details (Step 2 of 2)
        // Change category button
        createButton({
            screenId: 'fire_details',
            left: 76.878, top: 11.822, width: 15.141, height: 3.471, radius: '999px',
            onClick: () => {
                const p1 = document.getElementById('progress-bar-step1-fill');
                if (p1) p1.style.width = '50%';
                showScreen('situation_category');
            }
        });

        // Condition choices ("What do you see?")
        createSelectable({
            screenId: 'fire_details',
            left: 5.164, top: 26.952, width: 28.638, height: 11.280, radius: '1.518cqh', group: 'fire_visible', selected: true
        });
        createSelectable({
            screenId: 'fire_details',
            left: 36.150, top: 26.952, width: 28.169, height: 11.280, radius: '1.518cqh', group: 'fire_visible'
        });
        createSelectable({
            screenId: 'fire_details',
            left: 66.667, top: 26.952, width: 28.169, height: 11.280, radius: '1.518cqh', group: 'fire_visible'
        });

        // Occupancy choices ("Anyone inside?")
        createSelectable({
            screenId: 'fire_details',
            left: 5.164, top: 47.939, width: 28.326, height: 11.280, radius: '1.518cqh', group: 'occupancy', selected: true
        });
        createSelectable({
            screenId: 'fire_details',
            left: 35.837, top: 47.939, width: 28.326, height: 11.280, radius: '1.518cqh', group: 'occupancy'
        });
        createSelectable({
            screenId: 'fire_details',
            left: 66.510, top: 47.939, width: 28.326, height: 11.280, radius: '1.518cqh', group: 'occupancy'
        });

        // Message & voice note box toggle
        createSelectable({
            screenId: 'fire_details',
            left: 5.164, top: 68.384, width: 89.671, height: 7.918, radius: '1.518cqh'
        });

        // Adjust location button
        createButton({
            screenId: 'fire_details',
            left: 76.174, top: 78.905, width: 15.845, height: 4.121, radius: '999px'
        });

        // Send details button -> animates progress to 100%, closes form, returns to sos_active with 3 cards
        createButton({
            screenId: 'fire_details',
            left: 5.164, top: 86.171, width: 89.671, height: 6.725, radius: '1.735cqh',
            onClick: (btn) => {
                const p2 = document.getElementById('progress-bar-step2-fill');
                if (p2) {
                    p2.style.width = '100%';
                    p2.style.backgroundColor = '#22c55e';
                }
                btn.style.filter = 'brightness(1.2)';
                setTimeout(() => {
                    showScreen('sos_active', { cardsReady: true });
                }, 420);
            }
        });

        // 6. SOS Situation Worse screen
        // Vibrate toggle
        createSelectable({
            screenId: 'sos_situation_worse',
            left: 85.0, top: 8.5, width: 8.5, height: 4.5, radius: '50%', selected: true
        });

        // Better button
        createSelectable({
            screenId: 'sos_situation_worse',
            left: 4.225, top: 66.486, width: 44.0, height: 9.328, radius: '1.7cqh', group: 'worse_status'
        });

        // Worse button
        createSelectable({
            screenId: 'sos_situation_worse',
            left: 51.291, top: 66.486, width: 44.484, height: 9.328, radius: '1.7cqh', group: 'worse_status', selected: true
        });

        // Cancel SOS button
        createButton({
            screenId: 'sos_situation_worse',
            left: 4.225, top: 77.332, width: 91.549, height: 6.725, radius: '2cqh',
            onClick: () => showScreen('home')
        });

        // 7. You're Safe screen
        // 5 Rating stars
        const starPositions = [
            { left: 60.915, top: 83.297, w: 5.164, h: 2.386 },
            { left: 67.488, top: 83.297, w: 5.164, h: 2.386 },
            { left: 74.061, top: 83.297, w: 5.164, h: 2.386 },
            { left: 80.634, top: 83.297, w: 5.164, h: 2.386 },
            { left: 87.207, top: 83.297, w: 5.164, h: 2.386 }
        ];
        const starEls = [];
        starPositions.forEach((pos, index) => {
            const screen = document.getElementById('safe');
            if (!screen) return;
            const starEl = document.createElement('div');
            starEl.className = 'rating-star';
            starEl.style.position = 'absolute';
            starEl.style.left = pos.left + '%';
            starEl.style.top = pos.top + '%';
            starEl.style.width = pos.w + '%';
            starEl.style.height = pos.h + '%';
            starEl.style.borderRadius = '50%';
            starEl.style.zIndex = '9999';
            starEl.onclick = (e) => {
                e.stopPropagation();
                starEls.forEach((el, i) => {
                    if (i <= index) {
                        el.classList.add('lit');
                    } else {
                        el.classList.remove('lit');
                    }
                });
                const starSvgs = screen.querySelectorAll('[id^="21:393"], [id^="21:394"]');
                starSvgs.forEach((svg, i) => {
                    if (i <= index) {
                        svg.style.filter = 'drop-shadow(0 0 5px #fbbf24) brightness(1.6)';
                    } else {
                        svg.style.filter = 'none';
                    }
                });
            };
            screen.appendChild(starEl);
            starEls.push(starEl);
        });

        // Done button -> returns to Home
        createButton({
            screenId: 'safe',
            left: 4.577, top: 89.913, width: 90.845, height: 5.857, radius: '2cqh',
            onClick: () => showScreen('home')
        });

        clearSosActiveUpdates();
        clearWorseUpdates();
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

        /* Smooth page transition for all screens */
        .screen {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            pointer-events: none;
            visibility: hidden;
            transition: opacity 0.28s cubic-bezier(0.16, 1, 0.3, 1), transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.28s;
            transform: scale(0.992);
        }}
        .screen.active {{
            opacity: 1;
            pointer-events: auto;
            visibility: visible;
            transform: scale(1);
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

        /* Interactive selectable elements */
        .selectable-item {{
            cursor: pointer;
            pointer-events: auto;
            transition: border-color 0.2s ease, background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
            box-sizing: border-box;
            border: 1.5px solid transparent;
        }}
        .selectable-item:active {{
            transform: scale(0.975);
        }}
        .selectable-item.selected {{
            border: 1.5px solid #22c55e !important;
            background: rgba(34, 197, 94, 0.10) !important;
            box-shadow: 0 0 16px rgba(34, 197, 94, 0.20) !important;
        }}

        /* Interactive button feedback */
        .interactive-btn {{
            cursor: pointer;
            pointer-events: auto;
            transition: transform 0.15s ease, filter 0.15s ease;
        }}
        .interactive-btn:active {{
            transform: scale(0.975);
            filter: brightness(1.15);
        }}

        /* Rating stars */
        .rating-star {{
            cursor: pointer;
            pointer-events: auto;
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.2s ease;
        }}
        .rating-star:active {{
            transform: scale(1.2);
        }}
        .rating-star.lit {{
            filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.8)) brightness(1.4) !important;
        }}

        @media (prefers-reduced-motion: reduce) {{
            .screen, .update-card {{
                transition: opacity 0.2s ease;
                transform: none !important;
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
