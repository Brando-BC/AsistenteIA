from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import random

app = Flask(__name__)
CORS(app)

# --- Datos actuales de sensores ---
datos_esp32 = {}
ultima_actualizacion = 0

@app.route('/')
def home():
    return "🤖 Servidor AsistenteIA activo ✅"

@app.route('/sensores', methods=['POST'])
def recibir_datos():
    global datos_esp32, ultima_actualizacion
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    datos_esp32 = data
    ultima_actualizacion = time.time()
    print("📡 Datos recibidos:", datos_esp32)
    return jsonify({"status": "OK", "mensaje": "Datos actualizados"}), 200

@app.route('/ia', methods=['POST'])
def ia_responder():
    global datos_esp32, ultima_actualizacion
    mensaje = request.json.get("mensaje", "").strip()
    print("💬 Pregunta del usuario:", mensaje)

    # Reinicia datos si no hay actualización reciente
    if time.time() - ultima_actualizacion > 120:
        datos_esp32 = {}

    # --- Preguntas sobre salud / bienestar ---
    if any(k in mensaje.lower() for k in ["signos", "vitales", "salud", "temperatura", "pulso", "bpm", "oxígeno", "actividad", "nutrición"]):
        if datos_esp32:
            temp = datos_esp32.get("Temp", 0)
            bpm = datos_esp32.get("BPM", 0)
            spo2 = datos_esp32.get("SpO2", 0)

            recomendaciones = []
            if temp > 37.5:
                recomendaciones.append("descansa y toma agua")
            if bpm > 100:
                recomendaciones.append("relájate y respira profundo")
            if spo2 < 94:
                recomendaciones.append("respira profundo o abre una ventana")
            if not recomendaciones:
                recomendaciones.append("todo está estable, sigue así")

            respuesta = (
                f"Tus signos vitales actuales son: temperatura {temp}°C, pulso {bpm} bpm, "
                f"oxígeno {spo2}%. Recomendación: {', '.join(recomendaciones)}."
            )
        else:
            respuesta = "Todavía no tengo tus signos vitales, asegúrate que tu dispositivo esté enviando los datos."

    # --- Preguntas aleatorias ---
    else:
        # Respuesta estándar y dato curioso
        datos_curiosos = [
            "En Perú hay una maravilla del mundo llamada Machu Picchu.",
            "El cerebro humano consume cerca del 20% de la energía del cuerpo.",
            "Beber agua suficiente mejora la concentración y la energía.",
            "Una caminata diaria de 30 minutos ayuda a reducir el estrés."
        ]
        dato = random.choice(datos_curiosos)
        respuesta = (
            f"No estoy diseñado para eso, pero respondiendo a tu pregunta: {mensaje.capitalize()}. "
            f"Dato curioso: {dato}"
        )

    return jsonify({"respuesta": respuesta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
