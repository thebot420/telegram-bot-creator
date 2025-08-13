document.addEventListener('DOMContentLoaded', () => {

    // --- Reusable Helper Function for API Errors ---
    async function handleApiError(response) {
        if (response.status === 401) {
            alert("Your session has expired. Please log in again.");
            window.location.href = '/';
            return null;
        }
        if (response.status === 403) {
            alert("Error: You do not have permission for this action.");
            return null;
        }
        if (response.ok && (response.headers.get("content-length") === "0" || response.status === 204)) {
            return true;
        }
        if (!response.ok) {
            const errorData = await response.json();
            alert(`An error occurred: ${errorData.message}`);
            return null;
        }
        return response.json();
    }

    // --- Get all the necessary elements ---
    const createBotButton = document.getElementById('create-bot-button');
    const addBotModal = document.getElementById('add-bot-modal');
    const cancelButton = document.getElementById('cancel-button');
    const addBotForm = document.getElementById('add-bot-form');
    const logoutButton = document.getElementById('logout-button');
    const botsListContainer = document.getElementById('bots-list-container');
    const noBotsMessage = document.querySelector('.no-bots-message');
    const userTotalSalesEl = document.getElementById('user-total-sales');
    const userTotalOrdersEl = document.getElementById('user-total-orders');
    const userRecentOrdersListDiv = document.getElementById('user-recent-orders-list');
    const userNoRecentOrdersMessage = document.getElementById('user-no-recent-orders');

    // --- Functions ---
    function renderBot(bot) {
        if (noBotsMessage) noBotsMessage.classList.add('hidden');
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
        manageButton.addEventListener('click', () => { window.location.href = `/manage/${bot.id}`; });
        
        const deleteButton = botCard.querySelector('.delete-btn');
        deleteButton.addEventListener('click', async () => {
            if (confirm('Are you sure you want to delete this bot?')) {
                try {
                    const response = await fetch(`/api/bots/${bot.id}`, { method: 'DELETE' });
                    const success = await handleApiError(response);
                    if (success) {
                        botCard.remove();
                    }
                } catch (error) {
                    console.error('Error deleting bot:', error);
                }
            }
        });
        botsListContainer.appendChild(botCard);
    }
    
    function renderRecentOrder(order) {
        if (userNoRecentOrdersMessage) userNoRecentOrdersMessage.style.display = 'none';
        const orderItem = document.createElement('div');
        orderItem.className = 'order-item';
        const orderDate = new Date(order.timestamp).toLocaleString();
        orderItem.innerHTML = `
            <div class="order-details">
                <span class="order-product-name">${order.product_name}</span>
            </div>
            <div class="order-info">
                <span class="order-price">${order.price.toFixed(2)}</span>
                <span class="order-timestamp">${orderDate}</span>
            </div>
        `;
        userRecentOrdersListDiv.appendChild(orderItem);
    }

    async function fetchAndDisplayBots() {
        const userId = localStorage.getItem('userId');
        if (!userId) { window.location.href = '/'; return; }
        try {
            const response = await fetch(`/api/users/${userId}/bots`);
            const bots = await handleApiError(response);

            if (bots) {
                botsListContainer.innerHTML = ''; 
                if (bots.length === 0 && noBotsMessage) {
                    noBotsMessage.classList.remove('hidden');
                    botsListContainer.appendChild(noBotsMessage);
                }
                bots.forEach(bot => renderBot(bot));
            }
        } catch (error) {
            console.error('Error fetching bots:', error);
        }
    }

    async function fetchUserDashboardStats() {
        const userId = localStorage.getItem('userId');
        if (!userId) return;
        try {
            const response = await fetch(`/api/users/${userId}/dashboard-stats`);
            const stats = await handleApiError(response);
            if (stats) {
                userTotalSalesEl.textContent = `$${stats.total_sales.toFixed(2)}`;
                userTotalOrdersEl.textContent = stats.total_orders;

                userRecentOrdersListDiv.innerHTML = '';
                if (stats.recent_orders.length > 0) {
                    if (userNoRecentOrdersMessage) userNoRecentOrdersMessage.style.display = 'none';
                    stats.recent_orders.forEach(order => renderRecentOrder(order));
                } else {
                    if (userNoRecentOrdersMessage) userNoRecentOrdersMessage.style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Failed to fetch user dashboard stats:', error);
        }
    }

    // --- Event Listeners & Initial Load ---
    if (logoutButton) {
        logoutButton.addEventListener('click', () => { 
            localStorage.removeItem('userId');
            window.location.href = '/'; 
        });
    }

    if (createBotButton) { createBotButton.addEventListener('click', () => { addBotModal.classList.remove('hidden'); }); }
    if (cancelButton) { cancelButton.addEventListener('click', () => { addBotModal.classList.add('hidden'); }); }
    
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
                const newBot = await handleApiError(response);
                if (newBot) {
                    renderBot(newBot);
                    addBotModal.classList.add('hidden');
                    addBotForm.reset();
                }
            } catch (error) {
                console.error('Error creating bot:', error);
            }
        });
    }

    fetchAndDisplayBots();
    fetchUserDashboardStats();
});