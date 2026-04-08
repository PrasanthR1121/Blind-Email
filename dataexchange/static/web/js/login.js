// login.js

// 1. Clear any stuck toasts from the previous session immediately
$(document).ready(function() {
    if (window.history.replaceState) {
        // This stops the refresh loop by clearing the POST state
        window.history.replaceState(null, null, window.location.href);
    }
});

// 2. Handle the auto-disappear logic
document.addEventListener("DOMContentLoaded", function () {
    const toasts = document.querySelectorAll('.toast-card');
    
    toasts.forEach((toast, index) => {
        // Set a timer to remove the toast automatically
        setTimeout(() => {
            if (toast) {
                dismissToast(toast);
            }
        }, 3000 + (index * 200)); // 3 seconds + stagger for multiple messages
    });
});

// 3. Reusable dismiss function
function dismissToast(element) {
    element.style.transition = "all 0.5s ease";
    element.style.transform = "translateX(120%)";
    element.style.opacity = "0";
    setTimeout(() => {
        element.remove();
        // If no more toasts exist, remove the container to prevent layout blocking
        if (document.querySelectorAll('.toast-card').length === 0) {
            const container = document.getElementById('toast-container');
            if (container) container.innerHTML = '';
        }
    }, 500);
}

// 4. Manual close button
function closeToast(btn) {
    const toast = btn.closest('.toast-card');
    dismissToast(toast);
}

// 5. Form Validation
document.getElementById('loginForm')?.addEventListener('submit', function (e) {
    const input = document.getElementById('usernameField').value.trim();
    const emailError = document.getElementById('emailError');
    const isAdmin = input.toLowerCase() === 'prasanth';
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!isAdmin && !emailPattern.test(input)) {
        e.preventDefault();
        emailError.style.display = 'block';
        document.getElementById('usernameField').style.borderColor = '#ff4d4d';
    }
});