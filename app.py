import os
import logging
import datetime
import json
import random
from groq import Groq
from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, Index
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message
from werkzeug.middleware.proxy_fix import ProxyFix

# --- CONFIGURACIÓN E INFRAESTRUCTURA ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definición de puerto para Render/Local
port = int(os.environ.get("PORT", 5000))

dist_path = os.path.join(os.path.dirname(__file__), 'dist')
if not os.path.exists(dist_path):
    os.makedirs(dist_path, exist_ok=True)

app = Flask(__name__, static_folder=dist_path, static_url_path='/')

# FIX: ProxyFix configurado para la arquitectura de Render (resuelve MismatchingStateError)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
if not allowed_origins_raw:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173", "https://mentor-academico-0cn1.onrender.com"]
else:
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

CORS(app, origins=allowed_origins, supports_credentials=True)

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_provisional")

# --- CONFIGURACIÓN DE BASE DE DATOS ---
db_uri_raw = os.environ.get("DATABASE_URL")
if db_uri_raw:
    db_uri = db_uri_raw.replace("postgres://", "postgresql://", 1).split("?")[0]
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {"sslmode": "require"}
    }
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_uri = 'sqlite:///' + os.path.join(basedir, 'local.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)

# FIX: Configuración de cookies para entorno producción HTTPS
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True 

mail = Mail(app)
db = SQLAlchemy(app)

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

api_key = os.environ.get("API_KEY")
if not api_key:
    raise ValueError("Falta la variable de entorno API_KEY")
client = Groq(api_key=api_key)
MODEL_ID = "llama-3.3-70b-versatile"

# --- CONSTANTES Y PERFILES ---
PERFILES_MATERIA = {
    "higiene_upe": "ROL: Inspector Técnico de Higiene y Seguridad (UPE). Rigor legal y técnico máximo.",
    "politica_upe": "ROL: Mentor de Política y Sociedad (UPE).",
    "matematica_propedutico": "ROL: Profesor del Ciclo Propedéutico UPE. Tono motivador pero firme.",
}

# --- MODELO ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    consultas_usadas = db.Column(db.Integer, default=0, nullable=False)
    bloques_publicidad_vistos = db.Column(db.Integer, default=0, nullable=False)
    creditos_comprados = db.Column(db.Integer, default=0, nullable=False)
    material = db.Column(db.Text, default="")
    perfil_aprendizaje = db.Column(db.Text, default="{}")

# --- INICIALIZACIÓN DE BD ---
try:
    with app.app_context():
        db.create_all()
except Exception as e:
    logger.error(f"Error en DB: {e}")

# --- HELPERS ---
def get_usuario_actual():
    uid = session.get("usuario_id")
    return db.session.get(Usuario, uid) if uid else None

def consultas_permitidas(u):
    return 4 + (u.bloques_publicidad_vistos * 2) + u.creditos_comprados

def creditos_restantes(u):
    return max(consultas_permitidas(u) - u.consultas_usadas, 0)

def llamar_groq(prompt: str, system_prompt: str = "Eres el Mentor Académico UPE. Responde solo en JSON técnico.") -> dict:
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model=MODEL_ID,
            response_format={"type": "json_object"},
            timeout=45
        )
        raw = chat_completion.choices[0].message.content
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Error en llamada a Groq: {e}")
        raise RuntimeError(f"Error al contactar el servicio de IA: {str(e)}")

def descontar_consulta(u: Usuario) -> bool:
    try:
        u.consultas_usadas += 1
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False

def obtener_campo(data: dict, campo: str, tipo=str, default=None, requerido=False):
    valor = data.get(campo, default)
    if requerido and valor is None:
        return None, f"El campo '{campo}' es requerido."
    if valor is not None:
        try:
            valor = tipo(valor)
        except (ValueError, TypeError):
            return None, f"El campo '{campo}' debe ser de tipo {tipo.__name__}."
    return valor, None

# --- RUTAS API ---

@app.route("/api/explicar_concepto", methods=["POST"])
def explicar_concepto():
    u = get_usuario_actual()
    if not u or creditos_restantes(u) <= 0:
        return jsonify({"error": "Sin créditos"}), 403
    data = request.json or {}
    pregunta, err = obtener_campo(data, "pregunta", requerido=True)
    if err: return jsonify({"error": err}), 400
    sys = "Eres Mentor IA UPE. Responde JSON con campos: 'explicacion', 'puntos_clave' (lista), 'ejemplo_practico'."
    try:
        resultado = llamar_groq(f"Tema: {pregunta}. Contexto: {data.get('texto', '')}", system_prompt=sys)
        descontar_consulta(u)
        return jsonify({"resultado": resultado, "restantes": creditos_restantes(u)})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/generar_resumen", methods=["POST"])
