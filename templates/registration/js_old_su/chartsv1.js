// Authentication Functions

// Función para guardar el token en localStorage
function saveAuthData(token, username) {
    localStorage.setItem('access_token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('login_time', new Date().toISOString());
}

// Función para eliminar los datos de autenticación
function clearAuthData() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    localStorage.removeItem('login_time');
}

// Función para obtener información del usuario
function getUserInfo() {
    return {
        username: localStorage.getItem('username'),
        loginTime: localStorage.getItem('login_time')
    };
}

// Función para verificar si el usuario está autenticado
function isAuthenticated() {
    const token = localStorage.getItem('access_token');
    if (!token) return false;
    
    // Verificar expiración básica (opcional, el backend debe manejar la expiración)
    const loginTime = localStorage.getItem('login_time');
    if (loginTime) {
        const loginDate = new Date(loginTime);
        const now = new Date();
        const hoursDiff = (now - loginDate) / (1000 * 60 * 60);
        
        // Si han pasado más de 24 horas, considerar expirado
        if (hoursDiff > 24) {
            clearAuthData();
            return false;
        }
    }
    
    return true;
}

// Función para realizar login
async function login(username, password) {
    try {
        const response = await fetch('/api/token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            saveAuthData(data.access, username);
            showDashboard();
            loadDashboardData();
            showNotification('Login exitoso', 'success');
            return true;
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error de autenticación');
        }
    } catch (error) {
        console.error('Error en login:', error);
        showNotification(error.message || 'Error en las credenciales', 'danger');
        return false;
    }
}

// Función para realizar logout
function logout() {
    clearAuthData();
    showLogin();
    showNotification('Sesión cerrada correctamente', 'info');
}

// Función para mostrar la pantalla de login
function showLogin() {
    toggleElement('login-section', true);
    toggleElement('dashboard-section', false);
    // Limpiar formulario de login
    document.getElementById('login-form').reset();
}

// Función para mostrar el dashboard
function showDashboard() {
    const userInfo = getUserInfo();
    if (userInfo.username) {
        document.getElementById('user-name').textContent = userInfo.username;
    }
    toggleElement('login-section', false);
    toggleElement('dashboard-section', true);
}

// Función para mostrar/ocultar elementos
function toggleElement(id, show) {
    const element = document.getElementById(id);
    if (show) {
        element.classList.remove('hidden');
    } else {
        element.classList.add('hidden');
    }
}

// Exportar funciones para uso global
window.Auth = {
    login,
    logout,
    showLogin,
    showDashboard,
    isAuthenticated,
    getUserInfo,
    toggleElement
};