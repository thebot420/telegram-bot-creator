// Replace the old renderBot function in dashboard.js with this one
function renderBot(bot) {
    if (noBotsMessage) {
        noBotsMessage.classList.add('hidden');
    }

    const botCard = document.createElement('div');
    botCard.className = 'bot-card';
    // --- NEW: Added a delete button with a specific data-id attribute ---
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

    // --- NEW: Find the delete button and add a click event to it ---
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