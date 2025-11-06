from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# Base de datos simulada en memoria
datos_esp32 = {}
ultima_actualizacion = 0

@app.route('/')
def home():
    return "Servidor Asistente IA funcionando ✅"

# 🛰️ Ruta para recibir datos del ESP32
@app.route('/sensores', methods=['POST'])
def recibir_datos():
    global datos_esp32, ultima_actualizacion
    data = request.get_json(force=True)
    print("📡 Datos recibidos del ESP32:", data)

    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    datos_esp32 = data
    ultima_actualizacion = time.time()
    return jsonify({"status": "OK", "mensaje": "Datos guardados correctamente"}), 200

# 💬 Ruta de IA (para HTML o ESP32)
@app.route('/ia', methods=['POST'])
def ia_responder():
    global datos_esp32
    mensaje = request.json.get("mensaje", "").lower()

    print("💬 Mensaje recibido de IA:", mensaje)

    # Si han pasado más de 2 minutos sin datos nuevos del ESP32, se limpia
    if time.time() - ultima_actualizacion > 120:
        datos_esp32 = {}

    if "signos" in mensaje or "vitales" in mensaje:
        if datos_esp32:
            temp = datos_esp32.get("Temp", "N/A")
            bpm = datos_esp32.get("BPM", "N/A")
            spo2 = datos_esp32.get("SpO2", "N/A")

            respuesta = (
                f"📊 Tus signos vitales actuales son:\n"
                f"• Temperatura: {temp} °C\n"
                f"• Frecuencia cardíaca: {bpm} BPM\n"
                f"• Saturación de oxígeno: {spo2}%.\n"
            )

            # Diagnóstico básico
            if temp > 37.5:
                respuesta += "🌡️ Tienes fiebre, cuídate y mantente hidratado."
            elif bpm > 100:
                respuesta += "❤️ Tu frecuencia cardíaca está un poco alta, intenta relajarte."
            elif spo2 < 94:
                respuesta += "🫁 Saturación baja, procura respirar aire fresco."
            else:
                respuesta += "✅ Todos los valores se encuentran dentro de lo normal."
        else:
            respuesta = (
                "⚠️ Aún no tengo datos de tus sensores. "
                "Por favor, asegúrate de que el ESP32 esté enviando correctamente."
            )

    else:
        respuesta = (
            "Hola 👋 Soy tu asistente de salud. "
            "Puedes preguntarme cosas como: '¿Cuáles son mis signos vitales actuales?'"
        )

    return jsonify({"respuesta": respuesta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
