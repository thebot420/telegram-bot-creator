    document.addEventListener('DOMContentLoaded', () => {
        const pageTitle = document.getElementById('user-details-title');
        const botsListDiv = document.getElementById('user-bots-list');
        const noBotsMessage = document.getElementById('no-bots-message');
        const logoutButton = document.getElementById('admin-logout-button');

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
            botCard.className = 'bot-card'; // We can reuse the bot-card style
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
                    
                    if (user.bots.length > 0) {
                        user.bots.forEach(bot => renderBot(bot));
                    }
                }
            } catch (error) {
                console.error("Failed to fetch user details:", error);
            }
        }

        fetchUserDetails();
    });
    