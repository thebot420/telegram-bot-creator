document.addEventListener('DOMContentLoaded', () => {
    const pageTitle = document.getElementById('user-details-title');
    const botsListDiv = document.getElementById('user-bots-list');
    const noBotsMessage = document.getElementById('no-bots-message');
    const logoutButton = document.getElementById('admin-logout-button');
    
    // NEW: Get elements for the status switch
    const statusText = document.getElementById('user-status-text');
    const activeToggle = document.getElementById('active-toggle-switch');

    // Get the user ID from the URL
    const pathParts = window.location.pathname.split('/');
    const userId = pathParts[pathParts.length - 1];

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            window.location.href = '/admin';
        });
    }

    function renderBot(bot) {
        if (noBotsMessage) {
            noBotsMessage.style.display = 'none';
        }
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
                
                // NEW: Set the initial state of the toggle switch
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

    // NEW: Add event listener for the toggle switch
    if (activeToggle) {
        activeToggle.addEventListener('change', async () => {
            try {
                const response = await fetch(`/api/admin/users/${userId}/toggle-active`, {
                    method: 'POST'
                });
                if (response.ok) {
                    // Update the text and color based on the new state
                    const newState = activeToggle.checked;
                    statusText.textContent = newState ? 'Active' : 'Inactive';
                    statusText.className = newState ? 'status-active' : 'status-inactive';
                } else {
                    alert('Failed to update user status.');
                    // Revert the switch if the API call fails
                    activeToggle.checked = !activeToggle.checked;
                }
            } catch (error) {
                console.error("Error toggling user status:", error);
                activeToggle.checked = !activeToggle.checked;
            }
        });
    }

    fetchUserDetails();
});