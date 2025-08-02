document.addEventListener('DOMContentLoaded', () => {
    // --- Get all necessary elements ---
    const pageTitle = document.getElementById('manage-bot-title');
    const viewOrdersLink = document.getElementById('view-orders-link');
    const welcomeMessageForm = document.getElementById('welcome-message-form');
    const welcomeMessageTextarea = document.getElementById('welcome-message');
    const categoryManagerDiv = document.getElementById('category-manager');
    const noCategoriesMessage = document.getElementById('no-categories-message');
    const addMainCategoryForm = document.getElementById('add-main-category-form');
    const addProductForm = document.getElementById('add-product-form');
    const productCategorySelect = document.getElementById('product-category');
    const logoutButton = document.getElementById('logout-button');

    const pathParts = window.location.pathname.split('/');
    const botId = pathParts[pathParts.length - 1];

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('userId');
            window.location.href = '/';
        });
    }

    // --- Main Data Loading Function ---
    async function loadBotData() {
        if (!botId) return;
        try {
            const response = await fetch(`/api/bots/${botId}`);
            if (!response.ok) return;
            const bot = await response.json();
            
            pageTitle.textContent = `Manage Bot (...${bot.id.slice(-6)})`;
            if (viewOrdersLink) viewOrdersLink.href = `/orders/${bot.id}`;
            welcomeMessageTextarea.value = bot.welcome_message;

            // Render the entire category tree
            renderCategoryTree(bot.categories);
        } catch (error) {
            console.error('Failed to load bot data:', error);
        }
    }

    // --- Category Rendering Functions ---
    function renderCategoryTree(categories) {
        categoryManagerDiv.innerHTML = ''; // Clear previous tree
        productCategorySelect.innerHTML = '<option value="">-- Select a Category --</option>';

        if (categories.length === 0) {
            categoryManagerDiv.appendChild(noCategoriesMessage);
            noCategoriesMessage.style.display = 'block';
        } else {
            if (noCategoriesMessage) noCategoriesMessage.style.display = 'none';
            categories.forEach(category => {
                const categoryElement = createCategoryElement(category);
                categoryManagerDiv.appendChild(categoryElement);
                addCategoryToSelect(category, 0); // Add to product dropdown
            });
        }
    }

    function createCategoryElement(category, level = 0) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-node';
        categoryDiv.style.marginLeft = `${level * 20}px`;

        const categoryHeader = document.createElement('div');
        categoryHeader.className = 'category-header';
        categoryHeader.innerHTML = `
            <span class="category-name">${category.name}</span>
            <button class="delete-category-btn" data-id="${category.id}">&times;</button>
        `;
        categoryDiv.appendChild(categoryHeader);

        const subCategoryForm = document.createElement('form');
        subCategoryForm.className = 'sub-category-form';
        subCategoryForm.innerHTML = `
            <input type="text" placeholder="New sub-category name" required>
            <button type="submit">Add</button>
        `;
        categoryDiv.appendChild(subCategoryForm);

        const subCategoryList = document.createElement('div');
        category.sub_categories.forEach(sub => {
            subCategoryList.appendChild(createCategoryElement(sub, level + 1));
        });
        categoryDiv.appendChild(subCategoryList);

        const deleteButton = categoryHeader.querySelector('.delete-category-btn');
        deleteButton.addEventListener('click', () => deleteCategory(category.id));

        subCategoryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = subCategoryForm.querySelector('input');
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

    // --- API Call Functions ---
    async function deleteCategory(categoryId) {
        if (confirm('Are you sure you want to delete this category and all its contents?')) {
            await fetch(`/api/categories/${categoryId}`, { method: 'DELETE' });
            loadBotData(); // Reload the whole tree
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

    // --- Form Event Listeners ---
    if (welcomeMessageForm) {
        welcomeMessageForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const response = await fetch(`/api/bots/${botId}/welcome-message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: welcomeMessageTextarea.value })
            });
            if (response.ok) {
                alert('Welcome message saved!');
            } else {
                alert('Failed to save message.');
            }
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

    if (addProductForm) {
        addProductForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const productData = {
                category_id: document.getElementById('product-category').value,
                name: document.getElementById('product-name').value,
                price: document.getElementById('product-price').value,
                unit: document.getElementById('product-unit').value,
                image_url: document.getElementById('product-image-url').value,
            };
            const response = await fetch(`/api/bots/${botId}/products`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData)
            });
            if (response.ok) {
                addProductForm.reset();
                alert('Product added successfully!');
            } else {
                alert('Failed to add product.');
            }
        });
    }

    // Initial load
    loadBotData();
});
