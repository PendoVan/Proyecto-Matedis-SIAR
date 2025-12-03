/**
 * CORRECCIÓN PARA EL ERROR 422 EN FSM ALERTAS
 * 
 * PROBLEMA: Las coordenadas se están enviando en formato incorrecto
 * 
 * SOLUCIÓN: Reemplaza la función crearAlertaFSM() completa con esta version:
 */

async function crearAlertaFSM(event) {
    event.preventDefault();

    const depto = document.getElementById('nueva-alerta-depto').value;
    const tipo = document.getElementById('nueva-alerta-tipo').value;
    const desc = document.getElementById('nueva-alerta-desc').value;
    const fiab = parseFloat(document.getElementById('nueva-alerta-fiab').value);
    const precip = parseFloat(document.getElementById('nueva-alerta-precip').value);
    const temp = parseFloat(document.getElementById('nueva-alerta-temp').value);
    const viento = parseFloat(document.getElementById('nueva-alerta-viento').value);

    const coords = COORDENADAS[depto];

    // ✅ VALIDACIÓN AGREGADA
    if (!coords || !coords.lat || !coords.lon) {
        alert('Error: No se encontraron coordenadas para ' + depto);
        console.error('Coordenadas disponibles:', COORDENADAS);
        console.error('Buscando:', depto);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/fsm/alertas/crear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                departamento: depto,
                // ✅ CORRECCIÓN: Asegurar formato correcto {lat: ..., lon: ...}
                coordenadas: {
                    lat: coords.lat,
                    lon: coords.lon
                },
                tipo: tipo,
                descripcion: desc,
                fiabilidad: fiab,
                metadata: {
                    precipitacion: precip,
                    temperatura: temp,
                    viento: viento
                }
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            alert(`✓ Alerta creada: ${data.alerta.id}\nEstado: ${data.alerta.estado_actual}`);
            cerrarModalNuevaAlerta();
            cargarAlertasFSM();
        } else {
            alert('Error creando alerta: ' + (data.detail || JSON.stringify(data)));
            console.error('Error del servidor:', data);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    }
}

/**
 * INSTRUCCIONES PARA APLICAR EL PARCHE:
 * 
 * 1. Abre frontend/index.html
 * 2. Busca la función `async function crearAlertaFSM(event) {`
 * 3. Reemplaza TODA la función con el código de arriba
 * 4. Guarda el archivo
 * 5. Recarga el navegador con Ctrl+Shift+R (hard refresh)
 * 6. Intenta crear una alerta nuevamente
 * 
 * Si el error persiste, abre la consola del navegador (F12) y verifica:
 * - ¿Se muestra el mensaje "Coordenadas disponibles"?
 * - ¿El objeto COORDENADAS tiene el formato correcto?
 */
