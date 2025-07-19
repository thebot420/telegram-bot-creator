document.addEventListener('DOMContentLoaded', () => {
    // --- Get all necessary elements from the page ---
    const addProductForm = document.getElementById('add-product-form');
    const productListDiv = document.getElementById('product-list');
    const noProductsMessage = document.getElementById('no-products-message');
    const pageTitle = document.getElementById('manage-bot-title');
    const viewOrdersLink = document.getElementById('view-orders-link'); // Moved to the correct place

    // Get the bot ID from the URL
    const pathParts = window.location.pathname.split('/');
    const botId = pathParts[pathParts.length - 1];

    // --- Functions ---

    // Function to render a single product in the list
    function renderProduct(product) {
        if (noProductsMessage) {
            noProductsMessage.style.display = 'none';
        }
        const productDiv = document.createElement('div');
        productDiv.className = 'product-item';
        productDiv.innerHTML = `
            <span>${product.name}</span>
            <span class="product-price">${product.price}</span>
        `;
        productListDiv.appendChild(productDiv);
    }

    // Function to load bot details and products
    async function loadBotData() {
        if (!botId) return;
        try {
            const response = await fetch(`/api/bots/${botId}`);
            if (!response.ok) return;
            const bot = await response.json();
            
            // Update the page title
            pageTitle.textContent = `Manage Bot (...${bot.id.slice(-6)})`;
            
            // Set the "View Orders" link URL - This logic is now in the correct place
            if (viewOrdersLink) {
                viewOrdersLink.href = `/orders/${bot.id}`;
            }
            
            // Render existing products
            bot.products.forEach(product => renderProduct(product));
        } catch (error) {
            console.error('Failed to load bot data:', error);
        }
    }

    // --- Event Listeners & Initial Load ---

    // Handle the "Add Product" form submission
    addProductForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const name = document.getElementById('product-name').value;
        const price = document.getElementById('product-price').value;

        try {
            const response = await fetch(`/api/bots/${botId}/products`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, price })
            });

            if (response.ok) {
                const newProduct = await response.json();
                renderProduct(newProduct);
                addProductForm.reset();
            } else {
                alert('Failed to add product.');
            }
        } catch (error) {
            console.error('Error adding product:', error);
        }
    });

    // Initial load of data when the page opens
    loadBotData();
});