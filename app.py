from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, db

# ------------------------------------------------------------
# CONFIGURACIÓN DE FLASK
# ------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# ------------------------------------------------------------
# CONFIGURACIÓN DE FIREBASE (usando variable de entorno segura)
# ------------------------------------------------------------
firebase_key_env = os.getenv("FIREBASE_KEY")

if firebase_key_env:
    try:
        cred_data = json.loads(firebase_key_env)
        cred = credentials.Certificate(cred_data)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://asistente-signos-vitales-default-rtdb.firebaseio.com/"
        })
        print("✅ Firebase inicializado correctamente con variable de entorno.")
    except Exception as e:
        print("⚠️ Error al inicializar Firebase:", e)
else:
    print("⚠️ No se encontró la variable FIREBASE_KEY. Firebase no se inicializará.")

# ------------------------------------------------------------
# CONFIGURACIÓN DE OPENAI
# ------------------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------------------------------------------
# PARÁMETROS NORMALES (fuente: OMS, NIH, Mayo Clinic)
# ------------------------------------------------------------
parametros_normales = {
    "temperatura": (36.1, 37.2),        # °C
    "frecuencia_cardiaca": (60, 100),   # lpm
    "spo2": (95, 100),                  # %
    "presion_sistolica": (90, 120),     # mmHg
    "presion_diastolica": (60, 80)      # mmHg
}

# ------------------------------------------------------------
# RUTA PRINCIPAL
# ------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ------------------------------------------------------------
# RECIBIR DATOS DEL ESP32 Y GUARDAR EN FIREBASE
# ------------------------------------------------------------
@app.route("/sensores", methods=["POST"])
def recibir_datos():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400

        # Agrega un timestamp a los datos
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if firebase_admin._apps:
            ref = db.reference("signos_vitales")
            ref.push(data)
            print("📡 Datos guardados en Firebase:", data)
        else:
            print("⚠️ Firebase no inicializado, datos no guardados:", data)

        return jsonify({"status": "ok", "mensaje": "Datos recibidos y guardados correctamente"}), 200
    except Exception as e:
        print("⚠️ Error:", e)
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------
# CONSULTAR ÚLTIMO DATO REGISTRADO
# ------------------------------------------------------------
@app.route("/ultimo", methods=["GET"])
def obtener_ultimo():
    try:
        if not firebase_admin._apps:
            return jsonify({"error": "Firebase no está inicializado"}), 500

        ref = db.reference("signos_vitales")
        data = ref.order_by_key().limit_to_last(1).get()

        if data:
            ultimo = list(data.values())[0]
            return jsonify(ultimo)
        else:
            return jsonify({"mensaje": "No hay datos en Firebase"}), 404
    except Exception as e:
        print("⚠️ Error al obtener datos:", e)
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------
# CHAT CON IA MÉDICA
# ------------------------------------------------------------
@app.route("/ia", methods=["POST"])
def ia_responder():
    try:
        mensaje = request.json.get("mensaje", "").strip()
        if not mensaje:
            return jsonify({"respuesta": "No se recibió ningún mensaje"}), 400

        # Crear contexto médico para la IA
        prompt = (
            "Eres un asistente médico llamado Brani. Analiza los signos vitales con empatía, claridad y según estándares médicos confiables. "
            "Parámetros normales: "
            f"Temperatura {parametros_normales['temperatura'][0]}-{parametros_normales['temperatura'][1]} °C, "
            f"Frecuencia cardíaca {parametros_normales['frecuencia_cardiaca'][0]}-{parametros_normales['frecuencia_cardiaca'][1]} lpm, "
            f"Saturación de oxígeno {parametros_normales['spo2'][0]}-{parametros_normales['spo2'][1]} %, "
            f"Presión arterial {parametros_normales['presion_sistolica'][0]}/{parametros_normales['presion_diastolica'][0]} "
            f"a {parametros_normales['presion_sistolica'][1]}/{parametros_normales['presion_diastolica'][1]} mmHg. "
            f"Consulta del usuario: {mensaje}"
        )

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente médico empático, experto en signos vitales, que ofrece consejos generales, nunca diagnósticos clínicos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=250
        )

        respuesta = completion.choices[0].message.content.strip()
        return jsonify({"respuesta": respuesta})

    except Exception as e:
        print("⚠️ Error con IA:", e)
        return jsonify({"respuesta": "Ocurrió un error al procesar la respuesta de la IA."})

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
