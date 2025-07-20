document.addEventListener('DOMContentLoaded', () => {
    // --- Get all the necessary elements ---
    const createBotButton = document.getElementById('create-bot-button');
    const addBotModal = document.getElementById('add-bot-modal');
    const cancelButton = document.getElementById('cancel-button');
    const addBotForm = document.getElementById('add-bot-form');
    const logoutButton = document.getElementById('logout-button');
    const botsListContainer = document.getElementById('bots-list-container');
    const noBotsMessage = document.querySelector('.no-bots-message');

    // --- Functions ---

    // Function to render a single bot card on the dashboard
    function renderBot(bot) {
        if (noBotsMessage) {
            noBotsMessage.classList.add('hidden');
        }

        const botCard = document.createElement('div');
        botCard.className = 'bot-card';
        botCard.innerHTML = `
            <div class="bot-icon">🤖</div>
            <div class="bot-details">
                <h3>Bot ID: ...${bot.id.slice(-6)}</h3>
                <p>Wallet: ...${bot.wallet.slice(-6)}</p>
            </div>
            <div class="bot-actions">
                <button class="manage-btn">Manage</button>
                <button class="delete-btn" data-id="${bot.id}">Delete</button>
            </div>
        `;

        const manageButton = botCard.querySelector('.manage-btn');
        manageButton.addEventListener('click', () => {
            window.location.href = `/manage/${bot.id}`;
        });

        const deleteButton = botCard.querySelector('.delete-btn');
        deleteButton.addEventListener('click', async () => {
            if (confirm('Are you sure you want to delete this bot?')) {
                const response = await fetch(`/api/bots/${bot.id}`, { method: 'DELETE' });
                if (response.ok) {
                    botCard.remove();
                } else {
                    alert('Failed to delete bot.');
                }
            }
        });

        botsListContainer.appendChild(botCard);
    }

    // Function to fetch all bots for the logged-in user and display them
    async function fetchAndDisplayBots() {
        const userId = localStorage.getItem('userId');
        if (!userId) {
            console.error("No user ID found, cannot fetch bots.");
            return;
        }

        try {
            const response = await fetch(`/api/users/${userId}/bots`);
            if (response.ok) {
                const bots = await response.json();
                botsListContainer.innerHTML = ''; 
                if (bots.length === 0 && noBotsMessage) {
                    noBotsMessage.classList.remove('hidden');
                    botsListContainer.appendChild(noBotsMessage);
                } else if (noBotsMessage) {
                    noBotsMessage.classList.add('hidden');
                }
                bots.forEach(bot => renderBot(bot));
            }
        } catch (error) {
            console.error('Error fetching bots:', error);
        }
    }

    // --- Event Listeners & Initial Load ---

    if (logoutButton) {
        logoutButton.addEventListener('click', () => { 
            localStorage.removeItem('userId'); // Clear the user ID on logout
            window.location.href = '/'; 
        });
    }

    if (createBotButton) {
        createBotButton.addEventListener('click', () => { addBotModal.classList.remove('hidden'); });
    }

    if (cancelButton) {
        cancelButton.addEventListener('click', () => {
            addBotModal.classList.add('hidden');
        });
    }

    if (addBotForm) {
        addBotForm.addEventListener('submit', async (event) => {
            event.preventDefault(); 
            
            const bot_token = document.getElementById('bot-token').value;
            const wallet_address = document.getElementById('wallet-address').value;
            const userId = localStorage.getItem('userId');

            if (!userId) {
                alert('Error: Not logged in. Please log in again.');
                return;
            }
            
            try {
                const response = await fetch('/api/bots', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ bot_token, wallet_address, userId })
                });

                if (response.ok) {
                    const newBot = await response.json();
                    renderBot(newBot);
                    addBotModal.classList.add('hidden');
                    addBotForm.reset();
                } else {
                    const error = await response.json();
                    alert(`Failed to create bot: ${error.message}`);
                }
            } catch (error) {
                console.error('Error creating bot:', error);
            }
        });
    }

    fetchAndDisplayBots();
});
