document.addEventListener('DOMContentLoaded', () => {
    
    
    // --- Helper Function for Admin API Errors ---
    async function handleApiError(response) {
        // Redirect to ADMIN login on 401
        if (response.status === 401) {
            alert("Your session has expired. Please log in again.");
            window.location.href = '/admin'; // <-- Key change for admin pages
            return null;
        }
        if (response.status === 403) {
            alert("Error: You do not have permission for this action.");
            return null;
        }
        if (!response.ok) {
            const errorData = await response.json();
            const errorMessageEl = document.getElementById('error-message');
            if (errorMessageEl) {
                errorMessageEl.textContent = errorData.message || 'An unknown error occurred.';
            } else {
                alert(`An error occurred: ${errorData.message}`);
            }
            return null;
        }
        return response.json();
    }
    
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
            }
        });
    }
});
document.addEventListener('DOMContentLoaded', () => {
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
                    // On success, redirect to the main admin dashboard
                    window.location.href = '/admin/dashboard';
                } else {
                    errorMessage.textContent = result.message || 'Login failed!';
                }
            } catch (error) {
                errorMessage.textContent = 'A network error occurred.';
                console.error('Admin login error:', error);
            }
        });
    }
});
