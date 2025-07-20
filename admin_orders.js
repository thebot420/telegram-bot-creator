    document.addEventListener('DOMContentLoaded', () => {
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
                }
            } catch (error) {
                console.error('Failed to fetch all orders:', error);
            }
        }

        fetchAllOrders();
    });
    