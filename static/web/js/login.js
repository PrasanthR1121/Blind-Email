function closeToast(btn) {
    let toast = btn.closest('.toast-card');
    toast.style.transform = "translateX(120%)";
    toast.style.transition = "0.5s ease";
    setTimeout(() => toast.remove(), 2000);
}

document.addEventListener("DOMContentLoaded", function () {
    const toasts = document.querySelectorAll('.toast-card');
    toasts.forEach(toast => {
        setTimeout(() => {
            if (toast) {
                toast.style.transform = "translateX(120%)";
                toast.style.transition = "0.5s ease";
                toast.style.opacity = "0";
                setTimeout(() => toast.remove(), 2000);
            }
        }, 2500);
    });
});

document.getElementById('loginForm').addEventListener('submit', function (e) {
    const input = document.getElementById('usernameField').value.trim();
    const emailError = document.getElementById('emailError');

    const isAdmin = input.toLowerCase() === 'prasanth';

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!isAdmin && !emailPattern.test(input)) {
        e.preventDefault();
        emailError.style.display = 'block';
        document.getElementById('usernameField').style.borderColor = '#ff4d4d';
    } else {
        emailError.style.display = 'none';
        document.getElementById('usernameField').style.borderColor = 'rgba(255,255,255,0.2)';
    }
});

document.getElementById('usernameField').addEventListener('input', function () {
    this.style.borderColor = 'rgba(255,255,255,0.2)';
    document.getElementById('emailError').style.display = 'none';
});

(function () {
    window.onpageshow = function (event) {
        if (event.persisted) {
            window.location.reload();
        }
    };
})();