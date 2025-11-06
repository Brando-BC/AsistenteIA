from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# Almacenamiento temporal de los últimos datos enviados por el ESP32
datos_esp32 = {}
ultima_actualizacion = 0

@app.route('/')
def home():
    return "Servidor Asistente IA funcionando ✅"

# 🛰️ Recibir datos del ESP32
@app.route('/sensores', methods=['POST'])
def recibir_datos():
    global datos_esp32, ultima_actualizacion
    data = request.get_json(force=True)
    print("📡 Datos recibidos del ESP32:", data)

    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    datos_esp32 = data
    ultima_actualizacion = time.time()
    return jsonify({"status": "OK", "mensaje": "Datos actualizados correctamente"}), 200

# 💬 Ruta de interacción de voz (HTML)
@app.route('/ia', methods=['POST'])
def ia_responder():
    global datos_esp32, ultima_actualizacion
    mensaje = request.json.get("mensaje", "").lower().strip()

    print("💬 Pregunta del usuario:", mensaje)

    # Si han pasado más de 2 minutos sin datos nuevos, se reinicia
    if time.time() - ultima_actualizacion > 120:
        datos_esp32 = {}

    respuesta = "Disculpa, no entendí bien lo que quisiste decir. ¿Podrías repetirlo?"

    # --- RESPUESTAS MÁS NATURALES ---
    if "hola" in mensaje:
        respuesta = "Hola, qué gusto escucharte. ¿Cómo te sientes hoy?"

    elif "signos" in mensaje or "vitales" in mensaje or "salud" in mensaje:
        if datos_esp32:
            temp = datos_esp32.get("Temp", 0)
            bpm = datos_esp32.get("BPM", 0)
            spo2 = datos_esp32.get("SpO2", 0)

            # Evaluación rápida con tono humano
            if temp > 37.5:
                estado = "parece que tienes un poco de fiebre, procura descansar y tomar agua."
            elif bpm > 100:
                estado = "tu ritmo cardíaco está algo acelerado, intenta relajarte un poco."
            elif spo2 < 94:
                estado = "tu oxígeno está algo bajo, respira profundo o abre una ventana."
            else:
                estado = "todo se ve estable, sigue así."

            respuesta = (
                f"Tu temperatura es de {temp} grados, tu pulso está en {bpm} latidos por minuto "
                f"y tu oxígeno en {spo2} por ciento. En resumen, {estado}"
            )
        else:
            respuesta = (
                "Aún no tengo tus datos de salud actualizados. "
                "Asegúrate de que el dispositivo esté enviando los signos vitales."
            )

    elif "gracias" in mensaje:
        respuesta = "De nada, siempre estoy aquí para ayudarte."

    elif "adiós" in mensaje or "chau" in mensaje:
        respuesta = "Hasta luego, cuídate mucho."

    else:
        respuesta = (
            "Puedo decirte tus signos vitales, o explicarte si están bien o no. "
            "¿Quieres que revise cómo estás ahora?"
        )

    return jsonify({"respuesta": respuesta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
