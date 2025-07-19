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

        // Find the manage button and add a click event to it
        const manageButton = botCard.querySelector('.manage-btn');
        manageButton.addEventListener('click', () => {
            window.location.href = `/manage/${bot.id}`;
        });

        // Find the delete button and add a click event to it
        const deleteButton = botCard.querySelector('.delete-btn');
        deleteButton.addEventListener('click', async () => {
            // Show a confirmation dialog to prevent accidental deletion
            const isConfirmed = confirm('Are you sure you want to delete this bot? This action cannot be undone.');

            if (isConfirmed) {
                try {
                    const response = await fetch(`/api/bots/${bot.id}`, {
                        method: 'DELETE',
                    });

                    if (response.ok) {
                        // If deletion is successful, remove the bot card from the page
                        botCard.remove();
                    } else {
                        alert('Failed to delete bot.');
                    }
                } catch (error) {
                    console.error('Error deleting bot:', error);
                    alert('An error occurred while deleting the bot.');
                }
            }
        });

        botsListContainer.appendChild(botCard);
    }

    // Function to fetch all bots from the server and display them
    async function fetchAndDisplayBots() {
        try {
            const response = await fetch('/api/bots');
            const bots = await response.json();
            bots.forEach(bot => renderBot(bot));
        } catch (error) {
            console.error('Error fetching bots:', error);
        }
    }

    // --- Event Listeners & Initial Load ---

    // Logout Button
    if (logoutButton) {
        logoutButton.addEventListener('click', () => { window.location.href = '/'; });
    }

    // Show modal
    if (createBotButton) {
        createBotButton.addEventListener('click', () => { addBotModal.classList.remove('hidden'); });
    }

    // Hide modal
    if (cancelButton) {
        cancelButton.addEventListener('click', () => {
            addBotModal.classList.add('hidden');
        });
    }

    // Handle the form submission to create a new bot
    if (addBotForm) {
        addBotForm.addEventListener('submit', async (event) => {
            event.preventDefault(); 
            
            const bot_token = document.getElementById('bot-token').value;
            const wallet_address = document.getElementById('wallet-address').value;
            
            try {
                const response = await fetch('/api/bots', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ bot_token, wallet_address })
                });

                if (response.ok) {
                    const newBot = await response.json();
                    renderBot(newBot);
                    addBotModal.classList.add('hidden');
                    addBotForm.reset();
                } else {
                    alert('Failed to create bot. Please try again.');
                }
            } catch (error) {
                console.error('Error creating bot:', error);
                alert('An error occurred.');
            }
        });
    }

    // Load any existing bots when the page first loads
    fetchAndDisplayBots();
});
