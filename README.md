# 🗺️ SIAR - Sistema Inteligente de Análisis de Rutas

Sistema avanzado para el cálculo de rutas óptimas en Perú, con integración de predicción climática mediante Machine Learning, gestión de alertas con codificación Hamming y máquinas de estados finitos.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración y Entrenamiento Inicial](#-configuración-y-entrenamiento-inicial)
- [Ejecución del Sistema](#-ejecución-del-sistema)
- [Uso del Sistema](#-uso-del-sistema)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Solución de Problemas](#-solución-de-problemas)

---

## ✨ Características

### 🎯 Funcionalidades Principales

- **Cálculo de Rutas Óptimas**: Algoritmo de Dijkstra con ponderación por fiabilidad climática
- **Comparación de Criterios**: Visualización simultánea de 3 rutas (más fiable, más corta, más rápida)
- **Predicción Climática con IA**: Red neuronal TensorFlow entrenada con datos SENAMHI
- **Sistema de Alertas FSM**: Gestión mediante máquinas de estados finitos
- **Codificación Hamming**: Corrección de errores en transmisión de alertas
- **Dashboard en Tiempo Real**: Monitoreo de fiabilidad y estadísticas del sistema

---

## 🔧 Requisitos Previos

### Software Necesario

- **Python 3.11** o superior
- **Git** (para clonar el repositorio)
- **Navegador web moderno** (Chrome, Firefox, Edge)

### Sistema Operativo

- Windows 10/11
- Linux (Ubuntu 20.04+, otras distribuciones)
- macOS 10.15+

---

## 📦 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/SIAR.git
cd SIAR/Proyecto-Matedis-SIAR
```

### 2. Crear Entorno Virtual

**Windows:**
```bash
python -m venv venv
```

**Linux/macOS:**
```bash
python3 -m venv venv
```

### 3. Activar Entorno Virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Actualizar pip

```bash
python -m pip install --upgrade pip
```

### 5. Instalar Dependencias

**⚠️ IMPORTANTE: Instalar en este orden específico para evitar conflictos**

#### Paso 1: Dependencias Core
```bash
pip install numpy==1.26.4 scipy==1.13.1 pandas==2.2.2
```

#### Paso 2: Machine Learning
```bash
pip install scikit-learn==1.5.1
pip install tensorflow-cpu==2.17.0
```

#### Paso 3: Web Framework
```bash
pip install fastapi==0.115.0 uvicorn[standard]==0.30.6 pydantic==2.9.2 python-multipart==0.0.12
```

#### Paso 4: Grafos y Visualización
```bash
pip install networkx==3.3 matplotlib==3.9.2 seaborn==0.13.2
```

#### Paso 5: Dependencias Geoespaciales
```bash
pip install geopandas==0.14.4
pip install osmnx==1.9.4
pip install folium==0.17.0
```

#### Paso 6: Resto de Dependencias
```bash
pip install -r requirements.txt
```

---

## 🚀 Configuración y Entrenamiento Inicial

### 1. Verificar Estructura de Datos

Asegúrate de que existan estos archivos:

```
data/
├── grafos/
│   ├── red_carreteras.json          # Grafo principal
│   └── coordenadas.json             # Coordenadas de departamentos
├── clima/
│   └── senamhi_procesado.csv        # Datos climáticos históricos
└── modelos/                         # (Se creará automáticamente)
```

### 2. Entrenar el Modelo de Red Neuronal

**⚠️ CRÍTICO: Ejecutar ANTES de iniciar la API**

```bash
python scripts/entrenar_modelo_senamhi.py
```

**Salida esperada:**
```
✅ Modelo entrenado y guardado en: data/modelos/red_neuronal_senamhi.keras
Precisión en validación: ~85-95%
```

### 3. Entrenar el Árbol de Decisión (Opcional)

```bash
python scripts/entrenar_arbol_decision.py
```

### 4. Verificar que los Modelos Existan

```bash
# Windows
dir data\modelos

# Linux/macOS
ls -la data/modelos
```

**Deberías ver:**
- `red_neuronal_senamhi.keras` (modelo principal)
- `arbol_decision.pkl` (opcional)

---

## 🎬 Ejecución del Sistema

### Método 1: Script Automático (Recomendado para Windows)

```bash
REINICIAR_TODO.bat
```

Esto iniciará:
1. Servidor HTTP en puerto 8080 (Frontend)
2. API FastAPI en puerto 8000 (Backend)

### Método 2: Ejecución Manual

#### Paso 1: Iniciar el Backend (API)

```bash
python -m uvicorn src.integracion.api_siar:app --reload --port 8000
```

**Espera a ver:**
```
======================================================================
✅ API LISTA
======================================================================
```

#### Paso 2: Iniciar el Frontend (en otra terminal)

```bash
python -m http.server 8080 --directory frontend
```

---

## 🌐 Uso del Sistema

### URLs de Acceso

| Componente | URL | Descripción |
|------------|-----|-------------|
| **Sistema Principal** | http://localhost:8080/index.html | Interfaz principal con 5 pestañas |
| **Alertas FSM** | http://localhost:8080/alertas_fsm.html | Sistema de máquinas de estados |
| **Dashboard** | http://localhost:8080/dashboard.html | Dashboard dedicado (opcional) |
| **API Docs** | http://localhost:8000/docs | Documentación interactiva OpenAPI |

### Pestañas del Sistema Principal

1. **Rutas** - Calcular ruta óptima entre departamentos
2. **Comparar** - Comparar 3 criterios de rutas simultáneamente
3. **Clima & IA** - Predicción manual con red neuronal
4. **Alertas FSM** - Sistema de alertas con estados automáticos
5. **Monitor** - Dashboard en tiempo real

---

## 📁 Estructura del Proyecto

```
Proyecto-Matedis-SIAR/
├── data/                           # Datos del sistema
│   ├── grafos/                     # Red de carreteras
│   ├── clima/                      # Datos climáticos SENAMHI
│   └── modelos/                    # Modelos entrenados
│
├── src/                            # Código fuente
│   ├── unidad3_grafos/             # Algoritmos de grafos
│   │   ├── algoritmo_fiabilidad.py
│   │   └── prediccion_climatica.py (Red Neuronal)
│   ├── unidad4_codificacion/       # Hamming & Protocolos
│   │   └── hamming.py
│   └── integracion/                # API FastAPI
│       ├── api_siar.py             # Punto de entrada principal
│       ├── dashboard_endpoints.py  # Endpoints del dashboard
│       └── maquina_estados.py      # FSM para alertas
│
├── frontend/                       # Interfaz de usuario
│   ├── index.html                  # Página principal
│   ├── alertas_fsm.html            # Sistema FSM
│   ├── dashboard.html              # Dashboard dedicado
│   └── js/                         # Módulos JavaScript
│
├── scripts/                        # Scripts de entrenamiento
│   ├── entrenar_modelo_senamhi.py  # ⭐ Entrenar red neuronal
│   └── entrenar_arbol_decision.py
│
├── tests/                          # Pruebas unitarias
├── notebooks/                      # Jupyter notebooks
│
├── requirements.txt                # Dependencias Python
├── REINICIAR_TODO.bat              # Script de inicio rápido
└── README.md                       # Este archivo
```

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web asíncrono
- **TensorFlow** - Red neuronal para predicciones
- **NetworkX** - Procesamiento de grafos
- **Scikit-learn** - Árbol de decisión

### Frontend
- **HTML5/CSS3/JavaScript** - Interfaz de usuario
- **Leaflet.js** - Mapas interactivos
- **Chart.js** - Gráficos en tiempo real

### Datos
- **SENAMHI** - Datos climáticos históricos
- **OSM** - Red de carreteras de Perú

---

## 🐛 Solución de Problemas

### Problema: "No se cargan los departamentos en los selectores"

**Causa:** La API no está respondiendo o no se ha entrenado el modelo.

**Solución:**
1. Verifica que la API esté corriendo: http://localhost:8000/docs
2. Asegúrate de haber ejecutado `entrenar_modelo_senamhi.py`
3. Haz hard refresh en el navegador: **Ctrl + Shift + R**
4. Si persiste, ejecuta `REINICIAR_TODO.bat`

### Problema: "ModuleNotFoundError al iniciar la API"

**Causa:** Dependencias no instaladas correctamente.

**Solución:**
```bash
# Desactivar entorno virtual
deactivate

# Borrar entorno virtual
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# Repetir instalación desde el paso 2
```

### Problema: "Error al entrenar el modelo"

**Causa:** Falta el archivo `senamhi_procesado.csv`.

**Solución:**
```bash
# Verificar que existe
ls data/clima/senamhi_procesado.csv

# Si no existe, ejecutar script de generación
python scripts/generar_datos_senamhi.py
```

### Problema: "Puerto 8000 ya está en uso"

**Solución:**
```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
killall python
```

### Problema: "Demo de Hamming no funciona"

**Verificación:**
1. Abre http://localhost:8000/docs
2. Busca el endpoint `/demo/codificacion`
3. Prueba con valores: `tipo="TEST"`, `ubicacion="Test"`, `simular_errores=1`
4. Si responde 200, el problema está en el frontend (hacer hard refresh)

---

## 📊 Flujo de Uso Típico

### Ejemplo 1: Calcular Ruta
1. Abre http://localhost:8080/index.html
2. Pestaña "Rutas"
3. Selecciona origen: "Lima"
4. Selecciona destino: "Cusco"
5. Click "Buscar Ruta"
6. Verás la ruta en el mapa con fiabilidad, distancia y tiempo

### Ejemplo 2: Crear Alerta FSM
1. Abre http://localhost:8080/alertas_fsm.html
2. Click "+ Nueva Alerta"
3. Selecciona departamento
4. Ingresa fiabilidad (ej: 0.4 para estado CRÍTICO)
5. Click "Crear"
6. La alerta aparece en el mapa con color según su estado

### Ejemplo 3: Predicción Climática
1. Pestaña "Clima & IA"
2. Selecciona departamento
3. Ingresa: Temp=25, Precip=80, Hum=75
4. Click "Predecir"
5. Verás el % de riesgo de bloqueo calculado por la red neuronal

---

## 📞 Soporte

Para problemas o preguntas:
1. Revisa la sección [Solución de Problemas](#-solución-de-problemas)
2. Consulta los logs de la API en la terminal
3. Verifica la consola del navegador (F12)

---

## 📝 Notas Importantes

- ⚠️ **Siempre** entrena los modelos antes del primer uso
- ⚠️ La API **debe estar corriendo** antes de abrir el frontend
- ⚠️ **NO** abras `index.html` directamente (doble click) - usa el servidor HTTP
- ✅ Usa **hard refresh** (Ctrl+Shift+R) después de cambios
- ✅ El script `REINICIAR_TODO.bat` resuelve el 90% de problemas

---

## 🎓 Fundamentos Matemáticos

- **Algoritmo de Dijkstra**: Cálculo de caminos más cortos con ponderación
- **Código Hamming (7,4)**: Corrección de errores de 1 bit
- **Autómatas Finitos**: Gestión de transiciones de estados en alertas
- **Redes Neuronales**: Predicción de riesgo climático
- **Árboles de Decisión**: Clasificación de rutas por seguridad

---

## 📄 Licencia

Este proyecto es parte del curso de Matemáticas Discretas.

---

**Desarrollado con ❤️ para la gestión inteligente de rutas en Perú**
