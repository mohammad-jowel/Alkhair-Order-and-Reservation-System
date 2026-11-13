/**
 * Restoran Alkhair - Main JavaScript
 * Minimal, progressive enhancement script.
 * Core site functionality works with or without JavaScript.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Universal In-App Confirmation Modal (Replaces native browser alert/confirm)
    const universalModalEl = document.getElementById('universalConfirmModal');
    let universalModal = null;
    let pendingAction = null;

    if (universalModalEl && typeof bootstrap !== 'undefined') {
        universalModal = new bootstrap.Modal(universalModalEl);

        const modalTitle = document.getElementById('universalConfirmModalLabel');
        const modalText = document.getElementById('universalConfirmModalText');
        const submitBtn = document.getElementById('universalConfirmSubmitBtn');
        const submitText = document.getElementById('universalConfirmSubmitText');
        const iconWrapper = document.getElementById('universalConfirmIconWrapper');
        const icon = document.getElementById('universalConfirmIcon');

        document.addEventListener('click', function (e) {
            const target = e.target.closest('[data-confirm]');
            if (!target) return;

            e.preventDefault();
            e.stopPropagation();

            const message = target.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            const msgLower = message.toLowerCase();

            // Auto-detect title, button text, and intent
            const title = target.getAttribute('data-confirm-title') || (
                msgLower.includes('delete') ? 'Confirm Deletion' :
                msgLower.includes('cancel') ? 'Confirm Cancellation' :
                msgLower.includes('clear') ? 'Confirm Clear' :
                msgLower.includes('reject') ? 'Confirm Rejection' : 'Confirmation'
            );

            const btnText = target.getAttribute('data-confirm-btn') || (
                msgLower.includes('delete') ? 'Delete' :
                msgLower.includes('cancel') ? 'Confirm Cancel' :
                msgLower.includes('clear') ? 'Clear' :
                msgLower.includes('reject') ? 'Reject' : 'Confirm'
            );

            const confirmType = target.getAttribute('data-confirm-type') || (
                (msgLower.includes('delete') || msgLower.includes('cancel') || msgLower.includes('clear') || msgLower.includes('reject')) ? 'danger' : 'primary'
            );

            // Populate modal content
            modalTitle.textContent = title;
            modalText.innerHTML = message;
            submitText.textContent = btnText;

            // Set button and icon colors
            submitBtn.className = `btn btn-${confirmType} px-3 btn-sm`;
            if (confirmType === 'danger') {
                iconWrapper.style.background = '#fee2e2';
                iconWrapper.style.color = '#dc2626';
                icon.className = 'bi bi-exclamation-triangle-fill fs-3';
            } else if (confirmType === 'warning') {
                iconWrapper.style.background = '#fef3c7';
                iconWrapper.style.color = '#d97706';
                icon.className = 'bi bi-exclamation-circle-fill fs-3';
            } else {
                iconWrapper.style.background = '#ffedd5';
                iconWrapper.style.color = '#ea580c';
                icon.className = 'bi bi-info-circle-fill fs-3';
            }

            // Save callback to execute on confirmation
            pendingAction = function () {
                if (target.tagName.toLowerCase() === 'a') {
                    window.location.href = target.href;
                } else if (target.form) {
                    if (target.name && target.value) {
                        let hidden = target.form.querySelector(`input[type="hidden"][name="${target.name}"]`);
                        if (!hidden) {
                            hidden = document.createElement('input');
                            hidden.type = 'hidden';
                            hidden.name = target.name;
                            target.form.appendChild(hidden);
                        }
                        hidden.value = target.value;
                    }
                    target.form.submit();
                } else if (target.closest('form')) {
                    target.closest('form').submit();
                }
            };

            universalModal.show();
        });

        submitBtn.addEventListener('click', function () {
            if (pendingAction) {
                const action = pendingAction;
                pendingAction = null;
                universalModal.hide();
                action();
            }
        });
    } else {
        // Fallback for no-bootstrap or disabled JS environment
        const deleteButtons = document.querySelectorAll('[data-confirm]');
        deleteButtons.forEach(button => {
            button.addEventListener('click', function (e) {
                const message = this.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });
    }

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
