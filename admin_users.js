document.addEventListener('DOMContentLoaded', () => {
    const logoutButton = document.getElementById('admin-logout-button');
    const createUserForm = document.getElementById('create-user-form');
    const userListDiv = document.getElementById('user-list');
    const noUsersMessage = document.getElementById('no-users-message');

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            window.location.href = '/admin';
        });
    }

    function renderUser(user) {
        if (noUsersMessage) {
            noUsersMessage.style.display = 'none';
        }
        const userItem = document.createElement('div');
        userItem.className = 'user-item clickable';
        userItem.innerHTML = `
            <a href="/admin/users/${user.id}" class="user-info-link">
                <div class="user-info">
                    <span class="user-email">${user.email}</span>
                    <span class="user-bot-count">${user.bots.length} bots</span>
                </div>
            </a>
            <button class="delete-btn" data-id="${user.id}">Delete</button>
        `;

        const deleteButton = userItem.querySelector('.delete-btn');
        deleteButton.addEventListener('click', async (event) => {
            event.stopPropagation();
            if (confirm(`Are you sure you want to delete the user ${user.email}?`)) {
                const response = await fetch(`/api/admin/users/${user.id}`, { method: 'DELETE' });
                if (response.ok) {
                    userItem.remove();
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
                userListDiv.innerHTML = '';
                if (users.length === 0 && noUsersMessage) {
                    noUsersMessage.style.display = 'block';
                } else if (noUsersMessage) {
                    noUsersMessage.style.display = 'none';
                }
                users.forEach(user => renderUser(user));
            }
        } catch (error) {
            console.error('Failed to fetch users:', error);
        }
    }

    if (createUserForm) {
        createUserForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const emailInput = document.getElementById('user-email');
            const passwordInput = document.getElementById('user-password');
            const response = await fetch('/api/admin/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: emailInput.value, password: passwordInput.value })
            });
            if (response.ok) {
                const newUser = await response.json();
                renderUser(newUser);
                createUserForm.reset();
            } else {
                const error = await response.json();
                alert(`Error: ${error.message}`);
            }
        });
    }

    fetchAndDisplayUsers();
});
