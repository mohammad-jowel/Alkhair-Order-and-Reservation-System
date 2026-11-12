/**
 * Restoran Alkhair - Main JavaScript
 * Minimal, progressive enhancement script.
 * Core site functionality works with or without JavaScript.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Delete confirmation prompt for safety
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // 2. Cart quantity buttons (+ / -) progressive enhancement
    const quantityControls = document.querySelectorAll('.cart-quantity-control');
    quantityControls.forEach(control => {
        const input = control.querySelector('input[type="number"]');
        const btnMinus = control.querySelector('.btn-qty-minus');
        const btnPlus = control.querySelector('.btn-qty-plus');

        if (input && btnMinus && btnPlus) {
            btnMinus.addEventListener('click', function () {
                let currentVal = parseInt(input.value, 10) || 1;
                if (currentVal > 1) {
                    input.value = currentVal - 1;
                }
            });

            btnPlus.addEventListener('click', function () {
                let currentVal = parseInt(input.value, 10) || 1;
                if (currentVal < 99) {
                    input.value = currentVal + 1;
                }
            });
        }
    });

    // 3. Auto-dismiss alerts after 5 seconds (optional enhancement)
    const alertElements = document.querySelectorAll('.alert-dismissible');
    alertElements.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 6000);
    });
});
