from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import os

# --- Configuración ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)

# Variable global para guardar últimos datos del ESP32
datos_esp32 = {}

@app.route('/')
def home():
    return "🤖 Servidor Flask AsistenteIA funcionando correctamente."

# --- Ruta para recibir datos del ESP32 ---
@app.route('/sensores', methods=['POST'])
def recibir_datos():
    global datos_esp32
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    datos_esp32 = data  # Guardar los últimos valores recibidos
    print("📡 Datos recibidos del ESP32:", datos_esp32)
    return jsonify({"status": "OK", "mensaje": "Datos recibidos correctamente"}), 200

# --- Ruta para IA (usa datos del ESP32 si existen) ---
@app.route('/ia', methods=['POST'])
def consultar_ia():
    global datos_esp32
    data = request.get_json()
    mensaje = data.get('mensaje', '')

    contexto = "Eres un asistente médico inteligente. Analiza signos vitales y posibles anomalías."

    # Si hay datos del ESP32 disponibles, se agregan al contexto
    if datos_esp32:
        contexto += f"\nLos últimos signos vitales recibidos son: " \
                    f"Temperatura: {datos_esp32.get('Temp', 'N/A')} °C, " \
                    f"Frecuencia cardíaca: {datos_esp32.get('BPM', 'N/A')} BPM, " \
                    f"Saturación de oxígeno: {datos_esp32.get('SpO2', 'N/A')}%, " \
                    f"Acelerómetro: ({datos_esp32.get('MPU_ax', 0)}, {datos_esp32.get('MPU_ay', 0)}, {datos_esp32.get('MPU_az', 0)})."
    else:
        contexto += "\nAún no se han recibido datos de sensores del ESP32."

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": contexto},
                {"role": "user", "content": mensaje}
            ]
        )
        respuesta = completion.choices[0].message.content
        return jsonify({"respuesta": respuesta})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
