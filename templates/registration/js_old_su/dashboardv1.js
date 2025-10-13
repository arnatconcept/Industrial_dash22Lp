// Dashboard Management

let dataRefreshInterval;

// Cargar datos del dashboard
async function loadDashboardData() {
    try {
        showLoadingStates();
        
        // Cargar KPIs principales
        await loadKPIData();
        
        // Cargar datos de gráficos
        await loadChartsData();
        
        // Cargar actividades recientes
        await loadRecentActivities();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        API.showNotification('Error al cargar los datos del dashboard', 'danger');
    }
}

// Cargar datos de KPIs
async function loadKPIData() {
    try {
        const kpiData = await API.fetchData('/dashboard/eficiencia-general/');
        if (kpiData) {
            updateKPIDisplay(kpiData);
        }
    } catch (error) {
        console.error('Error loading KPI data:', error);
    }
}

// Actualizar visualización de KPIs
function updateKPIDisplay(kpiData) {
    // Unidades producidas
    if (kpiData.totales?.unidades_producidas !== undefined) {
        document.getElementById('kpi-unidades').textContent = API.formatNumber(kpiData.totales.unidades_producidas);
    }
    
    // Eficiencia general
    if (kpiData.totales?.eficiencia_general_porcentaje !== undefined) {
        document.getElementById('kpi-eficiencia').textContent = kpiData.totales.eficiencia_general_porcentaje.toFixed(1) + '%';
    }
    
    // Tiempo de paradas
    if (kpiData.totales?.paradas !== undefined) {
        document.getElementById('kpi-paradas').textContent = API.formatNumber(kpiData.totales.paradas);
    }
    
    // Fallas activas (cargar desde endpoint específico)
    loadFallasData();
}

// Cargar datos de fallas
async function loadFallasData() {
    try {
        const fallasData = await API.fetchData('/dashboard/fallas-activas/');
        if (fallasData) {
            document.getElementById('kpi-fallas').textContent = fallasData.total || 0;
        }
    } catch (error) {
        console.error('Error loading fallas data:', error);
    }
}

// Cargar datos para gráficos
async function loadChartsData() {
    try {
        // Producción por línea
        const produccionData = await API.fetchData('/reportes/produccion/');
        if (produccionData && produccionData.por_linea) {
            Charts.updateProductionChart(produccionData.por_linea);
        }
        
        // Distribución de paradas
        const paradasData = await API.fetchData('/reportes/paradas/');
        if (paradasData && paradasData.por_tipo) {
            Charts.updateDowntimeChart(paradasData.por_tipo);
        }
        
    } catch (error) {
        console.error('Error loading charts data:', error);
    }
}

// Cargar actividades recientes
async function loadRecentActivities() {
    try {
        // Paradas recientes
        const paradasData = await API.fetchData('/reportes/paradas-recientes/');
        if (paradasData) {
            updateRecentDowntimes(paradasData);
        }
        
        // Fallas recientes
        const fallasData = await API.fetchData('/reportes/fallas-recientes/');
        if (fallasData) {
            updateRecentFailures(fallasData);
        }
        
    } catch (error) {
        console.error('Error loading recent activities:', error);
    }
}

