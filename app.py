from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os
import openai  # Asegúrate de instalarlo: pip install openai

app = Flask(__name__)
CORS(app)

# --- API KEY de OpenAI ---
openai.api_key = os.getenv("OPENAI_API_KEY")  # o pon tu clave directamente si estás en entorno local

# --- Variables globales ---
datos_esp32 = {}
ultima_actualizacion = 0


@app.route('/')
def home():
    return "🤖 Servidor Asistente Inteligente con ESP32 activo"


# 🛰️ Recibe datos del ESP32
@app.route('/sensores', methods=['POST'])
def recibir_datos():
    global datos_esp32, ultima_actualizacion
    data = request.get_json(force=True)
    print("📡 Datos recibidos del ESP32:", data)

    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    datos_esp32 = data
    ultima_actualizacion = time.time()
    return jsonify({"status": "OK", "mensaje": "Datos de salud actualizados correctamente"}), 200


# 💬 Ruta principal para responder preguntas desde el HTML
@app.route('/ia', methods=['POST'])
def ia_responder():
    global datos_esp32, ultima_actualizacion
    mensaje = request.json.get("mensaje", "").lower().strip()
    print("💬 Usuario:", mensaje)

    # Si han pasado más de 2 minutos sin datos, reiniciar
    if time.time() - ultima_actualizacion > 120:
        datos_esp32 = {}

    # --- Detección de tema de salud ---
    temas_salud = ["salud", "signos", "vitales", "presión", "oxígeno", "temperatura", "bienestar", "cansado", "fatiga", "pulso", "bpm", "spo2", "fiebre"]
    es_salud = any(palabra in mensaje for palabra in temas_salud)

    if es_salud and datos_esp32:
        temp = datos_esp32.get("Temp", 0)
        bpm = datos_esp32.get("BPM", 0)
        spo2 = datos_esp32.get("SpO2", 0)

        estado = ""
        if temp > 37.5:
            estado = "parece que tienes un poco de fiebre. Procura descansar y mantenerte hidratado."
        elif bpm > 100:
            estado = "tu ritmo cardíaco está algo elevado. Intenta respirar profundo o relajarte un poco."
        elif spo2 < 94:
            estado = "tu nivel de oxígeno está algo bajo. Respira profundo o sal a tomar aire fresco."
        else:
            estado = "todo parece estable. Sigue cuidándote."

        respuesta = (
            f"Tu temperatura es de {temp} grados, tu pulso está en {bpm} latidos por minuto "
            f"y tu nivel de oxígeno es de {spo2} por ciento. En general, {estado}"
        )
        return jsonify({"respuesta": respuesta})

    elif es_salud and not datos_esp32:
        return jsonify({"respuesta": "No tengo tus datos de salud actualizados. Asegúrate de que el ESP32 esté enviando información."})

    # --- Para todo lo demás: usar IA general ---
    try:
        prompt = (
            f"Eres un asistente amable y útil llamado Brani. "
            f"Responde de forma natural, clara y sin tecnicismos. "
            f"Pregunta del usuario: {mensaje}"
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # modelo ligero, rápido y económico
            messages=[{"role": "system", "content": "Eres un asistente conversacional inteligente y empático."},
                      {"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )

        respuesta = response.choices[0].message["content"].strip()
        return jsonify({"respuesta": respuesta})

    except Exception as e:
        print("⚠️ Error con OpenAI:", e)
        return jsonify({"respuesta": "Hubo un problema al generar la respuesta de la IA."})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
