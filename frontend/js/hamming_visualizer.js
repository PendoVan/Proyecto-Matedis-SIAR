/**
 * hamming_visualizer.js
 * Visualización paso a paso de corrección de errores Hamming
 */

const API_BASE = 'http://localhost:8000';

let hammingStats = null;
let graficoTasaErrores = null;

/**
 * Ejecutar demo Hamming con visualización paso a paso
 */
async function ejecutarDemoHamming() {
    const ubicacion = document.getElementById('demo-ubicacion').value;
    const errores = parseInt(document.getElementById('demo-errores').value) || 0;

    try {
        // Ejecutar demo de codificación completa
        const res = await fetch(`${API_BASE}/demo/codificacion`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tipo: 'DEMO_HAMMING',
                ubicacion: ubicacion,
                descripcion: 'Demostración de corrección de errores',
                simular_errores: errores
            })
        });

        const demo = await res.json();

        // Mostrar resultado general
        mostrarResultadoDemo(demo);

        // Si hay errores, mostrar visualización paso a paso
        if (errores > 0) {
            await mostrarVisualizacionPasoAPaso(demo);
        }

    } catch (error) {
        console.error('Error ejecutando demo:', error);
        alert('Error ejecutando demo');
    }
}

/**
 * Mostrar resultado general del demo
 */
function mostrarResultadoDemo(demo) {
    const resultadoHtml = `
        <div class="card" style="background:#e7f3ff; margin-top: 15px;">
            <h3>Resultado de Demo Hamming</h3>
            <div style="font-family: monospace; font-size: 0.85em;">
                <p><strong>Mensaje Original:</strong><br>
                    ${JSON.stringify(demo.mensaje_original, null, 2)}</p>
                
                <p><strong>Codificación:</strong><br>
                    Bits totales: ${demo.bits_codificados}<br>
                    Redundancia: ${demo.redundancia ? demo.redundancia.toFixed(1) : '75.0'}%</p>
                
                <p style="color: ${demo.errores_simulados > 0 ? '#dc3545' : '#28a745'};">
                    <strong>Transmisión:</strong><br>
                    Errores introducidos: ${demo.errores_simulados}<br>
                    Errores corregidos: ${demo.errores_corregidos}</p>
                
                <p><strong>Mensaje Recuperado:</strong><br>
                    ${JSON.stringify(demo.mensaje_recuperado, null, 2)}</p>
                
                <p style="color: ${demo.firma_valida ? '#28a745' : '#dc3545'};">
                    <strong>Firma Digital:</strong> ${demo.firma_valida ? 'VÁLIDA ✓' : 'INVÁLIDA ✗'}</p>
            </div>
        </div>
    `;

    document.getElementById('resultado-demo').innerHTML = resultadoHtml;
}

/**
 * Mostrar visualización paso a paso de corrección
 */
async function mostrarVisualizacionPasoAPaso(demo) {
    const container = document.getElementById('visualizacion-paso-a-paso');
    if (!container) return;

    container.innerHTML = `
        <div class="card" style="background:#fff3cd; margin-top: 10px;">
            <h4>Visualización Paso a Paso</h4>
            <div id="pasos-hamming" style="margin-top: 10px;"></div>
            <div id="animacion-bits" style="margin-top: 15px; text-align: center;"></div>
        </div>
    `;

    // Simular animación de bits
    const animacionDiv = document.getElementById('animacion-bits');
    animacionDiv.innerHTML = `
        <div style="display: flex; justify-content: center; gap: 5px; flex-wrap: wrap;">
            ${Array(7).fill(0).map((_, i) => `
                <div class="bit-box" id="bit-${i}" style="
                    width: 40px;
                    height: 40px;
                    border: 2px solid #333;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    background: ${i >= 4 ? '#fff3cd' : '#e7f3ff'};
                ">
                    ${i < 4 ? 'D' : 'P'}${i + 1}
                </div>
            `).join('')}
        </div>
        <div style="margin-top: 10px; font-size: 0.8em; color: #666;">
            <span style="color: #0066cc;">■ Bits de Datos</span> | 
            <span style="color: #cc8800;">■ Bits de Paridad</span>
        </div>
    `;
}

/**
 * Cargar estadísticas de Hamming
 */
async function cargarEstadisticasHamming() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/hamming-stats`);
        hammingStats = await res.json();

        // Actualizar contadores
        document.getElementById('hamming-total-mensajes').textContent = hammingStats.total_mensajes;
        document.getElementById('hamming-errores-detectados').textContent = hammingStats.total_errores_detectados;
        document.getElementById('hamming-errores-corregidos').textContent = hammingStats.total_errores_corregidos;
        document.getElementById('hamming-tasa-error').textContent = `${hammingStats.tasa_error.toFixed(2)}%`;
        document.getElementById('hamming-eficiencia').textContent = `${hammingStats.eficiencia_correccion.toFixed(1)}%`;

        // Crear gráfico de tasa de errores
        crearGraficoTasaErrores(hammingStats.ultimas_24h);

    } catch (error) {
        console.error('Error cargando estadísticas Hamming:', error);
    }
}

/**
 * Crear gráfico de tasa de errores en el tiempo
 */
function crearGraficoTasaErrores(datos24h) {
    const ctx = document.getElementById('grafico-tasa-errores');

    if (ctx) {
        if (graficoTasaErrores) {
            graficoTasaErrores.destroy();
        }

        const horas = Object.keys(datos24h);
        const valores = Object.values(datos24h);

        graficoTasaErrores = new Chart(ctx, {
            type: 'line',
            data: {
                labels: horas,
                datasets: [{
                    label: 'Errores Detectados',
                    data: valores,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
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
}
