/**
 * Data Event Manager - Javascript
 * Maneja la interactividad de la interfaz web.
 */

// Variables globales
let allEvents = [];
let filteredEvents = [];
let currentPage = 1;
const perPage = 10;

// Cargar datos cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
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
});

/**
 * Actualizar datos desde el servidor
 */
function refreshData() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.textContent = 'Actualizando...';
    }
    
    fetch('/api/refresh')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Recargar la página actual
                window.location.reload();
            } else {
                console.error('Error al actualizar los datos:', data.error);
                alert('Error al actualizar los datos: ' + data.error);
                if (refreshBtn) {
                    refreshBtn.disabled = false;
                    refreshBtn.textContent = 'Actualizar Datos';
                }
            }
        })
        .catch(error => {
            console.error('Error al actualizar los datos:', error);
            alert('Error al actualizar los datos: ' + error);
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.textContent = 'Actualizar Datos';
            }
        });
}

/**
 * Obtener todos los eventos 
 */
function fetchEvents() {
    const eventsBody = document.getElementById('events-body');
    if (!eventsBody) return;
    
    fetch('/api/events')
        .then(response => response.json())
        .then(data => {
            allEvents = data;
            filterData();
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