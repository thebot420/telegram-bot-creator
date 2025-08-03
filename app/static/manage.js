document.addEventListener('DOMContentLoaded', () => {
    // --- Get all necessary elements ---
    const pageTitle = document.getElementById('manage-bot-title');
    const viewOrdersLink = document.getElementById('view-orders-link');
    const addCategoryForm = document.getElementById('add-category-form');
    const categoryListDiv = document.getElementById('category-list');
    const noCategoriesMessage = document.getElementById('no-categories-message');
    const addProductForm = document.getElementById('add-product-form');
    const productCategorySelect = document.getElementById('product-category');
    const productListDisplayDiv = document.getElementById('product-list-display');
    const logoutButton = document.getElementById('logout-button'); // Added logout button

    // Get the bot ID from the URL
    const pathParts = window.location.pathname.split('/');
    const botId = pathParts[pathParts.length - 1];

    // --- Logout Logic ---
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('userId'); // Clear user session
            window.location.href = '/';
        });
    }

    // --- Functions ---

    // Renders a single category in the "Manage Categories" list
    function renderCategory(category) {
        if (noCategoriesMessage) noCategoriesMessage.style.display = 'none';
        
        const categoryItem = document.createElement('div');
        categoryItem.className = 'category-item';
        categoryItem.innerHTML = `
            <span>${category.name}</span>
            <button class="delete-category-btn" data-id="${category.id}">&times;</button>
        `;

        const deleteButton = categoryItem.querySelector('.delete-category-btn');
        deleteButton.addEventListener('click', async () => {
            if (confirm(`Are you sure you want to delete the category "${category.name}"? All products within it will also be deleted.`)) {
                try {
                    const response = await fetch(`/api/categories/${category.id}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        loadBotData(); // Reload everything to ensure consistency
                    } else {
                        alert('Failed to delete category.');
                    }
                } catch (error) {
                    console.error("Error deleting category:", error);
                }
            }
        });
        categoryListDiv.appendChild(categoryItem);
    }

    // Adds a category to the dropdown in the "Add Product" form
    function addCategoryToSelect(category) {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        productCategorySelect.appendChild(option);
    }

    // Renders all products, grouped by category
    function renderAllProducts(categories) {
        productListDisplayDiv.innerHTML = ''; // Clear previous list
        if (categories.length === 0 || categories.every(c => c.products.length === 0)) {
            const p = document.createElement('p');
            p.textContent = 'No products added yet.';
            productListDisplayDiv.appendChild(p);
            return;
        }

        categories.forEach(category => {
            if (category.products.length > 0) {
                const categorySection = document.createElement('div');
                categorySection.className = 'product-category-section';
                
                const categoryTitle = document.createElement('h4');
                categoryTitle.textContent = category.name;
                categorySection.appendChild(categoryTitle);

                category.products.forEach(product => {
                    const productItem = document.createElement('div');
                    productItem.className = 'product-item';
                    productItem.innerHTML = `
                        <span>${product.name}</span>
                        <span class="product-price">${product.price}</span>
                    `;
                    categorySection.appendChild(productItem);
                });
                productListDisplayDiv.appendChild(categorySection);
            }
        });
    }

    // Fetches all bot data (categories and products) when the page loads
    async function loadBotData() {
        if (!botId) return;
        try {
            const response = await fetch(`/api/bots/${botId}`);
            if (!response.ok) return;
            const bot = await response.json();
            
            pageTitle.textContent = `Manage Bot (...${bot.id.slice(-6)})`;
            if (viewOrdersLink) viewOrdersLink.href = `/orders/${bot.id}`;
            
            // --- THIS IS THE FIX ---
            // Clear existing lists before re-populating to prevent duplicates
            categoryListDiv.innerHTML = '';
            productCategorySelect.innerHTML = '<option value="">-- Select a Category --</option>';
            
            if (bot.categories.length > 0) {
                if (noCategoriesMessage) noCategoriesMessage.style.display = 'none';
            } else {
                if (noCategoriesMessage) noCategoriesMessage.style.display = 'block';
            }
            // --- END FIX ---

            // Re-populate the lists
            bot.categories.forEach(category => {
                renderCategory(category);
                addCategoryToSelect(category);
            });

            // Re-populate the product list
            renderAllProducts(bot.categories);

        } catch (error) {
            console.error('Failed to load bot data:', error);
        }
    }

    // --- Event Listeners ---

    // Handle "Add Category" form submission
    if (addCategoryForm) {
        addCategoryForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const nameInput = document.getElementById('category-name');
            const response = await fetch(`/api/bots/${botId}/categories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: nameInput.value })
            });
            if (response.ok) {
                const newCategory = await response.json();
                renderCategory(newCategory);
                addCategoryToSelect(newCategory);
                nameInput.value = '';
            } else {
                alert('Failed to create category.');
            }
        });
    }

    // Handle "Add Product" form submission
    if (addProductForm) {
        addProductForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const productData = {
                category_id: document.getElementById('product-category').value,
                name: document.getElementById('product-name').value,
                price: document.getElementById('product-price').value,
                image_url: document.getElementById('product-image-url').value,
                video_url: document.getElementById('product-video-url').value,
            };

            const response = await fetch(`/api/bots/${botId}/products`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData)
            });

            if (response.ok) {
                addProductForm.reset();
                loadBotData();
            } else {
                alert('Failed to add product.');
            }
        });
    }

    // Initial load of data
    loadBotData();
});
