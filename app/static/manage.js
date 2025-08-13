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
        // For successful actions that don't return data (like DELETE)
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

    // --- Get all necessary elements ---
    const pageTitle = document.getElementById('manage-bot-title');
    const viewOrdersLink = document.getElementById('view-orders-link');
    const welcomeMessageForm = document.getElementById('welcome-message-form');
    const welcomeMessageTextarea = document.getElementById('welcome-message');
    const categoryManagerDiv = document.getElementById('category-manager');
    const noCategoriesMessage = document.getElementById('no-categories-message');
    const addMainCategoryForm = document.getElementById('add-main-category-form');
    const productCategorySelect = document.getElementById('product-category');
    const addProductForm = document.getElementById('add-product-form');
    const productListDisplayDiv = document.getElementById('product-list-display');
    const logoutButton = document.getElementById('logout-button');
    const priceTierModal = document.getElementById('price-tier-modal');
    const priceTierTitle = document.getElementById('price-tier-title');
    const existingTiersList = document.getElementById('existing-tiers-list');
    const addPriceTierForm = document.getElementById('add-price-tier-form');
    const closePriceModalButton = document.getElementById('close-price-modal-button');

    let currentProductIdForTiers = null;
    const pathParts = window.location.pathname.split('/');
    const botId = pathParts[pathParts.length - 1];
    let uploadedFileUrl = null;

    // --- Initialize FilePond ---
    const inputElement = document.querySelector('input[type="file"]');
    if (window.FilePond && inputElement) {
        const pond = FilePond.create(inputElement);
        window.pond = pond;
        FilePond.setOptions({
            server: '/api/upload-media',
            name: 'file',
        });
        pond.on('processfile', (error, file) => {
            if (error) { console.error('FilePond server error:', error); return; }
            const response = JSON.parse(file.serverId);
            uploadedFileUrl = response.secure_url;
        });
    }

    // --- Main Data Loading Function (UPDATED) ---
    async function loadBotData() {
        if (!botId) return;
        try {
            const response = await fetch(`/api/bots/${botId}`);
            const bot = await handleApiError(response);
            if (bot) {
                pageTitle.textContent = `Manage Bot (...${bot.id.slice(-6)})`;
                if (viewOrdersLink) viewOrdersLink.href = `/orders/${bot.id}`;
                welcomeMessageTextarea.value = bot.welcome_message;
                renderCategoryTree(bot.categories);
                renderAllProducts(bot.categories);
            }
        } catch (error) {
            console.error('Failed to load bot data:', error);
        }
    }

    // --- Rendering Functions (UNCHANGED) ---
    function renderCategoryTree(categories) {
        categoryManagerDiv.innerHTML = '';
        productCategorySelect.innerHTML = '<option value="">-- Select a Category --</option>';
        if (categories.length === 0) {
            if (noCategoriesMessage) {
                noCategoriesMessage.style.display = 'block';
                categoryManagerDiv.appendChild(noCategoriesMessage);
            }
        } else {
            if (noCategoriesMessage) noCategoriesMessage.style.display = 'none';
            categories.forEach(category => {
                const categoryElement = createCategoryElement(category);
                categoryManagerDiv.appendChild(categoryElement);
                addCategoryToSelect(category, 0);
            });
        }
    }

    function createCategoryElement(category, level = 0) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-node';
        categoryDiv.style.marginLeft = `${level * 25}px`;
        categoryDiv.innerHTML = `
            <div class="category-header">
                <span class="category-name">${category.name}</span>
                <button class="delete-category-btn" data-id="${category.id}">&times;</button>
            </div>
            <form class="sub-category-form">
                <input type="text" placeholder="New sub-category name" required>
                <button type="submit">Add</button>
            </form>
            <div class="sub-category-list"></div>
        `;
        const subCategoryList = categoryDiv.querySelector('.sub-category-list');
        category.sub_categories.forEach(sub => {
            subCategoryList.appendChild(createCategoryElement(sub, level + 1));
        });
        categoryDiv.querySelector('.delete-category-btn').addEventListener('click', () => deleteCategory(category.id, category.name));
        categoryDiv.querySelector('.sub-category-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const input = e.target.querySelector('input');
            createSubCategory(input.value, category.id);
            input.value = '';
        });
        return categoryDiv;
    }

    function addCategoryToSelect(category, level) {
        const prefix = '- '.repeat(level);
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = `${prefix}${category.name}`;
        productCategorySelect.appendChild(option);
        category.sub_categories.forEach(sub => addCategoryToSelect(sub, level + 1));
    }

    function renderAllProducts(categories) {
        productListDisplayDiv.innerHTML = '';
        let hasProducts = false;
        categories.forEach(category => {
            const productElements = renderProductsForCategory(category);
            if (productElements) {
                productListDisplayDiv.appendChild(productElements);
                hasProducts = true;
            }
        });
        if (!hasProducts) {
            productListDisplayDiv.innerHTML = '<p>No products added yet.</p>';
        }
    }

    function renderProductsForCategory(category) {
        if (category.products.length === 0 && category.sub_categories.length === 0) return null;
        const categorySection = document.createElement('div');
        categorySection.className = 'product-category-section';
        const categoryTitle = document.createElement('h4');
        categoryTitle.textContent = category.name;
        categorySection.appendChild(categoryTitle);
        category.products.forEach(product => {
            const productItem = document.createElement('div');
            productItem.className = 'product-item-manage';
            productItem.innerHTML = `
                <span class="product-name-manage">${product.name}</span>
                <div class="product-actions-manage">
                    <button class="btn-secondary btn-small manage-pricing-btn">Manage Pricing</button>
                    <button class="delete-btn btn-small delete-product-btn">Delete Product</button>
                </div>
            `;
            productItem.querySelector('.manage-pricing-btn').addEventListener('click', () => {
                openPriceTierModal(product.id, product.name, product.price_tiers);
            });
            productItem.querySelector('.delete-product-btn').addEventListener('click', () => {
                deleteProduct(product.id, product.name);
            });
            categorySection.appendChild(productItem);
        });
        category.sub_categories.forEach(subCategory => {
            const subCategoryElements = renderProductsForCategory(subCategory);
            if (subCategoryElements) {
                subCategoryElements.style.marginLeft = '20px';
                categorySection.appendChild(subCategoryElements);
            }
        });
        return categorySection;
    }

    function openPriceTierModal(productId, productName, tiers) {
        currentProductIdForTiers = productId;
        priceTierTitle.textContent = `Manage Pricing for: ${productName}`;
        existingTiersList.innerHTML = '';
        if (tiers && tiers.length > 0) {
            tiers.forEach(tier => {
                const tierEl = document.createElement('div');
                tierEl.className = 'price-tier-item';
                tierEl.innerHTML = `
                    <span>${tier.label} - £${tier.price.toFixed(2)}</span>
                    <button class="delete-tier-btn" data-id="${tier.id}">&times;</button>
                `;
                tierEl.querySelector('.delete-tier-btn').addEventListener('click', () => deletePriceTier(tier.id, tier.label));
                existingTiersList.appendChild(tierEl);
            });
        } else {
            existingTiersList.innerHTML = '<p>No price options added yet.</p>';
        }
        priceTierModal.classList.remove('hidden');
    }

    // --- API Call Functions (All UPDATED) ---
    async function deleteCategory(categoryId, categoryName) {
        if (confirm(`Are you sure you want to delete "${categoryName}" and all its contents?`)) {
            try {
                const response = await fetch(`/api/categories/${categoryId}`, { method: 'DELETE' });
                const success = await handleApiError(response);
                if (success) {
                    loadBotData();
                }
            } catch (error) { console.error(error); }
        }
    }

    async function createSubCategory(name, parentId) {
        try {
            const response = await fetch(`/api/bots/${botId}/categories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, parent_id: parentId })
            });
            const result = await handleApiError(response);
            if (result) {
                loadBotData();
            }
        } catch (error) { console.error(error); }
    }

    async function deletePriceTier(tierId, tierLabel) {
        if (confirm(`Are you sure you want to delete the price option "${tierLabel}"?`)) {
            try {
                const response = await fetch(`/api/price-tiers/${tierId}`, { method: 'DELETE' });
                const success = await handleApiError(response);
                if (success) {
                    loadBotData(); // Reload all data to refresh the modal state
                }
            } catch (error) { console.error(error); }
        }
    }

    async function deleteProduct(productId, productName) {
        if (confirm(`Are you sure you want to delete the product "${productName}"?`)) {
            try {
                const response = await fetch(`/api/products/${productId}`, { method: 'DELETE' });
                const success = await handleApiError(response);
                if (success) {
                    loadBotData();
                }
            } catch (error) { console.error(error); }
        }
    }

    // --- Event Listeners (All UPDATED) ---
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('userId');
            window.location.href = '/';
        });
    }

    if (welcomeMessageForm) {
        welcomeMessageForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch(`/api/bots/${botId}/welcome-message`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: welcomeMessageTextarea.value })
                });
                const result = await handleApiError(response);
                if (result) alert('Welcome message saved!');
            } catch (error) { console.error(error); }
        });
    }
    
    if (addMainCategoryForm) {
        addMainCategoryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('main-category-name');
            try {
                const response = await fetch(`/api/bots/${botId}/categories`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: input.value, parent_id: null })
                });
                const result = await handleApiError(response);
                if (result) {
                    input.value = '';
                    loadBotData();
                }
            } catch (error) { console.error(error); }
        });
    }

    if (addProductForm) {
        addProductForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const productData = {
                category_id: document.getElementById('product-category').value,
                name: document.getElementById('product-name').value,
                description: document.getElementById('product-description').value,
                unit: document.getElementById('product-unit').value,
                image_url: uploadedFileUrl,
            };
            try {
                const response = await fetch(`/api/bots/${botId}/products`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(productData)
                });
                const newProduct = await handleApiError(response);
                if (newProduct) {
                    addProductForm.reset();
                    if (window.pond) pond.removeFiles();
                    uploadedFileUrl = null;
                    openPriceTierModal(newProduct.id, newProduct.name, []);
                    loadBotData();
                }
            } catch (error) { console.error(error); }
        });
    }

    if (addPriceTierForm) {
        addPriceTierForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const tierData = {
                label: document.getElementById('tier-label').value,
                price: document.getElementById('tier-price').value
            };
            try {
                const response = await fetch(`/api/products/${currentProductIdForTiers}/price-tiers`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(tierData)
                });
                const newTier = await handleApiError(response);
                if (newTier) {
                    addPriceTierForm.reset();
                    // Just reload all data to ensure modal is fresh
                    loadBotData(); 
                }
            } catch (error) { console.error(error); }
        });
    }

    if (closePriceModalButton) {
        closePriceModalButton.addEventListener('click', () => {
            priceTierModal.classList.add('hidden');
        });
    }

    // --- Initial Load ---
    loadBotData();
});