"""
Módulo: logger.py
Descripción: Sistema de logging para el proyecto.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from .config import LOGS_DIR


def configurar_logger(nombre: str, nivel=logging.INFO) -> logging.Logger:
    """
    Configura un logger con salida a archivo y consola.
    
    Args:
        nombre: Nombre del logger (usualmente __name__ del módulo)
        nivel: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(nombre)
    logger.setLevel(nivel)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Formato de mensajes
    formato = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setLevel(nivel)
    handler_consola.setFormatter(formato)
    logger.addHandler(handler_consola)
    
    # Handler para archivo
    fecha = datetime.now().strftime('%Y%m%d')
    archivo_log = LOGS_DIR / f"siar_{fecha}.log"
    
    handler_archivo = logging.FileHandler(archivo_log, encoding='utf-8')
    handler_archivo.setLevel(nivel)
    handler_archivo.setFormatter(formato)
    logger.addHandler(handler_archivo)
    
    return logger


# Logger por defecto del sistema
logger_sistema = configurar_logger('SIAR', nivel=logging.INFO)