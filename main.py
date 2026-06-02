from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from datetime import datetime, timezone
import json

app = FastAPI()

# Conexión limpia a tu clúster de MongoDB Atlas
MONGO_URI = "mongodb+srv://esp32:esp32pass@cluster0.cc7ewhd.mongodb.net/iot"

client = MongoClient(MONGO_URI)
db = client.iot
collection = db.sensores

@app.get("/")
def root():
    return {"mensaje": "API funcionando. Agrega /dashboard al link en tu navegador para ver los graficos."}

@app.post("/sensor")
def guardar_sensor(data: dict):
    data["fecha"] = datetime.now(timezone.utc)
    collection.insert_one(data)
    return {"status": "dato guardado"}

@app.get("/dashboard")
def obtener_dashboard():
    # 1. Traer los últimos 20 datos guardados
    registros = list(collection.find().sort("fecha", -1).limit(20))
    registros.reverse()
    
    fechas = []
    ritmos = []
    oxigeno = []
    
    for r in registros:
        if "fecha" in r:
            hora_bonita = r["fecha"].strftime("%H:%M:%S")
        else:
            hora_bonita = "--:--:--"
        fechas.append(hora_bonita)
        ritmos.append(r.get("ritmo_cardiaco", 0))
        oxigeno.append(r.get("oxigenacion", 0))

    # Convertir las listas a cadenas JSON seguras
    fechas_json = json.dumps(fechas)
    ritmos_json = json.dumps(ritmos)
    oxigeno_json = json.dumps(oxigeno)

    # 2. Construcción limpia del HTML sin usar f-strings conflictivos
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IoT Dashboard - Oximetro</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }
            .container { max-width: 1000px; margin: 0 auto; }
            h1 { text-align: center; color: #2c3e50; margin-bottom: 30px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
            .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .card h2 { margin-top: 0; font-size: 1.2rem; color: #7f8c8d; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }
            .btn-refresh { display: block; width: 150px; margin: 20px auto; padding: 10px; text-align: center; background-color: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; font-weight: bold; }
            .btn-refresh:hover { background-color: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Dashboard de Monitoreo Medico (ESP32)</h1>
            <button class="btn-refresh" onclick="location.reload()">🔄 Actualizar</button>
            
            <div class="grid">
                <div class="card">
                    <h2>Frecuencia Cardiaca (BPM)</h2>
                    <canvas id="chartRitmo"></canvas>
                </div>
                <div class="card">
                    <h2>Saturacion de Oxigeno (SpO2 %)</h2>
                    <canvas id="chartOxigeno"></canvas>
                </div>
            </div>
        </div>

        <script>
            // Inyeccion segura de arreglos desde Python usando reemplazo directo
            const etiquetasFechas = REEMPLAZAR_FECHAS;
            const datosRitmo = REEMPLAZAR_RITMOS;
            const datosOxigeno = REEMPLAZAR_OXIGENOS;

            // Grafica de Ritmo
            new Chart(document.getElementById('chartRitmo').getContext('2d'), {
                type: 'line',
                data: {
                    labels: etiquetasFechas,
                    datasets: [{
                        label: 'Pulsaciones (BPM)',
                        data: datosRitmo,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        borderWidth: 3,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: { scales: { y: { min: 40, max: 220 } } }
            });

            // Grafica de Oxigeno
            new Chart(document.getElementById('chartOxigeno').getContext('2d'), {
                type: 'line',
                data: {
                    labels: etiquetasFechas,
                    datasets: [{
                        label: 'Oxigeno (%)',
                        data: datosOxigeno,
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        borderWidth: 3,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: { scales: { y: { min: 40, max: 110 } } }
            });
        </script>
    </body>
    </html>
    """
    
    # 3. Reemplazar las etiquetas comodín por los datos reales procesados en JSON
    html_final = html_template.replace("REEMPLAZAR_FECHAS", fechas_json)
    html_final = html_final.replace("REEMPLAZAR_RITMOS", ritmos_json)
    html_final = html_final.replace("REEMPLAZAR_OXIGENOS", oxigeno_json)
    
    return HTMLResponse(content=html_final, status_code=200)