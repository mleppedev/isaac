/**
 * Data Event Manager - Javascript (versión básica sin WebSockets)
 * Maneja la interactividad de la interfaz web.
 */

// Variables globales
let allEvents = [];
let filteredEvents = [];
let currentPage = 1;
const perPage = 10;
let autoRefreshInterval = null;

// Cargar datos cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    // Cargar datos iniciales
    fetchEvents();
    
    // Asignar eventos a los elementos de la página
    const urlParams = new URLSearchParams(window.location.search);
    
    // Verificar si hay filtros en la URL
    if (urlParams.has('seed')) {
        const seedInput = document.getElementById('seed');
        if (seedInput) {
            seedInput.value = urlParams.get('seed');
        }
    }
    
    if (urlParams.has('type')) {
        const typeInput = document.getElementById('event-type');
        if (typeInput) {
            typeInput.value = urlParams.get('type');
        }
    }
    
    // Aplicar filtros si existen
    if (urlParams.has('seed') || urlParams.has('type')) {
        setTimeout(filterData, 500); // Dar tiempo a la carga de datos
    }
    
    // Configurar actualización automática cada 60 segundos
    setupAutoRefresh();
});

/**
 * Configurar actualización automática
 */
function setupAutoRefresh() {
    // Detener cualquier intervalo existente
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Crear un nuevo intervalo de actualización (cada 60 segundos)
    autoRefreshInterval = setInterval(function() {
        console.log('Actualizando datos automáticamente...');
        refreshData(true);
    }, 60000); // 60 segundos
    
    // Detener el intervalo cuando la ventana pierde el foco
    window.addEventListener('blur', function() {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    });
    
    // Reiniciar el intervalo cuando la ventana gana el foco
    window.addEventListener('focus', function() {
        if (!autoRefreshInterval) {
            setupAutoRefresh();
        }
    });
}

/**
 * Actualizar datos desde el servidor manualmente
 */
function refreshData(isAutomatic = false) {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn && !isAutomatic) {
        refreshBtn.disabled = true;
        refreshBtn.textContent = 'Actualizando...';
    }
    
    fetch('/api/refresh')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Si es actualización automática, no recargar la página completa
                if (isAutomatic) {
                    updateUIWithFreshData();
                } else {
                    // Recargar la página actual en actualizaciones manuales
                    window.location.reload();
                }
            } else {
                console.error('Error al actualizar los datos:', data.error);
                showNotification('Error al actualizar los datos: ' + data.error, 'error');
            }
            
            if (refreshBtn && !isAutomatic) {
                refreshBtn.disabled = false;
                refreshBtn.textContent = 'Actualizar Datos';
            }
        })
        .catch(error => {
            console.error('Error al actualizar los datos:', error);
            showNotification('Error al actualizar los datos: ' + error, 'error');
            
            if (refreshBtn && !isAutomatic) {
                refreshBtn.disabled = false;
                refreshBtn.textContent = 'Actualizar Datos';
            }
        });
}

/**
 * Actualizar la interfaz con datos frescos sin recargar la página
 */
function updateUIWithFreshData() {
    // Actualizar estadísticas
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            // Actualizar la información de última actualización
            const lastUpdatedElement = document.getElementById('last-updated');
            if (lastUpdatedElement && stats.latest_update) {
                const updateDate = stats.latest_update.split('T')[0];
                const updateTime = stats.latest_update.split('T')[1].substr(0, 8);
                lastUpdatedElement.textContent = `Última actualización: ${updateDate} ${updateTime}`;
            }
            
            // Actualizar contador de eventos
            const totalEventsElement = document.getElementById('total-events');
            if (totalEventsElement) {
                totalEventsElement.textContent = stats.total;
            }
            
            // Actualizar tipos de eventos (página principal)
            const eventTypesList = document.querySelector('.event-types ul');
            if (eventTypesList && stats.types && stats.types.length > 0) {
                let typeHtml = '';
                stats.types.slice(0, 5).forEach(type => {
                    typeHtml += `<li>${type.type}: ${type.count} (${type.percentage.toFixed(1)}%)</li>`;
                });
                eventTypesList.innerHTML = typeHtml;
            }
            
            // Actualizar partidas recientes
            updateRecentGames(stats);
            
            // Si estamos en la página de datos, actualizar los datos
            if (document.getElementById('events-body')) {
                fetchEvents();
            }
            
            // Si estamos en la página de estadísticas, es mejor recargar
            if (document.querySelector('.stats-grid')) {
                window.location.reload();
                return;
            }
            
            // Mostrar notificación
            showNotification('Datos actualizados automáticamente', 'success');
        })
        .catch(error => {
            console.error('Error al obtener estadísticas actualizadas:', error);
        });
}

