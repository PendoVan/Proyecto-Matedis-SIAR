"""
Script de Jerarquización Vial
Prioriza corredores principales y penaliza conexiones artificiales
"""
import sys
sys.path.insert(0, '.')
import json

# Definir corredores viales principales (Bidireccionales)
CORREDOR_COSTA = [
    "Tumbes", "Piura", "Lambayeque", "La Libertad", "Ancash", 
    "Lima", "Ica", "Arequipa", "Moquegua", "Tacna"
]

CORREDOR_SIERRA = [
    "Cajamarca", "La Libertad", "Huánuco", "Pasco", "Junín", 
    "Huancavelica", "Ayacucho", "Apurímac", "Cusco", "Puno"
]

CORREDOR_SELVA = [
    "Amazonas", "San Martín", "Huánuco", "Ucayali", "Cusco", "Madre de Dios"
]

# Pares de conexiones de alta prioridad (Autopistas reales)
CONEXIONES_PRIORITARIAS = set()

def agregar_corredor(lista_nodos):
    for i in range(len(lista_nodos)-1):
        n1, n2 = lista_nodos[i], lista_nodos[i+1]
        CONEXIONES_PRIORITARIAS.add(tuple(sorted([n1, n2])))

agregar_corredor(CORREDOR_COSTA)
agregar_corredor(CORREDOR_SIERRA)
agregar_corredor(CORREDOR_SELVA)

# Adicionales clave
CONEXIONES_PRIORITARIAS.add(tuple(sorted(["Lima", "Junín"]))) # Carretera Central
CONEXIONES_PRIORITARIAS.add(tuple(sorted(["Arequipa", "Puno"])))
CONEXIONES_PRIORITARIAS.add(tuple(sorted(["Cusco", "Arequipa"])))
CONEXIONES_PRIORITARIAS.add(tuple(sorted(["Lambayeque", "Cajamarca"])))
CONEXIONES_PRIORITARIAS.add(tuple(sorted(["Piura", "Lambayeque"])))

print("\n" + "="*80)
print("🛣️ JERARQUIZACIÓN VIAL DEL GRAFO")
print("="*80 + "\n")

ruta_json = "data/grafos/red_peru_24_departamentos.json"
with open(ruta_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

modificadas = 0
prioritarias = 0

for arista in data['aristas']:
    par = tuple(sorted([arista['origen'], arista['destino']]))
    
    if par in CONEXIONES_PRIORITARIAS:
        # ES UNA AUTOPISTA PRINCIPAL
        arista['fiabilidad'] = 0.95  # Muy alta fiabilidad
        arista['tipo_camino'] = 'asfaltado'
        arista['riesgo_historico'] = 0.05
        # Velocidad rápida (reducir tiempo)
        # Asumimos que la distancia es correcta, ajustamos tiempo
        # 80 km/h promedio
        arista['tiempo_estimado_min'] = int(arista['distancia_km'] / 80 * 60)
        prioritarias += 1
    else:
        # ES UNA CONEXIÓN SECUNDARIA O ARTIFICIAL
        # Penalizar para que solo se use si es necesario
        arista['fiabilidad'] = 0.60  # Baja fiabilidad
        arista['tipo_camino'] = 'trocha'
        arista['riesgo_historico'] = 0.3
        # Velocidad lenta (aumentar tiempo)
        # 40 km/h promedio (o penalización por "vuelo")
        arista['tiempo_estimado_min'] = int(arista['distancia_km'] / 40 * 60)
        
        # Penalizar distancia virtualmente para el algoritmo (peso)
        # No cambiamos distancia_km real para no mentir al usuario,
        # pero el algoritmo usará fiabilidad baja y tiempo alto para descartarla.
        modificadas += 1

with open(ruta_json, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Se optimizaron {len(data['aristas'])} aristas:")
print(f"   🌟 {prioritarias} Rutas Principales (Alta prioridad, Asfaltado)")
print(f"   📉 {modificadas} Rutas Secundarias (Baja prioridad, Trocha)")
print("\nEsto forzará al algoritmo a preferir la Panamericana y carreteras reales.")
print("="*80 + "\n")
