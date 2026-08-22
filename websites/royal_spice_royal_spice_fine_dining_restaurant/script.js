document.addEventListener('DOMContentLoaded', () => {
    const reserveBtn = document.querySelector('.reserve-btn');
    reserveBtn.addEventListener('click', () => {
        alert("Table reservation request received! We will call you shortly.");
    });
});