/**
 * Muestra una notificación en la interfaz
 */
function showNotification(message, type = 'info') {
    // Verificar si ya existe un contenedor de notificaciones
    let notificationsContainer = document.getElementById('notifications-container');
    
    if (!notificationsContainer) {
        // Crear el contenedor si no existe
        notificationsContainer = document.createElement('div');
        notificationsContainer.id = 'notifications-container';
        document.body.appendChild(notificationsContainer);
    }
    
    // Crear la notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Agregar al contenedor
    notificationsContainer.appendChild(notification);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
}

/**
 * Actualiza la sección de partidas recientes
 */
function updateRecentGames(stats) {
    // Verificar si existe el contenedor de partidas recientes
    const recentGamesSection = document.querySelector('.recent-games');
    if (!recentGamesSection) return;
    
    // Verificar si hay datos de partidas para mostrar
    if (!stats.seeds || stats.seeds.length === 0) {
        recentGamesSection.style.display = 'none';
        return;
    }
    
    // Actualizar el título de la sección si no está visible
    if (recentGamesSection.style.display === 'none') {
        recentGamesSection.style.display = 'block';
        recentGamesSection.innerHTML = '<h3>Partidas Recientes</h3><div class="game-list"></div>';
    }
    
    // Obtener o crear el contenedor de la lista de partidas
    let gameList = recentGamesSection.querySelector('.game-list');
    if (!gameList) {
        gameList = document.createElement('div');
        gameList.className = 'game-list';
        recentGamesSection.appendChild(gameList);
    }
    
    // Generar HTML para cada partida
    let gamesHtml = '';
    stats.seeds.slice(0, 3).forEach(seed => {
        let typesHtml = '';
        seed.types.forEach(([type, count]) => {
            typesHtml += `<li>${type}: ${count}</li>`;
        });
        
        gamesHtml += `
            <div class="game-card">
                <h4>Partida (Seed: ${seed.seed})</h4>
                <p>${seed.count} eventos registrados</p>
                <div class="event-types">
                    <h5>Principales eventos:</h5>
                    <ul>${typesHtml}</ul>
                </div>
                <a href="/data?seed=${seed.seed}" class="btn">Ver Detalles</a>
            </div>
        `;
    });
    
    // Actualizar el contenido
    gameList.innerHTML = gamesHtml;
}

/**
 * Obtener todos los eventos 
 */
