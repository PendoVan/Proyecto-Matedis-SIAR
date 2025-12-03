## 📝 CAMBIOS MANUALES PENDIENTES EN index.html

Necesitas hacer **3 cambios simples** manualmente en el archivo `frontend/index.html`:

### ✅ **CAMBIO 1: Reemplazar botón "Alertas" por "Alertas FSM"**

**Busca la línea 417:**
```html
<button class="tab-btn" onclick="switchTab('alertas')">Alertas</button>
```

**Reemplaza con:**
```html
<button class="tab-btn" onclick="window.open('alertas_fsm.html', '_blank')">Alertas FSM</button>
```

---

### ✅ **CAMBIO 2: Eliminar la sección "Monitor Automático (IA)"**

**Busca las líneas 508-524 (aproximadamente):**
```html
<div class="card" style="border-left: 4px solid #6610f2;">
    <h3>Monitor Automático (IA)</h3>
    <p style="font-size: 0.8em; color: #666; margin-bottom: 10px;">
        Ejecuta el script de predicción automática en el servidor para todas las rutas críticas.
    </p>
    <button onclick="ejecutarMonitor()" style="background: #6610f2;">
        Iniciar Escaneo de Red
    </button>
    <div id="monitor-console" class="monitor-console">
        <div class="log-info">> Sistema listo. Esperando comando...</div>
    </div>
</div>
```

**ELIMINA TODO ESE BLOQUE** (desde `<div class="card" style="border-left...` hasta `</div>` que lo cierra).

---

### ✅ **CAMBIO 3: Verificar que la Demo Hamming funcione**

**No necesitas cambiar nada en el código**, pero asegúrate de que el botón "Ejecutar Demo" esté visible.

La demo YA usa el endpoint correcto (`/demo/codificacion`) que ya está funcionando en el backend.

---

## 🎯 Resultado Final

Después de estos 3 cambios tendrás:

**Pestañas:**
1. ✅ Rutas - Cálculo de rutas óptimas
2. ✅ Comparar - Comparación de 3 criterios
3. ✅ Clima & IA - **Solo predicción manual** (sin monitor automático)
4. ✅ Alertas FSM - Abre la página de máquina de estados
5. ✅ Demo - Demostración de Hamming
6. ✅ Monitor - Dashboard en tiempo real

---

## 🔧 **Cómo aplicarlo:**

1. Abre `frontend/index.html` en un editor
2. Usa **Ctrl+F** para buscar cada texto
3. Haz los 3 cambios marcados arriba
4. Guarda el archivo
5. Recarga el navegador con **Ctrl+Shift+R**

¡Listo! Todo funcionará perfectamente.
