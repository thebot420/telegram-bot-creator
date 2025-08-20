document.addEventListener('DOMContentLoaded', () => {

    // --- Reusable Helper Function for API Errors ---
    async function handleApiError(response) {
        if (response.status === 401) {
            alert("Your session has expired. Please log in again.");
            window.location.href = '/';
            return null;
        }
        if (response.status === 403) {
            alert("Error: You do not have permission to perform this action.");
            return null;
        }
        if (!response.ok) {
            const errorData = await response.json();
            alert(`An error occurred: ${errorData.message}`);
            return null;
        }
        if (response.headers.get("content-length") === "0") {
            return true; 
        }
        return response.json();
    }

    // --- Get all necessary elements ---
    const pageTitle = document.getElementById('orders-title');
    const backToManageLink = document.getElementById('back-to-manage-link');
    const logoutButton = document.getElementById('logout-button');
    const ordersListBody = document.getElementById('orders-list');
    const noOrdersMessage = document.getElementById('no-orders-message');

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

    // --- UPDATED RENDER FUNCTION ---
    function renderOrder(order) {
        const orderRow = document.createElement('tr');
        const orderDate = new Date(order.timestamp).toLocaleString();
        const username = order.telegram_username ? `@${order.telegram_username}` : 'N/A';
        const address = order.shipping_address || 'N/A';
        const note = order.customer_note || 'None';

        // --- NEW: Status Cell Logic ---
        let statusCellHtml = '';
        const formattedStatus = order.status.replace('_', ' ');

        if (order.status === 'underpaid' || order.status === 'overpaid') {
            const discrepancy = Math.abs(order.amount_paid - order.price);
            const currency = order.payment_currency ? order.payment_currency.toUpperCase() : 'USD';
            
            statusCellHtml = `
                <span class="status-${order.status}" title="Expected: ${order.price.toFixed(2)} ${currency} | Paid: ${order.amount_paid.toFixed(8)} ${currency}">
                    ${formattedStatus}
                    <small>(${discrepancy.toFixed(8)} ${currency})</small>
                </span>
            `;
        } else {
            statusCellHtml = `<span class="status-${order.status}">${formattedStatus}</span>`;
        }
        // --- END of New Logic ---

        orderRow.innerHTML = `
            <td>${order.product_name}</td>
            <td>$${order.price.toFixed(2)}</td>
            <td>${statusCellHtml}</td>
            <td>${username}</td>
            <td>${address}</td>
            <td>${note}</td>
            <td>${orderDate}</td>
            <td class="actions-cell"></td>
        `;

        const actionsCell = orderRow.querySelector('.actions-cell');
        
        if (order.status === 'paid') {
            const dispatchButton = document.createElement('button');
            dispatchButton.className = 'btn-primary btn-small';
            dispatchButton.textContent = 'Mark as Dispatched';
            dispatchButton.addEventListener('click', () => markAsDispatched(order.id, dispatchButton));
            actionsCell.appendChild(dispatchButton);
        } else if (order.status === 'dispatched') {
            actionsCell.textContent = '✅ Dispatched';
        }

        ordersListBody.appendChild(orderRow);
    }

    // --- API Call Functions ---
    async function markAsDispatched(orderId, buttonElement) {
        try {
            const response = await fetch(`/api/orders/${orderId}/dispatch`, {
                method: 'POST'
            });
            const success = await handleApiError(response);
            if (success) {
                buttonElement.parentElement.textContent = '✅ Dispatched';
            }
        } catch (error) {
            console.error('Error dispatching order:', error);
            alert('A network error occurred.');
        }
    }

    async function fetchBotOrders() {
        if (!botId) return;
        try {
            const response = await fetch(`/api/bots/${botId}/orders`);
            const orders = await handleApiError(response);
            
            if (orders) {
                ordersListBody.innerHTML = '';
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

    // --- Initial Load ---
    pageTitle.textContent = `Orders for Bot (...${botId.slice(-6)})`;
    fetchBotOrders();
});