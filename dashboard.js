document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin Dashboard Script Loaded."); // DEBUG: Check if script is running

    const logoutButton = document.getElementById('admin-logout-button');
    const createUserForm = document.getElementById('create-user-form');
    const userListDiv = document.getElementById('user-list');
    const noUsersMessage = document.getElementById('no-users-message');

    // --- Logout Logic ---
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            window.location.href = '/admin';
        });
    } else {
        console.error("Logout button not found!"); // DEBUG
    }

    // --- Functions ---
    function renderUser(user) {
        if (noUsersMessage) {
            noUsersMessage.style.display = 'none';
        }
        const userItem = document.createElement('div');
        userItem.className = 'user-item';
        userItem.innerHTML = `
            <span class="user-email">${user.email}</span>
            <span class="user-bot-count">${user.bots.length} bots</span>
        `;
        userListDiv.appendChild(userItem);
    }

    async function fetchAndDisplayUsers() {
        console.log("Fetching users..."); // DEBUG
        try {
            const response = await fetch('/api/admin/users');
            if (response.ok) {
                const users = await response.json();
                console.log("Users received:", users); // DEBUG
                userListDiv.innerHTML = ''; 
                if (users.length === 0 && noUsersMessage) {
                    noUsersMessage.style.display = 'block';
                }
                users.forEach(user => renderUser(user));
            } else {
                console.error("Failed to fetch users. Status:", response.status); // DEBUG
            }
        } catch (error) {
            console.error('Failed to fetch users:', error);
        }
    }

    // --- Event Listeners & Initial Load ---
    if (createUserForm) {
        console.log("Create user form found. Attaching event listener."); // DEBUG
        createUserForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            console.log("Create User form submitted."); // DEBUG

            const emailInput = document.getElementById('user-email');
            const passwordInput = document.getElementById('user-password');

            try {
                const response = await fetch('/api/admin/users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: emailInput.value,
                        password: passwordInput.value
                    })
                });

                if (response.ok) {
                    const newUser = await response.json();
                    renderUser(newUser);
                    createUserForm.reset();
                } else {
                    const error = await response.json();
                    alert(`Error: ${error.message}`);
                    console.error("Error creating user:", error.message); // DEBUG
                }
            } catch (error) {
                console.error("A network error occurred while creating user:", error); // DEBUG
            }
        });
    } else {
        console.error("Create user form not found!"); // DEBUG
    }

    // Load all users when the page opens
    fetchAndDisplayUsers();
});
