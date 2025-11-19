"""
Módulo de Teoría de Codificación y Criptografía
Incluye: Hamming, Paridad, Firmas Digitales, Protocolo de Mensajería
"""

from .hamming import CodificadorHamming
from .firmas_digitales import GeneradorFirmas

__all__ = ['CodificadorHamming', 'GeneradorFirmas']