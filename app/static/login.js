document.addEventListener('DOMContentLoaded', () => {

    // --- Helper Function for API Errors ---
    async function handleApiError(response) {
        if (response.status === 401) {
            alert("Your session has expired. Please log in again.");
            window.location.href = '/';
            return null;
        }
        if (response.status === 403) {
            alert("Error: You do not have permission to perform this action.");
            return null;
        }
        if (!response.ok) {
            const errorData = await response.json();
            // Use the error message element instead of an alert for login errors
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

    // --- Select Elements from the HTML ---
    // This is the part that was likely missing.
    const form = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    // --- Login Form Logic ---
    if (form) {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            errorMessage.textContent = ''; // Clear previous errors

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const result = await handleApiError(response);

                if (result) {
                    localStorage.setItem('userId', result.userId);
                    window.location.href = '/dashboard.html';
                }
            } catch (error) {
                errorMessage.textContent = 'A network error occurred. Please try again.';
                console.error('Login error:', error);
            }
        });
    }
});