document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();

        if (response.ok) {
            // --- NEW: Save the logged-in user's ID in the browser's local storage ---
            localStorage.setItem('userId', result.userId);
            window.location.href = '/dashboard.html';
        } else {
            errorMessage.textContent = result.message;
        }
    });
});