// Actualizar lista de fallas recientes
function updateRecentFailures(failures) {
    const container = document.getElementById('recent-failures');
    
    if (!failures || failures.length === 0) {
        container.innerHTML = '<div class="text-center py-3 text-muted">No hay fallas recientes</div>';
        return;
    }
    
    let html = '';
    failures.slice(0, 3).forEach(failure => {
        const severityClass = failure.severidad === 'critica' ? 'bg-danger' : 
                            failure.severidad === 'alta' ? 'bg-warning' : 'bg-info';
        
        html += `
            <div class="list-group-item recent-item">
                <div class="d-flex justify-content-between">
                    <h6 class="mb-1">${failure.codigo || 'Falla sin código'}</h6>
                    <span class="status-badge ${severityClass}">${failure.severidad || 'media'}</span>
                </div>
                <p class="mb-1">${failure.descripcion || 'Sin descripción'}</p>
                <small class="text-muted">
                    <i class="fas fa-history me-1"></i> Detectada: ${API.formatDate(failure.timestamp)}
                </small>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Actualizar lista de paradas recientes
function updateRecentDowntimes(downtimes) {
    const container = document.getElementById('recent-downtimes');
    
    if (!downtimes || downtimes.length === 0) {
        container.innerHTML = '<div class="text-center py-3 text-muted">No hay paradas recientes</div>';
        return;
    }
    
    let html = '';
    downtimes.slice(0, 3).forEach(downtime => {
        html += `
            <div class="list-group-item recent-item">
                <div class="d-flex justify-content-between">
                    <h6 class="mb-1">${downtime.tipo || 'Tipo no especificado'}</h6>
                    <small class="text-muted">${downtime.cantidad || 0} ocurrencias</small>
                </div>
                <p class="mb-1">Duración total: ${downtime.duracion || 0} minutos</p>
                <small class="text-muted">
                    <i class="fas fa-clock me-1"></i> Última: ${API.formatDate(downtime.ultima_actualizacion)}
                </small>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Mostrar estados de carga
function showLoadingStates() {
    // Mostrar spinners en las listas recientes
    const downtimesContainer = document.getElementById('recent-downtimes');
    const failuresContainer = document.getElementById('recent-failures');
    
    const spinner = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div></div>';
    
    downtimesContainer.innerHTML = spinner;
    failuresContainer.innerHTML = spinner;
}

// Configurar eventos del dashboard
function setupDashboardEvents() {
    // Evento de logout
    document.getElementById('logout-btn').addEventListener('click', function(e) {
        e.preventDefault();
        Auth.logout();
    });
    
    // Eventos de filtros
    document.querySelectorAll('.filter-bar .btn-group .btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remover clase active de todos los botones del grupo
            this.parentElement.querySelectorAll('.btn').forEach(b => {
                b.classList.remove('active');
            });
            // Agregar clase active al botón clickeado
            this.classList.add('active');
            
            // Recargar datos con nuevo filtro
            loadDashboardData();
        });
    });
    
    // Eventos de dropdown de líneas
    document.querySelectorAll('.filter-bar .dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const lineName = this.textContent;
            const dropdownToggle = this.closest('.dropdown-menu').previousElementSibling;
            dropdownToggle.innerHTML = `<i class="fas fa-filter me-1"></i> Línea: ${lineName}`;
            
            // Recargar datos con nueva línea seleccionada
            loadDashboardData();
        });
    });
}

// Inicializar dashboard
function initializeDashboard() {
    if (!Auth.isAuthenticated()) {
        Auth.showLogin();
        return;
    }
    
    Auth.showDashboard();
    Charts.initializeCharts();
    setupDashboardEvents();
    loadDashboardData();
    
    // Configurar actualización periódica de datos (cada 5 minutos)
    dataRefreshInterval = setInterval(loadDashboardData, 300000);
}

// Limpiar recursos del dashboard
function cleanupDashboard() {
    if (dataRefreshInterval) {
        clearInterval(dataRefreshInterval);
        dataRefreshInterval = null;
    }
    Charts.destroyCharts();
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Configurar evento de login
    document.getElementById('login-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        const success = await Auth.login(username, password);
        if (success) {
            document.getElementById('login-error').classList.add('hidden');
        } else {
            document.getElementById('login-error').classList.remove('hidden');
        }
    });
    
    // Verificar autenticación al cargar
    if (Auth.isAuthenticated()) {
        initializeDashboard();
    } else {
        Auth.showLogin();
    }
});

// Exportar funciones para uso global
window.Dashboard = {
    initializeDashboard,
    loadDashboardData,
    cleanupDashboard
};