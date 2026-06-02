from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from datetime import datetime, timezone

app = FastAPI()

# Tu conexión real a MongoDB Atlas
MONGO_URI = "mongodb+srv://esp32:esp32pass@cluster0.cc7ewhd.mongodb.net/iot"

client = MongoClient(MONGO_URI)
db = client.iot
collection = db.sensores

@app.get("/")
def root():
    return {"mensaje": "API funcionando. Ve a /dashboard para ver las graficas."}

@app.post("/sensor")
def guardar_sensor(data: dict):
    data["fecha"] = datetime.now(timezone.utc)
    collection.insert_one(data)
    return {"status": "dato guardado"}

# --- NUEVA RUTA PARA EL DASHBOARD ---
@app.get("/dashboard", response_class=HTMLResponse)
def obtener_dashboard():
    # 1. Traer los últimos 20 registros guardados en la base de datos
    registros = list(collection.find().sort("fecha", -1).limit(20))
    
    # Invertir el orden para que la gráfica se lea de izquierda (antiguo) a derecha (reciente)
    registros.reverse()
    
    # 2. Extraer los datos para las gráficas, saltándonos los errores de -999 si los hay
    fechas = []
    ritmos = []
    oxigeno = []
    
    for r in registros:
        # Formatear la fecha para que se vea bonita (Hora:Minuto:Segundo)
        if "fecha" in r:
            hora_bonita = r["fecha"].strftime("%H:%M:%S")
        else:
            hora_bonita = "--:--:--"
            
        fechas.append(hora_bonita)
        ritmos.append(r.get("ritmo_cardiaco", 0))
        oxigeno.append(r.get("oxigenacion", 0))

    # 3. Código HTML, CSS y JS de la página del Dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IoT Dashboard - Oxímetro</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f6f9;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
            }}
            h1 {{
                text-align: center;
                color: #2c3e50;
                margin-bottom: 30px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            @media (max-width: 768px) {{
                .grid {{ grid-template-columns: 1fr; }}
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }}
            .card h2 {{
                margin-top: 0;
                font-size: 1.2rem;
                color: #7f8c8d;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 10px;
            }}
            .btn-refresh {{
                display: block;
                width: 150px;
                margin: 20px auto;
                padding: 10px;
                text-align: center;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 1rem;
                font-weight: bold;
            }}
            .btn-refresh:hover {{ background-color: #2980b9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Dashboard de Monitoreo Médico (ESP32)</h1>
            <button class="btn-refresh" onclick="location.reload()">🔄 Actualizar</button>
            
            <div class="grid">
                <div class="card">
                    <h2>Frecuencia Cardíaca (BPM)</h2>
                    <canvas id="chartRitmo"></canvas>
                </div>
                
                <div class="card">
                    <h2>Saturación de Oxígeno (SpO2 %)</h2>
                    <canvas id="chartOxigeno"></canvas>
                </div>
            </div>
        </div>

        <script>
            // Pasar los datos de Python a JavaScript
            const etiquetasFechas = {fechas};
            const datosRitmo = {ritmos};
            const datosOxigeno = {oxigeno};

            // Configurar Gráfica de Ritmo Cardíaco
            const ctxRitmo = document.getElementById('chartRitmo').getContext('2d');
            new Chart(ctxRitmo, {{
                type: 'line',
                data: {{
                    labels: etiquetasFechas,
                    datasets: [{{
                        label: 'Pulsaciones (BPM)',
                        data: datosRitmo,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        borderWidth: 3,
                        tension: 0.3,
                        fill: true
                    }}]
                }},
                options: {{ scales: {{ y: {{ min: 40, max: 220 }} }} }}
            }});

            // Configurar Gráfica de Oxigenación
            const ctxOxigeno = document.getElementById('chartOxigeno').getContext('2d');
            new Chart(ctxOxigeno, {{
                type: 'line',
                data: {{
                    labels: etiquetasFechas,
                    datasets: [{{
                        label: 'Oxígeno (%)',
                        data: datosOxigeno,
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        borderWidth: 3,
                        tension: 0.3,
                        fill: true
                    }}]
                }},
                options: {{ scales: {{ y: {{ min: 50, max: 100 }} }} }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content