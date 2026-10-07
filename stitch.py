import os
import re

files = [
    "index.html",
    "sending_alert.html",
    "sos_active.html",
    "situation_category.html",
    "fire_details.html",
    "sos_situation_worse.html",
]

# We will read each file, extract the content inside <div class="phone">, 
# and wrap it in a <div id="screen_{name}" class="screen">.

spa_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harbor SPA</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="figma_additions.css">
</head>
<body>
    <div class="phone">
"""

screens_js = []

for file in files:
    name = file.replace(".html", "")
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract everything inside <div class="phone"> ... </div>
    match = re.search(r'<div class="phone"[^>]*>(.*?)</div>\s*</body>', content, re.DOTALL)
    if match:
        inner = match.group(1)
        # wrap in screen
        display = "flex" if name == "index" else "none"
        spa_html += f'        <div id="screen_{name}" class="screen" style="display: {display}; width: 100%; height: 100%; flex-direction: column;">\n'
        spa_html += inner
        spa_html += f'        </div>\n'

# Add JS for navigation
spa_html += """
    </div>
    
    <script>
        function showScreen(id) {
            document.querySelectorAll('.screen').forEach(s => s.style.display = 'none');
            document.getElementById('screen_' + id).style.display = 'flex';
        }

        document.addEventListener('DOMContentLoaded', () => {
            // Home -> SOS
            const sosBtn = document.querySelector('#screen_index .sos-card');
            if(sosBtn) sosBtn.addEventListener('click', () => {
                showScreen('sending_alert');
                setTimeout(() => showScreen('sos_active'), 2500);
            });

            // Sending -> Cancel
            const cancelBtn = document.querySelector('#screen_sending_alert .cancel-btn');
            if(cancelBtn) cancelBtn.addEventListener('click', () => {
                showScreen('index');
            });

            // Active -> Swipe up (Category)
            const swipeUp = document.querySelector('#screen_sos_active .swipe-hint');
            if(swipeUp) swipeUp.addEventListener('click', () => {
                showScreen('situation_category');
            });

            // Active -> Worse
            const worseBtn = document.querySelector('#screen_sos_active .action-btn.red');
            if(worseBtn) worseBtn.addEventListener('click', () => {
                showScreen('sos_situation_worse');
                setTimeout(() => showScreen('index'), 3000); // Or safe.html if we had it
            });

            // Category -> Fire
            const fireBtn = document.querySelector('#screen_situation_category .category-card'); // just grab first
            if(fireBtn) fireBtn.addEventListener('click', () => {
                showScreen('fire_details');
            });

            // Details -> Send
            const sendBtn = document.querySelector('#screen_fire_details .send-btn');
            if(sendBtn) sendBtn.addEventListener('click', () => {
                showScreen('sos_situation_worse');
                setTimeout(() => showScreen('index'), 3000);
            });
        });
    </script>
</body>
</html>
"""

with open("index_spa.html", "w", encoding="utf-8") as f:
    f.write(spa_html)
print("Built SPA")