def generar_resumen():
    u = get_usuario_actual()
    if not u or creditos_restantes(u) <= 0: return jsonify({"error": "Sin créditos"}), 403
    data = request.json or {}
    contenido, err = obtener_campo(data, "content", requerido=True)
    if err: return jsonify({"error": err}), 400
    sys = "Experto en Higiene y Seguridad UPE. Genera un resumen técnico detallado. JSON con campo 'resultado'."
    try:
        res = llamar_groq(contenido, system_prompt=sys)
        descontar_consulta(u)
        return jsonify({"resultado": res.get("resultado", res), "restantes": creditos_restantes(u)})
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/math_logic", methods=["POST"])
def math_logic():
    u = get_usuario_actual()
    if not u or creditos_restantes(u) <= 0: return jsonify({"error": "Sin créditos"}), 403
    data = request.json or {}
    tipo, _ = obtener_campo(data, "tipo", default="explicar")
    prompt = f"{PERFILES_MATERIA['matematica_propedutico']} Tarea: {tipo}. Ejercicio: {data.get('ejercicio')}. Responde JSON con 'explicacion', 'pasos', 'resultado'."
    try:
        resultado = llamar_groq(prompt)
        descontar_consulta(u)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/generar_examen", methods=["POST"])
def generar_examen():
    u = get_usuario_actual()
    if not u or creditos_restantes(u) <= 0: return jsonify({"error": "Sin créditos"}), 403
    data = request.json or {}
    cantidad, _ = obtener_campo(data, "cantidad", tipo=int, default=5)
    prompt = f"{PERFILES_MATERIA['higiene_upe']} Genera {cantidad} preguntas de: {data.get('contenido')}. JSON con lista 'preguntas' con id, tipo, pregunta, opciones, respuesta_correcta."
    try:
        resp_json = llamar_groq(prompt)
        for p in resp_json.get("preguntas", []):
            if p.get("tipo") == "Opción Múltiple": random.shuffle(p["opciones"])
        descontar_consulta(u)
        return jsonify(resp_json)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/generar_red", methods=["POST"])
def generar_red():
    u = get_usuario_actual()
    if not u or creditos_restantes(u) <= 0: return jsonify({"error": "Sin créditos"}), 403
    data = request.json or {}
    prompt = f"Genera red conceptual: {data.get('texto')}. JSON con 'nodos' (id, label) y 'enlaces' (source, target)."
    try:
        resultado = llamar_groq(prompt)
        descontar_consulta(u)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/corregir_escrito", methods=["POST"])
def corregir_escrito():
    u = get_usuario_actual()
    if not u or creditos_restantes(u) <= 0: return jsonify({"error": "Sin créditos"}), 403
    data = request.json or {}
    prompt = f"{PERFILES_MATERIA['higiene_upe']} Corrige: {data.get('texto')}. JSON: 'texto_corregido', 'observaciones_legales', 'nota'."
    try:
        resultado = llamar_groq(prompt)
        descontar_consulta(u)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/usuario")
def info_usuario():
    u = get_usuario_actual()
    if not u: return jsonify({"logueado": False, "restantes": 0})
    return jsonify({
        "logueado": True,
        "email": u.email,
        "restantes": creditos_restantes(u),
        "total_hoy": consultas_permitidas(u),
        "url_ad": "https://google.com"
    })

# Aliases de rutas
app.add_url_rule("/api/exam/generate", view_func=generar_examen, methods=["POST"])
app.add_url_rule("/api/text/correct", view_func=corregir_escrito, methods=["POST"])
app.add_url_rule("/api/math/explain", view_func=math_logic, methods=["POST"])

# --- RUTAS AUTH ---
@app.route("/login")
def login():
    return google.authorize_redirect(url_for("callback", _external=True))

@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    userinfo = token.get("userinfo")
    u = Usuario.query.filter_by(email=userinfo['email']).first()
    if not u:
        u = Usuario(email=userinfo['email'])
        db.session.add(u)
        db.session.commit()
    session["usuario_id"] = u.id
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
