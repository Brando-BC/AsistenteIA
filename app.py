from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import os
import time

# --- Cargar variables de entorno ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Inicializar Flask ---
app = Flask(__name__)
CORS(app)

# --- Almacenar datos de sensores ---
datos_esp32 = {}
ultima_actualizacion = 0

@app.route('/')
def home():
    return "🤖 AsistenteIA conectado a Internet y listo ✅"

@app.route('/sensores', methods=['POST'])
def recibir_datos():
    global datos_esp32, ultima_actualizacion
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    datos_esp32 = data
    ultima_actualizacion = time.time()
    print("📡 Datos recibidos del ESP32:", datos_esp32)
    return jsonify({"status": "OK", "mensaje": "Datos actualizados"}), 200

@app.route('/ia', methods=['POST'])
def ia_responder():
    global datos_esp32, ultima_actualizacion
    mensaje = request.json.get("mensaje", "").strip()
    print("💬 Pregunta del usuario:", mensaje)

    # --- Preparar mensaje para IA ---
    system_prompt = (
        "Eres un asistente virtual tipo Alexa. Responde siempre de manera natural, "
        "breve y coloquial. "
        "Si la pregunta es sobre signos vitales o salud, usa los datos que el usuario ha enviado "
        "en el JSON 'datos_esp32' para dar recomendaciones cortas y claras. "
        "Si la pregunta es general, responde usando información correcta de Internet, "
        "y si no está relacionado con salud puedes agregar un aviso breve de 'No estoy diseñado específicamente para esto, pero...'."
    )

    # --- Adjuntar datos de sensores si son recientes ---
    datos_actuales = {}
    if time.time() - ultima_actualizacion < 120 and datos_esp32:
        datos_actuales = datos_esp32
        system_prompt += f" Aquí están los datos de signos vitales recientes del usuario: {datos_actuales}"

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensaje}
            ]
        )
        respuesta = completion.choices[0].message.content.strip()
        return jsonify({"respuesta": respuesta})

    except Exception as e:
        print("❌ Error OpenAI:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
