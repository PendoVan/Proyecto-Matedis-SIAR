/**
 * clima_panel.js
 * Panel de clima en tiempo real
 */

const API_BASE = 'http://localhost:8000';

let graficoTemperaturas = null;
let graficoRiesgos = null;

/**
 * Inicializar panel de clima
 */
async function inicializarPanelClima() {
    await cargarClimaActual();
    await cargarTendenciasClimaticas();
}

/**
 * Cargar condiciones climáticas actuales
 */
async function cargarClimaActual() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/clima-actual`);
        const climas = await res.json();

        // Mostrar widgets de clima
        const climaHtml = climas.map(clima => `
            <div class="card clima-widget" style="margin-bottom: 10px; border-left: 4px solid ${getColorEstadoClima(clima.estado)};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${clima.departamento}</strong>
                        <div style="font-size: 0.8em; color: #666; margin-top: 3px;">
                            <div>🌡️ ${clima.temperatura}°C</div>
                            <div>💧 ${clima.precipitacion} mm</div>
                            <div>💨 ${clima.humedad}%</div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.3em; font-weight: bold; color: ${getColorRiesgo(clima.riesgo_bloqueo)};">
                            ${(clima.riesgo_bloqueo * 100).toFixed(0)}%
                        </div>
                        <div style="font-size: 0.7em; color: #666;">
                            ${clima.estado.toUpperCase()}
                        </div>
                        <div style="font-size: 0.7em; color: #999;">
                            ${getTendenciaIcon(clima.tendencia)} ${clima.tendencia}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        const container = document.getElementById('widgets-clima');
        if (container) {
            container.innerHTML = climaHtml;
        }

        // Crear gráficos
        crearGraficoTemperaturas(climas);
        crearGraficoRiesgos(climas);

    } catch (error) {
        console.error('Error cargando clima actual:', error);
    }
}

/**
 * Crear gráfico de temperaturas por departamento
 */
function crearGraficoTemperaturas(climas) {
    const ctx = document.getElementById('grafico-temperaturas');
    if (!ctx) return;

    if (graficoTemperaturas) {
        graficoTemperaturas.destroy();
    }

    graficoTemperaturas = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: climas.map(c => c.departamento),
            datasets: [
                {
                    label: 'Temperatura (°C)',
                    data: climas.map(c => c.temperatura),
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    yAxisID: 'y'
                },
                {
                    label: 'Precipitación (mm)',
                    data: climas.map(c => c.precipitacion),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Temperatura (°C)'
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Precipitación (mm)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

/**
 * Crear gráfico de riesgos de bloqueo
 */
function crearGraficoRiesgos(climas) {
    const ctx = document.getElementById('grafico-riesgos');
    if (!ctx) return;

    if (graficoRiesgos) {
        graficoRiesgos.destroy();
    }

    // Ordenar por riesgo descendente
    const climasOrdenados = [...climas].sort((a, b) => b.riesgo_bloqueo - a.riesgo_bloqueo);

    graficoRiesgos = new Chart(ctx, {
        type: 'horizontalBar',
        data: {
            labels: climasOrdenados.map(c => c.departamento),
            datasets: [{
                label: 'Riesgo de Bloqueo (%)',
                data: climasOrdenados.map(c => (c.riesgo_bloqueo * 100).toFixed(1)),
                backgroundColor: climasOrdenados.map(c => getColorRiesgo(c.riesgo_bloqueo))
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Cargar tendencias climáticas históricas
 */
async function cargarTendenciasClimaticas() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/tendencias-historicas?dias=7`);
        const tendencias = await res.json();

        // Aquí se podría crear un gráfico de tendencias
        console.log('Tendencias climáticas:', tendencias);

    } catch (error) {
        console.error('Error cargando tendencias:', error);
    }
}

/**
 * Obtener color según estado climático
 */
function getColorEstadoClima(estado) {
    switch (estado) {
        case 'favorable': return '#28a745';
        case 'moderado': return '#ffc107';
        case 'peligroso': return '#dc3545';
        default: return '#6c757d';
    }
}

/**
 * Obtener color según nivel de riesgo
 */
function getColorRiesgo(riesgo) {
    if (riesgo > 0.7) return '#dc3545';
    if (riesgo > 0.4) return '#ffc107';
    return '#28a745';
}

/**
 * Obtener icono de tendencia
 */
function getTendenciaIcon(tendencia) {
    switch (tendencia) {
        case 'mejorando': return '↑';
        case 'empeorando': return '↓';
        case 'estable': return '→';
        default: return '•';
    }
}
