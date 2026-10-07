// Main functionality for Harbor SOS app

document.addEventListener('DOMContentLoaded', () => {
    const sosCard = document.querySelector('.sos-card');
    
    sosCard.addEventListener('click', () => {
        console.log('SOS Button Clicked - Initiating Emergency Protocol');
        // Animation feedback
        sosCard.style.transform = 'scale(0.95)';
        setTimeout(() => {
            sosCard.style.transform = 'scale(1)';
        }, 150);
    });
});
