// API Configuration
const API_BASE_URL = '/api';

// Función para obtener datos de la API
async function fetchData(endpoint) {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            throw new Error('No authentication token found');
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.status === 401) {
            // Token inválido o expirado
            clearAuthData();
            showLogin();
            throw new Error('Authentication failed');
        }
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching data from', endpoint, ':', error);
        showNotification('Error al cargar los datos', 'danger');
        return null;
    }
}

// Función para realizar peticiones POST
async function postData(endpoint, data) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.status === 401) {
            clearAuthData();
            showLogin();
            throw new Error('Authentication failed');
        }
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error posting data to', endpoint, ':', error);
        showNotification('Error al enviar los datos', 'danger');
        return null;
    }
}

// Función para formatear números con separadores de miles
function formatNumber(num) {
    return new Intl.NumberFormat('es-ES').format(num);
}

// Función para formatear fechas
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 1050;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Agregar al documento
    document.body.appendChild(notification);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Exportar funciones para uso global
window.API = {
    fetchData,
    postData,
    formatNumber,
    formatDate,
    showNotification
};