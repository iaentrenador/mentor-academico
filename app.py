import os
import logging
import datetime
import json
from groq import Groq
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message

# --- CONFIGURACIÓN E INFRAESTRUCTURA (MANTENIDO) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
CORS(app, origins=allowed_origins)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise ValueError("Falta la variable de entorno SECRET_KEY")
app.secret_key = secret_key

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///local.db").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

# Configuración Mail
app.config.update(
    MAIL_SERVER=os.environ.get("MAIL_SERVER", 'smtp.gmail.com'),
    MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD")
)
mail = Mail(app)
db = SQLAlchemy(app)

# OAuth & Groq Init
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

client = Groq(api_key=os.environ.get("API_KEY"))
MODEL_ID = "llama-3.3-70b-versatile"

# --- CONSTANTES Y PERFILES (AJUSTADO) ---
TAREAS_VALIDAS = {"explicar", "resumir", "evaluar", "cargar_material", "preparar_oratoria"}
MAX_TEXTO, MAX_MATERIAL, PERFIL_MAX = 15_000, 50_000, 2_000
CONSULTAS_BASE, CONSULTAS_POR_AD, MAX_BLOQUES_PUBLICIDAD = 5, 5, 2

PERFILES_MATERIA = {
    "higiene": "ROL: Inspector Técnico de Higiene y Seguridad. REGLA: Exige rigor legal (Ley 19587/72 y decretos).",
    "matematica": "ROL: Tutor de Matemática UPE. Explica pasos y teclas de calculadora científica. Usa andamiaje.",
    "politica": "ROL: Mentor de Oratoria y Política. Enfócate en conceptos de Estado, Poder y argumentación.",
}

# --- MODELOS Y HELPERS (MANTENIDO) ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    consultas_usadas = db.Column(db.Integer, default=0, nullable=False)
    ultima_consulta = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bloques_publicidad_vistos = db.Column(db.Integer, default=0, nullable=False)
    material = db.Column(db.Text, default="")
    perfil_aprendizaje = db.Column(db.Text, default="")

with app.app_context():
    db.create_all()

def get_usuario_actual():
    uid = session.get("usuario_id")
    return db.session.get(Usuario, uid) if uid else None

def resetear_si_nuevo_dia(u):
    ahora = datetime.datetime.utcnow()
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86_400:
        u.consultas_usadas = 0
        u.bloques_publicidad_vistos = 0
        db.session.commit()

# --- IA LOGIC: EL NUEVO CEREBRO (SOPORTE TRIPLE BLOQUE + JSON) ---
def ejecutar_tarea_ia(tarea, texto, material, usuario, materia="general", consigna=""):
    perfil_materia = PERFILES_MATERIA.get(materia, "ROL: Mentor Académico Universitario.")
    
    prompt_sistema = f"""{perfil_materia}
    Eres el 'Mentor IA'. Tu objetivo es el entrenamiento cognitivo. 
    REGLAS: 1. Usa andamiaje (pistas, no soluciones). 2. Si la tarea es 'evaluar', responde SOLO en JSON.
    HISTORIAL: {usuario.perfil_aprendizaje}"""

    if tarea == "evaluar":
        content = f"CONSIGNA: {consigna}\nMATERIAL: {material}\nRESPUESTA ALUMNO: {texto}\nAnaliza rigurosamente."
        response_format = {"type": "json_object"}
    else:
        content = f"CONTEXTO: {material}\nACCIÓN: {tarea}\nENTRADA: {texto}"
        response_format = {"type": "text"}

    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": content}],
            temperature=0.7,
            response_format=response_format
        )
        res = completion.choices[0].message.content
        usuario.perfil_aprendizaje = f"[{tarea[:3]}] {res[:50]}...\n{usuario.perfil_aprendizaje}"[:PERFIL_MAX]
        return res
    except Exception as e:
        logger.error(f"Error Groq: {e}")
        return None

# --- RUTAS API (MONETIZACIÓN Y AUTH INTACTAS) ---
@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    if tarea not in TAREAS_VALIDAS: return jsonify({"error": "Tarea inválida"}), 400
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401

    if tarea == "cargar_material":
        u.material = request.json.get("material", "")
        db.session.commit()
        return jsonify({"res": "Material cargado"})

    resetear_si_nuevo_dia(u)
    permitidas = CONSULTAS_BASE + (u.bloques_publicidad_vistos * CONSULTAS_POR_AD)
    if u.consultas_usadas >= permitidas: return jsonify({"error": "Consultas agotadas"}), 403

    data = request.json
    res = ejecutar_tarea_ia(tarea, data.get("writing", data.get("texto", "")), u.material, u, data.get("materia", "general"), data.get("prompt", ""))
    
    if res:
        u.consultas_usadas += 1
        db.session.commit()
        return jsonify({"resultado": json.loads(res) if tarea == "evaluar" else res, "restantes": permitidas - u.consultas_usadas})
    return jsonify({"error": "Error IA"}), 500

# Rutas de Auth, Login, Callback, Logout, Anuncios y Examen se mantienen igual...
# (Omitidas aquí por brevedad, pero conservalas en tu archivo real)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
