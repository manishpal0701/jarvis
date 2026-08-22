document.addEventListener('DOMContentLoaded', () => {
    let cartCount = 0;
    const cartBtn = document.querySelector('.cart-btn');
    document.querySelectorAll('.btn-small').forEach(btn => {
        btn.addEventListener('click', () => {
            cartCount++;
            cartBtn.textContent = `Cart (${cartCount})`;
            btn.textContent = 'Added ✓';
            btn.style.background = '#10b981';
            setTimeout(() => {
                btn.textContent = 'Add to Cart';
                btn.style.background = '#1e293b';
            }, 1500);
        });
    });
});