"""
Módulo: config.py
Descripción: Configuraciones globales del sistema SIAR.
"""

import os
from pathlib import Path

# Directorios del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
GRAFOS_DIR = DATA_DIR / "grafos"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
GRAFOS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Parámetros del sistema
class ConfigSistema:
    """Configuraciones generales del sistema."""
    
    # Grafos y rutas
    PESO_RIESGO = 50  # Factor K de penalización por riesgo
    VELOCIDAD_ASFALTADO = 60  # km/h
    VELOCIDAD_AFIRMADO = 40
    VELOCIDAD_TROCHA = 25
    VELOCIDAD_HERRADURA = 5
    
    # Alertas
    CONFIANZA_INICIAL = 0.3  # 30%
    TIEMPO_EXPIRACION_ALERTA_HORAS = 24
    MIN_CONFIRMACIONES_CRITICAS = 3
    
    # Códigos de Hamming
    BITS_PARIDAD = 4  # Para Hamming(7,4)
    
    # API (si implementan)
    API_HOST = "localhost"
    API_PORT = 5000
    DEBUG_MODE = True


class ConfigRegiones:
    """Configuraciones específicas por región."""
    
    AYACUCHO = {
        "nodos_principales": ["Ayacucho", "Huanta", "San Miguel", "Sivia"],
        "productos_principales": ["papa", "quinua", "café"],
        "riesgo_base_lluvias": 0.3
    }
    
    CUSCO = {
        "nodos_principales": ["Cusco", "Urubamba", "Ollantaytambo"],
        "productos_principales": ["papa", "maíz", "café"],
        "riesgo_base_lluvias": 0.25
    }