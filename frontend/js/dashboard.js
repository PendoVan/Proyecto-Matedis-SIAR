/**
 * dashboard.js
 * Gestiona el dashboard de salud del sistema SIAR
 * Incluye: Estadísticas, gráficos de fiabilidad, contadores de alertas
 */

const API_BASE = 'http://localhost:8000';

// Variables globales para gráficos
let graficoFiabilidad = null;
let graficoAlertas = null;
let intervalActualizacion = null;

/**
 * Inicializa el dashboard
 */
async function inicializarDashboard() {
    await cargarEstadisticasGenerales();
    await cargarResumenAlertas();
    await cargarFiabilidadDepartamentos();
    await cargarMapaCalor();

    // Actualizar cada 5 segundos
    if (intervalActualizacion) {
        clearInterval(intervalActualizacion);
    }
    intervalActualizacion = setInterval(actualizarDashboard, 5000);
}

/**
 * Cargar estadísticas generales
 */
async function cargarEstadisticasGenerales() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/estadisticas`);
        const stats = await res.json();

        document.getElementById('stat-departamentos').textContent = stats.total_departamentos;
        document.getElementById('stat-rutas').textContent = stats.total_rutas;
        document.getElementById('stat-distancia').textContent = `${stats.distancia_total_km.toFixed(0)} km`;
        document.getElementById('stat-fiabilidad').textContent = `${(stats.fiabilidad_promedio * 100).toFixed(1)}%`;
        document.getElementById('stat-alertas-activas').textContent = stats.alertas_activas;
        document.getElementById('stat-alertas-criticas').textContent = stats.alertas_criticas;

    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

/**
 * Cargar resumen de alertas y crear gráfico
 */
async function cargarResumenAlertas() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/alertas-resumen`);
        const alertas = await res.json();

        // Agrupar por severidad
        const criticas = alertas.filter(a => a.severidad === 'critica').reduce((sum, a) => sum + a.cantidad, 0);
        const moderadas = alertas.filter(a => a.severidad === 'moderada').reduce((sum, a) => sum + a.cantidad, 0);
        const informativas = alertas.filter(a => a.severidad === 'informativaueva').reduce((sum, a) => sum + a.cantidad, 0);

        // Actualizar contadores
        document.getElementById('contador-criticas').textContent = criticas;
        document.getElementById('contador-moderadas').textContent = moderadas;
        document.getElementById('contador-informativas').textContent = informativas;

        // Crear gráfico de donut
        const ctx = document.getElementById('grafico-alertas');
        if (ctx) {
            if (graficoAlertas) {
                graficoAlertas.destroy();
            }

            graficoAlertas = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: alertas.map(a => a.tipo),
                    datasets: [{
                        data: alertas.map(a => a.cantidad),
                        backgroundColor: alertas.map(a => {
                            if (a.severidad === 'critica') return '#dc3545';
                            if (a.severidad === 'moderada') return '#ffc107';
                            return '#28a745';
                        })
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

    } catch (error) {
        console.error('Error cargando alertas:', error);
    }
}

/**
 * Cargar fiabilidad por departamentos y crear gráfico de barras
 */
async function cargarFiabilidadDepartamentos() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/fiabilidad-departamentos`);
        const departamentos = await res.json();

        const ctx = document.getElementById('grafico-fiabilidad');
        if (ctx) {
            if (graficoFiabilidad) {
                graficoFiabilidad.destroy();
            }

            graficoFiabilidad = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: departamentos.map(d => d.departamento),
                    datasets: [{
                        label: 'Fiabilidad (%)',
                        data: departamentos.map(d => (d.fiabilidad_promedio * 100).toFixed(1)),
                        backgroundColor: departamentos.map(d => {
                            if (d.estado === 'optimo') return '#28a745';
                            if (d.estado === 'normal') return '#ffc107';
                            return '#dc3545';
                        })
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
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

    } catch (error) {
        console.error('Error cargando fiabilidad:', error);
    }
}

/**
 * Cargar mapa de calor de rutas
 */
async function cargarMapaCalor() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/mapa-calor`);
        const data = await res.json();

        // Actualizar resumen
        const resumenHtml = `
            <div style="display: flex; justify-content: space-around; margin-top: 10px;">
                <div style="text-align: center;">
                    <div style="color: #dc3545; font-size: 1.5em; font-weight: bold;">${data.resumen.rutas_alto_riesgo}</div>
                    <div style="font-size: 0.8em; color: #666;">Alto Riesgo</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #ffc107; font-size: 1.5em; font-weight: bold;">${data.resumen.rutas_moderado}</div>
                    <div style="font-size: 0.8em; color: #666;">Moderado</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #28a745; font-size: 1.5em; font-weight: bold;">${data.resumen.rutas_bajo_riesgo}</div>
                    <div style="font-size: 0.8em; color: #666;">Bajo Riesgo</div>
                </div>
            </div>
        `;

        const resumenContainer = document.getElementById('resumen-mapa-calor');
        if (resumenContainer) {
            resumenContainer.innerHTML = resumenHtml;
        }

    } catch (error) {
        console.error('Error cargando mapa de calor:', error);
    }
}

/**
 * Actualizar dashboard (llamado periódicamente)
 */
async function actualizarDashboard() {
    await cargarEstadisticasGenerales();
    await cargarResumenAlertas();
}

/**
 * Detener actualización automática
 */
function detenerActualizacionDashboard() {
    if (intervalActualizacion) {
        clearInterval(intervalActualizacion);
        intervalActualizacion = null;
    }
}
