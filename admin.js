        const form = document.getElementById('admin-login-form');
        const errorMessage = document.getElementById('error-message');

        if (form) {
            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                try {
                    const response = await fetch('/api/admin/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });

                    const result = await response.json();

                    if (response.ok) {
                        // On success, redirect to the admin dashboard
                        window.location.href = '/admin/dashboard';
                    } else {
                        errorMessage.textContent = result.message || 'Login failed!';
                    }
                } catch (error) {
                    errorMessage.textContent = 'A network error occurred.';
                    console.error('Admin login error:', error);
                }  document.addEventListener('DOMContentLoaded', () => {
            });
        }
    });
    