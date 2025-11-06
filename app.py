from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# Datos del ESP32 y última actualización
datos_esp32 = {}
ultima_actualizacion = 0

@app.route('/')
def home():
    return "Servidor Asistente IA funcionando ✅"

# Recibir datos de sensores del ESP32
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

# Responder a preguntas del usuario
@app.route('/ia', methods=['POST'])
def ia_responder():
    global datos_esp32, ultima_actualizacion
    mensaje = request.json.get("mensaje", "").lower().strip()
    print("💬 Pregunta del usuario:", mensaje)

    # Reinicia datos si no hay actualización reciente
    if time.time() - ultima_actualizacion > 120:
        datos_esp32 = {}

    respuesta = "Disculpa, no entendí bien. ¿Puedes repetirlo?"

    # --- Preguntas sobre signos vitales o salud ---
    if "signos" in mensaje or "vitales" in mensaje or "salud" in mensaje:
        if datos_esp32:
            temp = datos_esp32.get("Temp", 0)
            bpm = datos_esp32.get("BPM", 0)
            spo2 = datos_esp32.get("SpO2", 0)

            # Evaluación simple con recomendaciones
            recomendaciones = []
            if temp > 37.5:
                recomendaciones.append("parece que tienes fiebre, descansa y toma agua")
            if bpm > 100:
                recomendaciones.append("tu pulso está acelerado, intenta relajarte")
            if spo2 < 94:
                recomendaciones.append("tu oxígeno está un poco bajo, respira profundo o abre una ventana")
            if not recomendaciones:
                recomendaciones.append("todo se ve estable, sigue así")

            respuesta = (
                f"Tus signos vitales actuales son: temperatura {temp}°C, pulso {bpm} bpm, "
                f"oxígeno {spo2}%. Recomendación: {', '.join(recomendaciones)}."
            )
        else:
            respuesta = (
                "Todavía no tengo tus signos vitales. Asegúrate de que tu dispositivo esté enviando los datos."
            )

    # --- Preguntas sobre actividades saludables ---
    elif "qué puedo hacer hoy" in mensaje or "actividades" in mensaje or "planes" in mensaje:
        if datos_esp32:
            temp = datos_esp32.get("Temp", 0)
            bpm = datos_esp32.get("BPM", 0)
            spo2 = datos_esp32.get("SpO2", 0)

            sugerencias = []
            if temp < 37.5 and bpm < 100 and spo2 >= 94:
                sugerencias = ["puedes ir a caminar", "hacer un poco de ejercicio ligero", "salir a comer algo"]
            else:
                sugerencias = ["mejor descansa un poco", "toma agua y mantente hidratado", "evita actividades exigentes"]

            respuesta = "Según tus signos vitales actuales, " + ", ".join(sugerencias) + "."
        else:
            respuesta = "No tengo tus datos de salud, pero intenta mantenerte activo según cómo te sientas."

    # --- Preguntas aleatorias o generales ---
    else:
        respuesta = (
            "Estoy diseñado principalmente para dar recomendaciones basadas en tus signos vitales. "
            "Pero respondiendo a tu pregunta: " + mensaje.capitalize()
        )

    return jsonify({"respuesta": respuesta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
