document.addEventListener('DOMContentLoaded', () => {
    console.log("DEBUG: manage.js script has started.");

    // --- Get all necessary elements ---
    const addProductForm = document.getElementById('add-product-form');
    console.log("DEBUG: addProductForm element:", addProductForm); // Check if the form is found

    // --- Event Listeners ---
    if (addProductForm) {
        console.log("DEBUG: Attaching event listener to the product form.");
        addProductForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log("DEBUG: 'Save Product & Add Pricing' button was clicked.");

            try {
                const categoryId = document.getElementById('product-category').value;
                const productName = document.getElementById('product-name').value;
                const productDesc = document.getElementById('product-description').value;
                const productUnit = document.getElementById('product-unit').value;
                const imageUrl = document.getElementById('product-image-url') ? document.getElementById('product-image-url').value : null;
                const videoUrl = document.getElementById('product-video-url') ? document.getElementById('product-video-url').value : null;

                console.log("DEBUG: Form data collected:", { categoryId, productName });

                const productData = {
                    category_id: categoryId,
                    name: productName,
                    description: productDesc,
                    unit: productUnit,
                    image_url: uploadedFileUrl || imageUrl, // Use uploaded file first
                    video_url: videoUrl,
                };

                console.log("DEBUG: Sending data to server:", productData);

                const response = await fetch(`/api/bots/${botId}/products`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(productData)
                });

                console.log("DEBUG: Received response from server with status:", response.status);

                if (response.ok) {
                    const newProduct = await response.json();
                    console.log("DEBUG: Product created successfully:", newProduct);
                    addProductForm.reset();
                    if (window.pond) pond.removeFiles();
                    uploadedFileUrl = null;
                    openPriceTierModal(newProduct.id, newProduct.name, []);
                    loadBotData();
                } else {
                    const error = await response.json();
                    console.error("DEBUG: Server responded with an error:", error.message);
                    alert(`Failed to add product: ${error.message}`);
                }
            } catch (error) {
                console.error("DEBUG: A critical JavaScript error occurred:", error);
                alert("A critical error occurred. Please check the console.");
            }
        });
    } else {
        console.error("DEBUG: CRITICAL ERROR - Could not find the add-product-form!");
    }

    // --- All other functions from the file go here ---
    // (I have included the full file content below for simplicity)

    const pageTitle = document.getElementById('manage-bot-title');
    const viewOrdersLink = document.getElementById('view-orders-link');
    const welcomeMessageForm = document.getElementById('welcome-message-form');
    const welcomeMessageTextarea = document.getElementById('welcome-message');
    const categoryManagerDiv = document.getElementById('category-manager');
    const noCategoriesMessage = document.getElementById('no-categories-message');
    const addMainCategoryForm = document.getElementById('add-main-category-form');
    const productCategorySelect = document.getElementById('product-category');
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

    // Initialize FilePond if it exists
    const inputElement = document.querySelector('input[type="file"]');
    if (window.FilePond && inputElement) {
        const pond = FilePond.create(inputElement);
        window.pond = pond; // Make it globally accessible for clearing
        FilePond.setOptions({
            server: '/api/upload-media',
            name: 'file',
        });
        pond.on('processfile', (error, file) => {
            if (error) {
                console.error('FilePond server error:', error);
                return;
            }
            const response = JSON.parse(file.serverId);
            uploadedFileUrl = response.secure_url;
        });
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('userId');
            window.location.href = '/';
        });
    }

    async function loadBotData() {
        if (!botId) return;
        try {
            const response = await fetch(`/api/bots/${botId}`);
            if (!response.ok) return;
            const bot = await response.json();
            pageTitle.textContent = `Manage Bot (...${bot.id.slice(-6)})`;
            if (viewOrdersLink) viewOrdersLink.href = `/orders/${bot.id}`;
            welcomeMessageTextarea.value = bot.welcome_message;
            renderCategoryTree(bot.categories);
            renderAllProducts(bot.categories);
        } catch (error) {
            console.error('Failed to load bot data:', error);
        }
    }

    function renderCategoryTree(categories) {
        categoryManagerDiv.innerHTML = '';
        productCategorySelect.innerHTML = '<option value="">-- Select a Category --</option>';
        if (categories.length === 0) {
            if(noCategoriesMessage) categoryManagerDiv.appendChild(noCategoriesMessage);
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
                tierEl.querySelector('.delete-tier-btn').addEventListener('click', () => deletePriceTier(tier.id, tier.label, tierEl));
                existingTiersList.appendChild(tierEl);
            });
        } else {
            existingTiersList.innerHTML = '<p>No price options added yet.</p>';
        }
        priceTierModal.classList.remove('hidden');
    }

    async function deleteCategory(categoryId, categoryName) {
        if (confirm(`Are you sure you want to delete "${categoryName}" and all its contents?`)) {
            await fetch(`/api/categories/${categoryId}`, { method: 'DELETE' });
            loadBotData();
        }
    }

    async function createSubCategory(name, parentId) {
        await fetch(`/api/bots/${botId}/categories`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, parent_id: parentId })
        });
        loadBotData();
    }

    async function deletePriceTier(tierId, tierLabel, elementToRemove) {
        if (confirm(`Are you sure you want to delete the price option "${tierLabel}"?`)) {
            const response = await fetch(`/api/price-tiers/${tierId}`, { method: 'DELETE' });
            if (response.ok) {
                elementToRemove.remove();
            } else {
                alert('Failed to delete price option.');
            }
        }
    }

    async function deleteProduct(productId, productName) {
        if (confirm(`Are you sure you want to delete the product "${productName}"?`)) {
            const response = await fetch(`/api/products/${productId}`, { method: 'DELETE' });
            if (response.ok) {
                loadBotData();
            } else {
                alert('Failed to delete product.');
            }
        }
    }

    if (welcomeMessageForm) {
        welcomeMessageForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const response = await fetch(`/api/bots/${botId}/welcome-message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: welcomeMessageTextarea.value })
            });
            alert(response.ok ? 'Welcome message saved!' : 'Failed to save message.');
        });
    }
    
    if (addMainCategoryForm) {
        addMainCategoryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('main-category-name');
            await fetch(`/api/bots/${botId}/categories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: input.value, parent_id: null })
            });
            input.value = '';
            loadBotData();
        });
    }

    if (addPriceTierForm) {
        addPriceTierForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const tierData = {
                label: document.getElementById('tier-label').value,
                price: document.getElementById('tier-price').value
            };
            const response = await fetch(`/api/products/${currentProductIdForTiers}/price-tiers`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(tierData)
            });
            if (response.ok) {
                addPriceTierForm.reset();
                const newTier = await response.json();
                const tierEl = document.createElement('div');
                tierEl.className = 'price-tier-item';
                tierEl.innerHTML = `
                    <span>${newTier.label} - £${newTier.price.toFixed(2)}</span>
                    <button class="delete-tier-btn" data-id="${newTier.id}">&times;</button>
                `;
                tierEl.querySelector('.delete-tier-btn').addEventListener('click', () => deletePriceTier(newTier.id, newTier.label, tierEl));
                if (existingTiersList.querySelector('p')) {
                    existingTiersList.innerHTML = '';
                }
                existingTiersList.appendChild(tierEl);
            } else {
                alert('Failed to add price option.');
            }
        });
    }

    if(closePriceModalButton) {
        closePriceModalButton.addEventListener('click', () => {
            priceTierModal.classList.add('hidden');
            loadBotData();
        });
    }

    loadBotData();
});
