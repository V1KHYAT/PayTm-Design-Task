document.addEventListener("DOMContentLoaded", () => {
    function createOverlay(left, top, width, height, url) {
        const overlay = document.createElement('div');
        overlay.style.position = 'absolute';
        overlay.style.left = left + '%';
        overlay.style.top = top + '%';
        overlay.style.width = width + '%';
        overlay.style.height = height + '%';
        overlay.style.cursor = 'pointer';
        overlay.style.zIndex = '9999';
        overlay.style.pointerEvents = 'auto';
        // overlay.style.background = 'rgba(255,0,0,0.2)'; // debug
        
        overlay.onclick = () => {
            window.location.href = url;
        };
        document.querySelector('.phone-wrapper').appendChild(overlay);
    }

    const path = window.location.pathname;
    
    if (path.endsWith('index.html') || path === '/') {
        // SOS Button overlay
        createOverlay(5, 50, 90, 40, 'sending_alert.html');
    } 
    else if (path.endsWith('sending_alert.html')) {
        // Cancel button is at bottom
        createOverlay(5, 80, 90, 15, 'index.html');
        // auto forward
        setTimeout(() => {
            window.location.href = 'sos_active.html';
        }, 2500);
    }
    else if (path.endsWith('sos_active.html')) {
        // Swipe up
        createOverlay(5, 87, 90, 10, 'situation_category.html');
        // Worse button
        createOverlay(50, 60, 45, 10, 'sos_situation_worse.html');
        // Cancel SOS
        createOverlay(5, 70, 90, 10, 'index.html');
    }
    else if (path.endsWith('situation_category.html')) {
        // Fire or smoke (top left)
        createOverlay(5, 20, 45, 15, 'fire_details.html');
    }
    else if (path.endsWith('fire_details.html')) {
        // Send details
        createOverlay(5, 85, 90, 10, 'sos_situation_worse.html');
    }
    else if (path.endsWith('sos_situation_worse.html')) {
        setTimeout(() => {
            window.location.href = 'safe.html';
        }, 3000);
    }
    else if (path.endsWith('safe.html')) {
        // Done
        createOverlay(5, 85, 90, 10, 'index.html');
    }
});
