import os
import logging
import datetime
import json
import random
from groq import Groq
from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail

# --- CONFIGURACIÓN E INFRAESTRUCTURA ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

port = int(os.environ.get("PORT", 5000))
dist_path = os.path.join(os.path.dirname(__file__), 'dist')
if not os.path.exists(dist_path):
    os.makedirs(dist_path, exist_ok=True)

app = Flask(__name__, static_folder=dist_path, static_url_path='/')

# Configuración de CORS dinámica
allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")] if allowed_origins_raw else ["http://localhost:5173", "https://mentor-academico-0cn1.onrender.com"]
CORS(app, origins=allowed_origins, supports_credentials=True)

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_upe_2024")

# --- CONFIGURACIÓN DE BASE DE DATOS (Postgres / SQLite) ---
db_uri_raw = os.environ.get("DATABASE_URL")
if db_uri_raw:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri_raw.replace("postgres://", "postgresql://", 1)
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'local.db')

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- MODELO DE USUARIO (Para la Tienda y Créditos) ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    consultas_usadas = db.Column(db.Integer, default=0)
    bloques_ad_vistos = db.Column(db.Integer, default=0)
    creditos_comprados = db.Column(db.Integer, default=0)
    perfil_aprendizaje = db.Column(db.Text, default="{}")

with app.app_context():
    db.create_all()

# --- IA Y AUTH ---
client = Groq(api_key=os.environ.get("API_KEY"))
MODEL_ID = "llama-3.3-70b-versatile"

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# --- HELPERS DE NEGOCIO ---
def get_usuario_actual():
    uid = session.get("usuario_id")
    if not uid: return None
    return db.session.get(Usuario, uid)

def consultas_permitidas(u):
    # 4 base + 2 por cada anuncio + comprados
    return 4 + (u.bloques_ad_vistos * 2) + u.creditos_comprados

def llamar_groq(system_prompt, user_prompt):
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=MODEL_ID,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error Groq: {e}")
        return {"error": "Servicio de IA temporalmente fuera de línea."}

# --- RUTAS DE API (Sincronizadas con App.tsx) ---

@app.route("/api/usuario")
def info_usuario():
    u = get_usuario_actual()
    if not u: return jsonify({"logueado": False, "restantes": 0})
    restantes = consultas_permitidas(u) - u.consultas_usadas
    return jsonify({
        "logueado": True,
        "email": u.email,
        "restantes": max(0, restantes),
        "total_hoy": consultas_permitidas(u),
        "url_ad": "https://www.google.com" # Aquí iría tu link de afiliado o ad
    })

@app.route("/api/registrar_ad", methods=["POST"])
def registrar_ad():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No logueado"}), 401
    u.bloques_ad_vistos += 1
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/explicar_concepto", methods=["POST"])
def explicar_concepto():
    u = get_usuario_actual()
    if not u or (consultas_permitidas(u) - u.consultas_usadas) <= 0:
        return jsonify({"error": "Sin créditos"}), 403
    
    data = request.json
    prompt_sistema = f"Eres el Mentor Académico UPE. Especialidad: {data.get('materia')}. Responde en JSON con campo 'resultado'."
    prompt_usuario = f"Explica esto: {data.get('pregunta')} basado en: {data.get('texto')}. Modo legal: {data.get('modo_legal')}"
    
    res = llamar_groq(prompt_sistema, prompt_usuario)
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": res.get("resultado"), "restantes": consultas_permitidas(u) - u.consultas_usadas})

@app.route("/api/generar_red", methods=["POST"])
def generar_red():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No logueado"}), 401
    
    data = request.json
    prompt_sistema = "Eres un experto en mapas conceptuales. Genera JSON con 'nodos' (id, label) y 'enlaces' (from, to)."
    prompt_usuario = f"Crea una red conceptual de: {data.get('texto')}"
    
    res = llamar_groq(prompt_sistema, prompt_usuario)
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": res, "restantes": consultas_permitidas(u) - u.consultas_usadas})

@app.route("/api/math/explain", methods=["POST"])
def math_explain():
    u = get_usuario_actual()
    data = request.json
    prompt_sistema = "Eres profesor de matemáticas UPE. Responde JSON con 'resultado' (pasos en LaTeX)."
    res = llamar_groq(prompt_sistema, f"Explica: {data.get('exercise')} de {data.get('topic')}")
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": res.get("resultado"), "restantes": consultas_permitidas(u) - u.consultas_usadas})

# --- RUTAS DE AUTH ---
@app.route("/login")
def login():
    return google.authorize_redirect(url_for("callback", _external=True))

@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    u = Usuario.query.filter_by(email=user_info['email']).first()
    if not u:
        u = Usuario(email=user_info['email'])
        db.session.add(u)
        db.session.commit()
    session["usuario_id"] = u.id
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/")
def serve():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
