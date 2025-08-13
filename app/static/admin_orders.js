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
    const ordersListDiv = document.getElementById('master-orders-list');
    const noOrdersMessage = document.getElementById('no-orders-message');
    const logoutButton = document.getElementById('admin-logout-button');

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            window.location.href = '/admin';
        });
    }

    function renderOrder(order) {
        if (noOrdersMessage) {
            noOrdersMessage.style.display = 'none';
        }
        const orderItem = document.createElement('div');
        orderItem.className = 'order-item';
        
        const orderDate = new Date(order.timestamp).toLocaleString();

        orderItem.innerHTML = `
            <div class="order-details">
                <span class="order-product-name">${order.product_name}</span>
                <span class="order-user-email">Sold by: ${order.user_email}</span>
            </div>
            <div class="order-info">
                <span class="order-price">${order.price}</span>
                <span class="order-timestamp">${orderDate}</span>
            </div>
        `;
        ordersListDiv.appendChild(orderItem);
    }

    async function fetchAllOrders() {
        try {
            const response = await fetch('/api/admin/orders');
            if (response.ok) {
                const orders = await response.json();
                if (orders.length > 0) {
                    orders.forEach(order => renderOrder(order));
                }
            } else {
                console.error("Failed to fetch orders, server responded with an error.");
            }
        } catch (error) {
            console.error('Failed to fetch all orders:', error);
        }
    }

    fetchAllOrders();
});
