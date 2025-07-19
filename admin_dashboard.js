    document.addEventListener('DOMContentLoaded', () => {
        const logoutButton = document.getElementById('admin-logout-button');

        if (logoutButton) {
            logoutButton.addEventListener('click', () => {
                // For now, logging out just goes back to the admin login page
                window.location.href = '/admin';
            });
        }

        // We will add the logic for creating and listing users in the next step.
    });
    