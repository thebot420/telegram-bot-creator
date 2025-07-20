document.addEventListener('DOMContentLoaded', () => {
    const logoutButton = document.getElementById('admin-logout-button');
    const createUserForm = document.getElementById('create-user-form');
    const userListDiv = document.getElementById('user-list');
    const noUsersMessage = document.getElementById('no-users-message');

    // --- Logout Logic ---
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            window.location.href = '/admin';
        });
    }

    // --- Functions ---

    // Replace the old renderUser function with this one
    function renderUser(user) {
    if (noUsersMessage) {
        noUsersMessage.style.display = 'none';
    }

    const userItem = document.createElement('div');
    userItem.className = 'user-item';
    userItem.innerHTML = `
        <div class="user-info">
            <span class="user-email">${user.email}</span>
            <span class="user-bot-count">${user.bots.length} bots</span>
        </div>
        <button class="delete-btn" data-id="${user.id}">Delete</button>
    `;

    // Add click event listener for the new delete button
    const deleteButton = userItem.querySelector('.delete-btn');
    deleteButton.addEventListener('click', async () => {
        if (confirm(`Are you sure you want to delete the user ${user.email}? All of their bots will also be deleted.`)) {
            const response = await fetch(`/api/admin/users/${user.id}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                userItem.remove(); // Remove the user from the list on the page
            } else {
                alert('Failed to delete user.');
            }
        }
    });

    userListDiv.appendChild(userItem);
}



    
    async function fetchAndDisplayUsers() {
        try {
            const response = await fetch('/api/admin/users');
            if (response.ok) {
                const users = await response.json();
                userListDiv.innerHTML = ''; // Clear the list first
                if (users.length === 0 && noUsersMessage) {
                    noUsersMessage.style.display = 'block';
                }
                users.forEach(user => renderUser(user));
            }
        } catch (error) {
            console.error('Failed to fetch users:', error);
        }
    }

    // --- Event Listeners & Initial Load ---
    if (createUserForm) {
        createUserForm.addEventListener('submit', async (event) => {
            event.preventDefault();
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
                }
            } catch (error) {
                console.error("A network error occurred:", error);
                alert("A network error occurred. Please check the console.");
            }
        });
    }

    // Load all users when the page opens
    fetchAndDisplayUsers();
});
