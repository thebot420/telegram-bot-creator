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
    // --- Get all necessary elements ---
    const pageTitle = document.getElementById('user-details-title');
    const botsListDiv = document.getElementById('user-bots-list');
    const noBotsMessage = document.getElementById('no-bots-message');
    const logoutButton = document.getElementById('admin-logout-button');
    const statusText = document.getElementById('user-status-text');
    const activeToggle = document.getElementById('active-toggle-switch');
    
    // NEW: Elements for the edit modal
    const editUserButton = document.getElementById('edit-user-button');
    const editUserModal = document.getElementById('edit-user-modal');
    const closeEditModalButton = document.getElementById('close-edit-modal-button');
    const updateEmailForm = document.getElementById('update-email-form');
    const resetPasswordForm = document.getElementById('reset-password-form');
    const editUserEmailInput = document.getElementById('edit-user-email');

    // Get the user ID from the URL
    const pathParts = window.location.pathname.split('/');
    const userId = pathParts[pathParts.length - 1];

    if (logoutButton) {
        logoutButton.addEventListener('click', () => { window.location.href = '/admin'; });
    }

    // --- Functions ---
    function renderBot(bot) {
        // ... (This function remains the same)
        if (noBotsMessage) { noBotsMessage.style.display = 'none'; }
        const botCard = document.createElement('div');
        botCard.className = 'bot-card';
        botCard.innerHTML = `
            <div class="bot-icon">🤖</div>
            <div class="bot-details">
                <h3>Bot ID: ...${bot.id.slice(-6)}</h3>
                <p>Token: ${bot.token_snippet}</p>
            </div>
            <a href="/manage/${bot.id}" class="manage-btn">Manage Bot</a>
        `;
        botsListDiv.appendChild(botCard);
    }

    async function fetchUserDetails() {
        if (!userId) return;
        try {
            const response = await fetch(`/api/admin/users/${userId}`);
            if (response.ok) {
                const user = await response.json();
                pageTitle.textContent = `User: ${user.email}`;
                editUserEmailInput.value = user.email; // Pre-fill the email in the edit form
                
                activeToggle.checked = user.is_active;
                statusText.textContent = user.is_active ? 'Active' : 'Inactive';
                statusText.className = user.is_active ? 'status-active' : 'status-inactive';

                if (user.bots.length > 0) {
                    user.bots.forEach(bot => renderBot(bot));
                }
            }
        } catch (error) {
            console.error("Failed to fetch user details:", error);
        }
    }

    // --- Event Listeners ---

    // Toggle active status
    if (activeToggle) {
        activeToggle.addEventListener('change', async () => {
            // ... (This logic remains the same)
            try {
                const response = await fetch(`/api/admin/users/${userId}/toggle-active`, { method: 'POST' });
                if (response.ok) {
                    const newState = activeToggle.checked;
                    statusText.textContent = newState ? 'Active' : 'Inactive';
                    statusText.className = newState ? 'status-active' : 'status-inactive';
                } else {
                    alert('Failed to update user status.');
                    activeToggle.checked = !activeToggle.checked;
                }
            } catch (error) {
                console.error("Error toggling user status:", error);
                activeToggle.checked = !activeToggle.checked;
            }
        });
    }

    // NEW: Show/Hide Edit Modal
    if (editUserButton) {
        editUserButton.addEventListener('click', () => {
            editUserModal.classList.remove('hidden');
        });
    }
    if (closeEditModalButton) {
        closeEditModalButton.addEventListener('click', () => {
            editUserModal.classList.add('hidden');
        });
    }

    // NEW: Handle Update Email Form
    if (updateEmailForm) {
        updateEmailForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const newEmail = editUserEmailInput.value;
            const response = await fetch(`/api/admin/users/${userId}/update-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: newEmail })
            });
            if (response.ok) {
                alert('Email updated successfully!');
                pageTitle.textContent = `User: ${newEmail}`; // Update the title on the page
            } else {
                alert('Failed to update email.');
            }
        });
    }

    // NEW: Handle Reset Password Form
    if (resetPasswordForm) {
        resetPasswordForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const newPassword = document.getElementById('new-password').value;
            const response = await fetch(`/api/admin/users/${userId}/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: newPassword })
            });
            if (response.ok) {
                alert('Password reset successfully!');
                resetPasswordForm.reset();
                editUserModal.classList.add('hidden');
            } else {
                alert('Failed to reset password.');
            }
        });
    }

    fetchUserDetails();
});
