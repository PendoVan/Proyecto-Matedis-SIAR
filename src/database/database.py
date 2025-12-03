"""
Módulo de Base de Datos con SQLAlchemy
Auto-inicialización al arranque de FastAPI
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 📁 Configuración de la base de datos SQLite
DB_DIR = "data"
DB_FILE = "siar.db"
DB_PATH = os.path.join(DB_DIR, DB_FILE)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Crear motor de BD
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},  # Necesario para SQLite con FastAPI
    echo=False  # Cambiar a True para debug SQL
)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa para modelos
Base = declarative_base()


# ==================== MODELOS ====================

class AlertaDB(Base):
    """Modelo de Alertas Persistentes"""
    __tablename__ = "alertas"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alerta_id = Column(String, unique=True, index=True)  # GEO-XXXX o CLIMA-XXXX
    tipo = Column(String)  # 'huayco', 'deslizamiento', etc.
    ubicacion = Column(String)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    descripcion = Column(String, nullable=True)
    estado = Column(String, default="activa")  # 'activa', 'resuelta', 'archivada'
    nivel_confianza = Column(Float, nullable=True)
    departamento = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    datos_adicionales = Column(JSON, nullable=True)  # Para datos extra en formato JSON
    
    def to_dict(self):
        """Convierte el modelo a diccionario para API response"""
        return {
            "alerta_id": self.alerta_id,
            "tipo": self.tipo,
            "ubicacion": self.ubicacion,
            "lat": self.lat,
            "lon": self.lon,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "nivel_confianza": self.nivel_confianza,
            "departamento": self.departamento,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "datos_adicionales": self.datos_adicionales
        }


class HistorialRutasDB(Base):
    """Historial de cálculos de rutas"""
    __tablename__ = "historial_rutas"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    origen = Column(String, index=True)
    destino = Column(String, index=True)
    distancia_total_km = Column(Float)
    fiabilidad_promedio = Column(Float)
    peso_total = Column(Float)
    num_tramos = Column(Integer)
    ruta_completa = Column(JSON)  # Lista de nodos
    timestamp = Column(DateTime, default=datetime.now)
    condiciones_clima = Column(JSON, nullable=True)  # Clima al momento del cálculo


class EventosClimaDB(Base):
    """Registro de eventos climáticos"""
    __tablename__ = "eventos_clima"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    departamento = Column(String, index=True)
    fecha = Column(DateTime, default=datetime.now)
    temperatura = Column(Float, nullable=True)
    precipitacion = Column(Float, nullable=True)
    humedad = Column(Float, nullable=True)
    presion = Column(Float, nullable=True)
    viento = Column(Float, nullable=True)
    riesgo_calculado = Column(Float, nullable=True)  # 0.0 a 1.0
    es_prediccion = Column(Boolean, default=False)  # True si es predicción, False si es real


class LoteCosechaDB(Base):
    """Lotes de cosecha registrados"""
    __tablename__ = "lotes_cosecha"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lote_id = Column(String, unique=True, index=True)
    producto = Column(String)
    cantidad_kg = Column(Float)
    origen = Column(String)
    destino = Column(String)
    estado = Column(String, default="registrado")  # 'registrado', 'en_transito', 'entregado'
    timestamp_registro = Column(DateTime, default=datetime.now)
    timestamp_entrega = Column(DateTime, nullable=True)
    ruta_asignada = Column(JSON, nullable=True)


# ==================== FUNCIONES DE INICIALIZACIÓN ====================

def init_db():
    """
    Crea todas las tablas si no existen.
    Se llama automáticamente al iniciar FastAPI.
    """
    # Crear directorio si no existe
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    print("=" * 60)
    print("💾 BASE DE DATOS INICIALIZADA")
    print("=" * 60)
    print(f"📁 Ubicación: {os.path.abspath(DB_PATH)}")
    print(f"📊 Tablas creadas:")
    print(f"   - alertas")
    print(f"   - historial_rutas")
    print(f"   - eventos_clima")
    print(f"   - lotes_cosecha")
    print("=" * 60)


def get_db():
    """
    Dependency para FastAPI.
    Crea una sesión de BD y la cierra después de usarla.
    
    Uso en FastAPI:
        @app.get("/ejemplo")
        def ejemplo(db: Session = Depends(get_db)):
            alerts = db.query(AlertaDB).all()
            return alerts
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== UTILIDADES ====================

def contar_registros(db_session):
    """Retorna conteo de registros por tabla"""
    return {
        "alertas": db_session.query(AlertaDB).count(),
        "historial_rutas": db_session.query(HistorialRutasDB).count(),
        "eventos_clima": db_session.query(EventosClimaDB).count(),
        "lotes_cosecha": db_session.query(LoteCosechaDB).count()
    }


def limpiar_datos_antiguos(db_session, dias=30):
    """
    Limpia registros más antiguos de X días (mantenimiento)
    """
    from datetime import timedelta
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    # Limpiar historial de rutas antiguo
    db_session.query(HistorialRutasDB).filter(
        HistorialRutasDB.timestamp < fecha_limite
    ).delete()
    
    # Limpiar eventos de clima antiguos
    db_session.query(EventosClimaDB).filter(
        EventosClimaDB.fecha < fecha_limite
    ).delete()
    
    db_session.commit()
    print(f"🧹 Limpieza completada: eliminados datos anteriores a {fecha_limite.date()}")


if __name__ == "__main__":
    # Si ejecutas este archivo directamente, crea la BD
    print("Inicializando base de datos manualmente...")
    init_db()
    
    # Mostrar info
    db = SessionLocal()
    print(f"\n📊 Registros actuales: {contar_registros(db)}")
    db.close()
