document.addEventListener('DOMContentLoaded', () => {
    // --- Get all necessary elements ---
    const pageTitle = document.getElementById('orders-title');
    const backToManageLink = document.getElementById('back-to-manage-link');
    const logoutButton = document.getElementById('logout-button');
    const ordersListBody = document.getElementById('orders-list');
    const noOrdersMessage = document.getElementById('no-orders-message');

    // Get the bot ID from the URL
    const pathParts = window.location.pathname.split('/');
    const botId = pathParts[pathParts.length - 1];

    // --- Event Listeners ---
    if (backToManageLink) {
        backToManageLink.href = `/manage/${botId}`;
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('userId');
            window.location.href = '/';
        });
    }

    // --- Functions ---

    // Renders a single order row in the table
    function renderOrder(order) {
        const orderRow = document.createElement('tr');
        const orderDate = new Date(order.timestamp).toLocaleString();

        // Use empty strings as placeholders if data is not available
        const username = order.telegram_username ? `@${order.telegram_username}` : 'N/A';
        const address = order.shipping_address || 'N/A';
        const note = order.customer_note || 'None';

        orderRow.innerHTML = `
            <td>${order.product_name}</td>
            <td>£${order.price.toFixed(2)}</td>
            <td><span class="status-${order.status}">${order.status}</span></td>
            <td>${username}</td>
            <td>${address}</td>
            <td>${note}</td>
            <td>${orderDate}</td>
        `;
        ordersListBody.appendChild(orderRow);
    }

    // Fetches all orders for this specific bot
    async function fetchBotOrders() {
        if (!botId) return;
        try {
            const response = await fetch(`/api/bots/${botId}/orders`);
            if (response.ok) {
                const orders = await response.json();
                
                ordersListBody.innerHTML = ''; // Clear previous list
                
                if (orders.length > 0) {
                    noOrdersMessage.classList.add('hidden');
                    orders.forEach(order => renderOrder(order));
                } else {
                    noOrdersMessage.classList.remove('hidden');
                }
            }
        } catch (error) {
            console.error('Failed to fetch bot orders:', error);
        }
    }

    // Set the page title and load the initial data
    pageTitle.textContent = `Orders for Bot (...${botId.slice(-6)})`;
    fetchBotOrders();
});