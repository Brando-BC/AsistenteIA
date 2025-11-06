from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import os

# --- Cargar variables de entorno ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Inicializar Flask ---
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "🤖 Servidor Flask AsistenteIA funcionando correctamente."

# --- Ruta para consulta de IA ---
@app.route('/ia', methods=['POST'])
def consultar_ia():
    data = request.get_json()
    mensaje = data.get('mensaje', '')

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente médico que analiza signos vitales y posibles caídas."},
                {"role": "user", "content": mensaje}
            ]
        )
        respuesta = completion.choices[0].message.content
        return jsonify({"respuesta": respuesta})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Ruta para recibir datos del ESP32 ---
@app.route('/sensores', methods=['POST'])
def recibir_datos():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    print("📡 Datos recibidos del ESP32:", data)

    # Aquí puedes procesar, guardar o enviar los datos a la IA
    return jsonify({"status": "OK", "mensaje": "Datos recibidos correctamente"}), 200

# --- Iniciar servidor localmente ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
