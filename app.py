# ================== app.py – Mentor IA Premium Académico ==================
import os, datetime, google.generativeai as genai
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

load_dotenv()
app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# Configuración Gemini
genai.configure(api_key=os.environ.get("API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash', system_instruction="""
Eres el Entrenador Académico experto en bioplásticos, pirólisis y física/química.
Tu meta es enseñar. NO resuelvas tareas directamente. Si te piden un ejercicio, explícalo con ejemplos didácticos.
Penaliza el plagio, premia el parafraseo y da feedback constructivo.
""")

# Base de Datos
db_path = os.path.join(os.path.dirname(__file__), "mentor_db.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    tipo_usuario = db.Column(db.String(20), default="normal")
    consultas_usadas = db.Column(db.Integer, default=0)
    ultima_consulta = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bloques_publicidad_vistos = db.Column(db.Integer, default=0) # Contador 0, 1 o 2
    material = db.Column(db.Text)

with app.app_context():
    db.create_all()

# Lógica de Usuario: 5 (base) + (bloques * 5) = Máximo 15
def puede_usar_consulta(u):
    ahora = datetime.datetime.utcnow()
    # Reset diario si pasaron más de 24hs
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86400:
        u.consultas_usadas = 0
        u.bloques_publicidad_vistos = 0
        db.session.commit()
    
    if u.tipo_usuario == "super": return True
    
    total_permitido = 5 + (u.bloques_publicidad_vistos * 5)
    return u.consultas_usadas < total_permitido

@app.route("/confirmar_publicidad", methods=["POST"])
def confirmar_publicidad():
    u = Usuario.query.get(session.get("usuario_id"))
    if not u: return jsonify({"error": "No logueado"}), 401
    
    if u.bloques_publicidad_vistos < 2:
        u.bloques_publicidad_vistos += 1
        db.session.commit()
        return jsonify({"resultado": "Bloque de 5 consultas activado."})
    return jsonify({"error": "Límite de publicidad alcanzado"}), 400

# Ruta Central de Procesamiento
def procesar_con_ia(tarea, texto, material="", respuesta_extra=""):
    instrucciones = {
        "analizar": "Analiza y explica conceptos.",
        "evaluar": f"Profesor: Evalúa la respuesta '{texto}' para la consigna '{respuesta_extra}'. Calificación 0-10, detecta plagio y da feedback.",
        "resumen": "Genera resumen jerárquico.",
        "mapa_conceptual": "Genera una red conceptual estructurada.",
        "rap": "Crea un rap educativo técnico.",
        "explicar": "Eres el explicador didáctico. Resuelve la duda con ejemplos claros, sin hacer la tarea.",
        "aleatorio": "Genera un ejercicio práctico o concepto aleatorio."
    }
    prompt = f"{instrucciones.get(tarea)}\n\nMaterial: {material}\n\nEntrada: {texto}"
    return model.generate_content(prompt).text

@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    u = Usuario.query.get(session.get("usuario_id"))
    if not u or not puede_usar_consulta(u): 
        return jsonify({"error": "Consultas agotadas. Mira publicidad para más acceso."}), 403
    
    data = request.json
    resultado = procesar_con_ia(tarea, data.get("texto", ""), u.material or "", data.get("respuesta", ""))
    
    if u.tipo_usuario != "super":
        u.consultas_usadas += 1
        u.ultima_consulta = datetime.datetime.utcnow()
        db.session.commit()
    return jsonify({"resultado": resultado})

@app.route("/login_google", methods=["POST"])
def login():
    token = request.json.get("token")
    info = id_token.verify_oauth2_token(token, grequests.Request(), os.environ.get("GOOGLE_CLIENT_ID"))
    u = Usuario.query.filter_by(email=info["email"]).first()
    if not u:
        u = Usuario(email=info["email"], tipo_usuario="super" if info["email"].lower() == "gunmachine786@gmail.com" else "normal")
        db.session.add(u); db.session.commit()
    session["usuario_id"] = u.id
    return jsonify({"tipo": u.tipo_usuario})

if __name__ == "__main__": app.run()
    
