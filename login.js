// This script runs after the page is loaded
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    // Listen for when the user clicks the 'Login' button
    form.addEventListener('submit', async (event) => {
        // Prevent the page from refreshing
        event.preventDefault(); 

        // Get user input from the form fields
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        // Send the email and password to our Python backend
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();

        if (response.ok) {
            // If login is successful, redirect to the dashboard
            window.location.href = '/dashboard.html';
        } else {
            // If login fails, show an error message
            errorMessage.textContent = result.message;
        }
    });
});