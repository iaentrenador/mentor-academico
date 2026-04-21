import os
import logging
import datetime
import json
import random
from groq import Groq
from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth

# --- CONFIGURACIÓN ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='dist', static_url_path='/')
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get("SECRET_KEY", "proyect_upe_secret")

# --- DB ---
db_uri = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri.replace("postgres://", "postgresql://", 1) if db_uri else 'sqlite:///local.db'
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    consultas_usadas = db.Column(db.Integer, default=0)
    bloques_ad_vistos = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

# --- IA ---
client = Groq(api_key=os.environ.get("API_KEY"))
MODEL_ID = "llama-3.3-70b-versatile"

def llamar_groq(system_prompt, user_prompt):
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model=MODEL_ID,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error IA: {e}")
        return None

# --- HELPERS ---
def get_user():
    uid = session.get("usuario_id")
    return db.session.get(Usuario, uid) if uid else None

def creditos_restantes(u):
    return (4 + u.bloques_ad_vistos * 2) - u.consultas_usadas

# --- RUTAS QUE FALTABAN O FALLABAN ---

@app.route("/api/usuario")
def info_usuario():
    u = get_user()
    if not u: return jsonify({"logueado": False, "restantes": 0})
    return jsonify({"logueado": True, "email": u.email, "restantes": creditos_restantes(u), "total_hoy": 4 + u.bloques_ad_vistos * 2, "url_ad": "https://google.com"})

@app.route("/api/explicar_concepto", methods=["POST"])
def explicar():
    u = get_user()
    if not u or creditos_restantes(u) <= 0: return jsonify({"error": "Sin créditos"}), 403
    data = request.json
    # IMPORTANTE: El frontend espera 'resultado' como un objeto con 'explicacion', 'puntos_clave', etc.
    sys = "Eres Mentor IA UPE. Responde JSON con campos: 'explicacion', 'puntos_clave' (lista), 'ejemplo_practico'."
    res = llamar_groq(sys, f"Tema: {data.get('pregunta')}. Contexto: {data.get('texto')}")
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": res, "restantes": creditos_restantes(u)})

@app.route("/api/generar_red", methods=["POST"])
def red():
    u = get_user()
    if not u: return jsonify({"error": "No login"}), 401
    data = request.json
    sys = "Genera una red conceptual. JSON con 'nodos' (id, label) y 'enlaces' (from, to)."
    res = llamar_groq(sys, data.get('texto'))
    u.consultas_usadas += 1
    db.session.commit()
    # El frontend espera 'resultado' conteniendo la red
    return jsonify({"resultado": res, "restantes": creditos_restantes(u)})

@app.route("/api/math/explain", methods=["POST"])
def math_ex():
    u = get_user()
    data = request.json
    sys = "Profesor de Matemática UPE. JSON con 'explicacion', 'pasos' (lista), 'resultado_final'."
    res = llamar_groq(sys, data.get('exercise'))
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": res, "restantes": creditos_restantes(u)})

@app.route("/api/generar_resumen", methods=["POST"])
def resumen():
    u = get_user()
    data = request.json
    sys = "Experto en Higiene y Seguridad UPE. Genera un resumen técnico detallado. JSON con campo 'resultado'."
    res = llamar_groq(sys, data.get('content'))
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": res.get("resultado", res), "restantes": creditos_restantes(u)})

@app.route("/api/corregir_escrito", methods=["POST"])
def corregir():
    u = get_user()
    data = request.json
    sys = "Inspector de Higiene y Seguridad UPE. Corrije el informe. JSON con 'resultado' (objeto con 'texto_corregido', 'observaciones', 'grade')."
    res = llamar_groq(sys, data.get('writing'))
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": res.get("resultado", res), "restantes": creditos_restantes(u)})

# --- RUTA DE EXAMEN (La más compleja) ---
@app.route("/api/exam/generate", methods=["POST"])
def gen_exam():
    u = get_user()
    data = request.json
    sys = "Genera examen UPE. JSON con campo 'preguntas' que es una lista de objetos {id, tipo, pregunta, opciones, respuesta_correcta}."
    res = llamar_groq(sys, f"Materia: Higiene y Seguridad. Tema: {data.get('material')}")
    u.consultas_usadas += 1
    db.session.commit()
    # El frontend de examen espera el objeto directo con las preguntas
    return jsonify(res)

# --- RUTAS DE SISTEMA ---
@app.route("/login")
def login(): return redirect("/callback") # Simplificado para test

@app.route("/callback")
def cb():
    # Simulación de login para testear rápido si no tienes el client_id configurado
    u = Usuario.query.filter_by(email="test@upe.edu.ar").first()
    if not u:
        u = Usuario(email="test@upe.edu.ar")
        db.session.add(u)
        db.session.commit()
    session["usuario_id"] = u.id
    return redirect("/")

@app.route("/")
def index(): return send_from_directory('dist', 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
