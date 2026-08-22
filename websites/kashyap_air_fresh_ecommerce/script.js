document.addEventListener('DOMContentLoaded', () => {
    let count = 0;
    const cartBtn = document.querySelector('.cart-btn');
    document.querySelectorAll('.add-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            count++;
            cartBtn.textContent = `Shop Cart (${count})`;
            btn.textContent = 'Added ✓';
            btn.style.background = '#10b981';
            setTimeout(() => {
                btn.textContent = 'Shop Now';
                btn.style.background = '#292524';
            }, 1500);
        });
    });
});