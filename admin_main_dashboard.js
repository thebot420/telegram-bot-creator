    document.addEventListener('DOMContentLoaded', () => {
        const logoutButton = document.getElementById('admin-logout-button');
        
        // Get elements for the stat cards
        const totalSalesEl = document.getElementById('total-sales');
        const commissionEarnedEl = document.getElementById('commission-earned');
        const totalOrdersEl = document.getElementById('total-orders');
        const activeUsersEl = document.getElementById('active-users');
        
        // Get elements for the recent orders list
        const recentOrdersListDiv = document.getElementById('recent-orders-list');
        const noRecentOrdersMessage = document.getElementById('no-recent-orders');

        if (logoutButton) {
            logoutButton.addEventListener('click', () => {
                window.location.href = '/admin';
            });
        }

        function renderRecentOrder(order) {
            if (noRecentOrdersMessage) noRecentOrdersMessage.style.display = 'none';

            const orderItem = document.createElement('div');
            orderItem.className = 'order-item';
            const orderDate = new Date(order.timestamp).toLocaleString();

            orderItem.innerHTML = `
                <div class="order-details">
                    <span class="order-product-name">${order.product_name}</span>
                    <span class="order-user-email">Sold by: ${order.user_email}</span>
                </div>
                <div class="order-info">
                    <span class="order-price">${order.price.toFixed(2)}</span>
                    <span class="order-timestamp">${orderDate}</span>
                </div>
            `;
            recentOrdersListDiv.appendChild(orderItem);
        }

        async function fetchDashboardStats() {
            try {
                const response = await fetch('/api/admin/dashboard-stats');
                if (response.ok) {
                    const stats = await response.json();

                    // Populate the stat cards
                    totalSalesEl.textContent = `$${stats.total_sales.toFixed(2)}`;
                    commissionEarnedEl.textContent = `$${stats.commission_earned.toFixed(2)}`;
                    totalOrdersEl.textContent = stats.total_orders;
                    activeUsersEl.textContent = stats.active_users;

                    // Populate the recent orders list
                    if (stats.recent_orders.length > 0) {
                        stats.recent_orders.forEach(order => renderRecentOrder(order));
                    }
                }
            } catch (error) {
                console.error('Failed to fetch dashboard stats:', error);
            }
        }

        fetchDashboardStats();
    });
    