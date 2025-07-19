document.addEventListener('DOMContentLoaded', () => {
    const ordersListDiv = document.getElementById('orders-list');
    const noOrdersMessage = document.getElementById('no-orders-message');
    const backButton = document.getElementById('back-to-manage-link');

    // Get the bot ID from the URL
    const pathParts = window.location.pathname.split('/');
    const botId = pathParts[pathParts.length - 1];

    // Set the "Back" button link correctly
    if (backButton) {
        backButton.href = `/manage/${botId}`;
    }

    function renderOrder(order) {
        if (noOrdersMessage) {
            noOrdersMessage.style.display = 'none';
        }
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-item';

        const orderDate = new Date(order.timestamp).toLocaleString();

        orderDiv.innerHTML = `
            <div class="order-details">
                <span class="order-product-name">${order.product_name}</span>
                <span class="order-id">ID: ...${order.id.slice(-6)}</span>
            </div>
            <div class="order-info">
                <span class="order-price">${order.price}</span>
                <span class="order-timestamp">${orderDate}</span>
            </div>
        `;
        ordersListDiv.appendChild(orderDiv);
    }

    async function loadOrders() {
        if (!botId) return;
        try {
            // We'll create this API endpoint next
            const response = await fetch(`/api/bots/${botId}/orders`);
            if (!response.ok) return;

            const orders = await response.json();
            orders.forEach(order => renderOrder(order));
        } catch (error) {
            console.error('Failed to load orders:', error);
        }
    }

    loadOrders();
});