function fetchEvents() {
    const eventsBody = document.getElementById('events-body');
    if (!eventsBody) return Promise.resolve();
    
    // Actualizar indicador de carga
    eventsBody.innerHTML = '<tr><td colspan="6" class="loading">Cargando datos...</td></tr>';
    
    return fetch('/api/events')
        .then(response => response.json())
        .then(data => {
            allEvents = data;
            // Actualizar contador total en la página de datos si existe
            const totalCounter = document.getElementById('total-counter');
            if (totalCounter) {
                totalCounter.textContent = allEvents.length;
            }
            
            // Obtener los tipos de eventos y semillas únicas para los filtros
            if (document.getElementById('event-type')) {
                const eventTypes = [...new Set(allEvents.map(event => event.event_type))].sort();
                const eventTypeSelect = document.getElementById('event-type');
                
                // Guardar la selección actual
                const currentSelection = eventTypeSelect.value;
                
                // Reconstruir el dropdown manteniendo la opción seleccionada
                let optionsHtml = '<option value="">Todos los tipos</option>';
                eventTypes.forEach(type => {
                    const selected = type === currentSelection ? 'selected' : '';
                    optionsHtml += `<option value="${type}" ${selected}>${type}</option>`;
                });
                eventTypeSelect.innerHTML = optionsHtml;
            }
            
            // Actualizar lista de semillas si existe
            if (document.getElementById('seed')) {
                const seeds = [...new Set(allEvents.map(event => 
                    event.game_data && event.game_data.seed ? event.game_data.seed : null)
                )].filter(seed => seed !== null).sort((a, b) => a - b);
                
                const seedSelect = document.getElementById('seed');
                
                // Guardar la selección actual
                const currentSelection = seedSelect.value;
                
                // Reconstruir el dropdown manteniendo la opción seleccionada
                let optionsHtml = '<option value="">Todas las semillas</option>';
                seeds.forEach(seed => {
                    const selected = seed.toString() === currentSelection ? 'selected' : '';
                    optionsHtml += `<option value="${seed}" ${selected}>${seed}</option>`;
                });
                seedSelect.innerHTML = optionsHtml;
            }
            
            // Aplicar filtros y mostrar datos
            filterData();
            return data;
        })
        .catch(error => {
            console.error('Error al obtener los eventos:', error);
            if (eventsBody) {
                eventsBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="loading">Error al cargar los datos: ${error}</td>
                    </tr>
                `;
            }
            return Promise.reject(error);
        });
}

/**
 * Filtrar datos por tipo de evento y/o partida (seed)
 */
function filterData() {
    const eventType = document.getElementById('event-type')?.value || '';
    const seed = document.getElementById('seed')?.value || '';
    
    filteredEvents = allEvents.filter(event => {
        let matchType = true;
        let matchSeed = true;
        
        if (eventType && event.event_type !== eventType) {
            matchType = false;
        }
        
        if (seed && event.game_data?.seed != seed) {
            matchSeed = false;
        }
        
        return matchType && matchSeed;
    });
    
    // Ordenar por timestamp (más reciente primero)
    filteredEvents.sort((a, b) => b.timestamp - a.timestamp);
    
    // Actualizar URL con los filtros
    updateUrl(eventType, seed);
    
    // Mostrar datos
    currentPage = 1;
    displayEvents();
}

/**
 * Actualizar URL con filtros
 */
function updateUrl(eventType, seed) {
    const url = new URL(window.location.href);
    
    // Limpiar parámetros existentes
    url.searchParams.delete('type');
    url.searchParams.delete('seed');
    
    // Agregar nuevos parámetros si existen
    if (eventType) {
        url.searchParams.set('type', eventType);
    }
    
    if (seed) {
        url.searchParams.set('seed', seed);
    }
    
    // Actualizar URL sin recargar la página
    window.history.pushState({}, '', url);
}

/**
 * Mostrar eventos en la tabla
 */
function displayEvents() {
    const eventsBody = document.getElementById('events-body');
    if (!eventsBody) return;
    
    const start = (currentPage - 1) * perPage;
    const end = Math.min(start + perPage, filteredEvents.length);
    const eventsToDisplay = filteredEvents.slice(start, end);
    
    if (eventsToDisplay.length === 0) {
        eventsBody.innerHTML = `
            <tr>
                <td colspan="6" class="loading">No se encontraron eventos con los filtros seleccionados</td>
            </tr>
        `;
    } else {
        // Crear filas para cada evento
        const rows = eventsToDisplay.map((event, index) => {
            const eventId = event.event_id || `Evento ${index + 1}`;
            const eventType = event.event_type || 'Desconocido';
            const timestamp = event.timestamp || 0;
            const seed = event.game_data?.seed || 'N/A';
            const level = event.game_data?.level || 'N/A';
            
            // Convertir datos a JSON para mostrar
            let dataStr = JSON.stringify(event.data || {});
            if (dataStr.length > 50) {
                dataStr = dataStr.slice(0, 50) + '...';
            }
            
            return `
                <tr onclick="showEventDetails('${eventId}')">
                    <td>${eventId}</td>
                    <td>${eventType}</td>
                    <td>${timestamp}</td>
                    <td>${seed}</td>
                    <td>${level}</td>
                    <td>${dataStr}</td>
                </tr>
            `;
        });
        
        eventsBody.innerHTML = rows.join('');
    }
    
    // Actualizar paginación
    updatePagination();
}

/**
 * Actualizar controles de paginación
 */
function updatePagination() {
    const totalPages = Math.ceil(filteredEvents.length / perPage);
    const currentPageEl = document.getElementById('current-page');
    const totalPagesEl = document.getElementById('total-pages');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    
    if (currentPageEl && totalPagesEl) {
        currentPageEl.textContent = currentPage;
        totalPagesEl.textContent = totalPages;
    }
    
    if (prevBtn) {
        prevBtn.disabled = currentPage <= 1;
    }
    
    if (nextBtn) {
        nextBtn.disabled = currentPage >= totalPages;
    }
}

/**
 * Ir a la página anterior
 */
function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        displayEvents();
    }
}

/**
 * Ir a la página siguiente
 */
function nextPage() {
    const totalPages = Math.ceil(filteredEvents.length / perPage);
    if (currentPage < totalPages) {
        currentPage++;
        displayEvents();
    }
}

/**
 * Mostrar detalles de un evento
 */
function showEventDetails(eventId) {
    const event = allEvents.find(e => e.event_id === eventId);
    if (!event) return;
    
    const detailsEl = document.getElementById('event-details');
    const contentEl = detailsEl.querySelector('.detail-content');
    
    if (detailsEl && contentEl) {
        // Formatear datos del evento
        const eventData = formatEventData(event);
        
        // Mostrar datos en el panel de detalles
        contentEl.innerHTML = eventData;
        
        // Mostrar panel de detalles
        detailsEl.style.display = 'block';
        
        // Scroll al panel de detalles
        detailsEl.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Formatear datos de evento para mostrar en el panel de detalles
 */
function formatEventData(event) {
    // Datos básicos
    let html = `
        <div class="detail-section">
            <h4>Información Básica</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">ID:</span>
                    <span class="detail-value">${event.event_id || 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Tipo:</span>
                    <span class="detail-value">${event.event_type || 'Desconocido'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Timestamp:</span>
                    <span class="detail-value">${event.timestamp || 0}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Procesado:</span>
                    <span class="detail-value">${event.processed_timestamp || 'No procesado'}</span>
                </div>
            </div>
        </div>
    `;
    
    // Datos del juego
    if (event.game_data) {
        html += `
            <div class="detail-section">
                <h4>Datos del Juego</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">Seed:</span>
                        <span class="detail-value">${event.game_data.seed || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Nivel:</span>
                        <span class="detail-value">${event.game_data.level || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Tipo de Nivel:</span>
                        <span class="detail-value">${event.game_data.stage_type || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Habitación:</span>
                        <span class="detail-value">${event.game_data.room_id || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Tipo de Habitación:</span>
                        <span class="detail-value">${event.game_data.room_type || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Frame:</span>
                        <span class="detail-value">${event.game_data.frame_count || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Datos específicos del evento
    if (event.data && Object.keys(event.data).length > 0) {
        html += `
            <div class="detail-section">
                <h4>Datos Específicos</h4>
                <div class="detail-grid">
        `;
        
        // Agregar cada propiedad
        for (const [key, value] of Object.entries(event.data)) {
            html += `
                <div class="detail-item">
                    <span class="detail-label">${key}:</span>
                    <span class="detail-value">${value}</span>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    // JSON completo
    html += `
        <div class="detail-section">
            <h4>JSON Completo</h4>
            <pre class="detail-json">${JSON.stringify(event, null, 2)}</pre>
        </div>
    `;
    
    return html;
}

/**
 * Cerrar panel de detalles
 */
function closeDetails() {
    const detailsEl = document.getElementById('event-details');
    if (detailsEl) {
        detailsEl.style.display = 'none';
    }
} 