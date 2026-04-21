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

# --- CONFIGURACIÓN E INFRAESTRUCTURA ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

port = int(os.environ.get("PORT", 5000))

dist_path = os.path.join(os.path.dirname(__file__), 'dist')
if not os.path.exists(dist_path):
    os.makedirs(dist_path, exist_ok=True)

app = Flask(__name__, static_folder=dist_path, static_url_path='/')

allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
if not allowed_origins_raw:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173", "https://mentor-academico-0cn1.onrender.com"]
else:
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

CORS(app, origins=allowed_origins, supports_credentials=True)

secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_provisional")
app.secret_key = secret_key

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
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

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
ACADEMIC_COACH_PERSONA = "Eres un entrenador académico universitario estricto y pedagógico."

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

def llamar_groq(prompt: str) -> dict:
    try:
        prompt_estricto = prompt + "\n\nIMPORTANTE: Responde ÚNICAMENTE con el objeto JSON solicitado. No incluyas explicaciones fuera del JSON."
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_estricto}],
            model=MODEL_ID,
            response_format={"type": "json_object"},
            timeout=40
        )
        raw = chat_completion.choices[0].message.content
        logger.info(f"RESPUESTA IA RECIBIDA: {raw}") 
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Groq devolvió JSON inválido: {e}")
        raise ValueError("La IA devolvió un formato incorrecto. Reintenta la operación.")
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
        logger.error(f"Error al guardar consulta: {e}")
        return False

def obtener_campo(data: dict, campo: str, tipo=str, default=None, requerido=False):
    valor = data.get(campo, default)
    if requerido and (valor is None or valor == ""):
        return None, f"El campo '{campo}' es requerido."
    if valor is not None:
        try:
            valor = tipo(valor)
        except (ValueError, TypeError):
            return None, f"El campo '{campo}' debe ser {tipo.__name__}."
    return valor, None

# --- RUTAS: MATEMÁTICAS (Sincronizada) ---

@app.route("/api/math/logic", methods=["POST"])
def math_logic():
    u = get_usuario_actual()
    if not u or u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({"error": "No autorizado o sin créditos"}), 403

    data = request.json or {}
    tipo, err = obtener_campo(data, "tipo", requerido=True)
    tema, err2 = obtener_campo(data, "tema", requerido=True)
    ejercicio, err3 = obtener_campo(data, "ejercicio", requerido=True)
    if err or err2 or err3:
        return jsonify({"error": err or err2 or err3}), 400

    resolucion_alumno = data.get("resolucion", "")
    prompt = f"""
    {PERFILES_MATERIA['matematica_propedutico']}
    TAREA: {tipo.upper()} el siguiente ejercicio de {tema}: {ejercicio}.
    {f"Resolución del alumno a corregir: {resolucion_alumno}" if tipo == 'corregir' else "Explica el paso a paso."}
    Usa LaTeX. JSON: 'explicacion', 'pasos', 'resultado', 'feedback_entrenador'.
    """

    try:
        resultado = llamar_groq(prompt)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    if not descontar_consulta(u):
        return jsonify({"error": "Error de base de datos"}), 500
    return jsonify(resultado)

# --- RUTAS: SIMULACRO DE EXAMEN (Sincronizada con error 405) ---

@app.route("/api/exam/generate", methods=["POST"])
def generar_examen():
    u = get_usuario_actual()
    if not u or u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({"error": "Sin créditos"}), 403

    data = request.json or {}
    cantidad_raw, _ = obtener_campo(data, "cantidad", tipo=int, default=5)
    cantidad = min(cantidad_raw, 20)
    contenido = data.get("contenido") or data.get("texto", "")
    tipos = data.get("tipos", ["Opción Múltiple"])

    if not isinstance(tipos, list) or not tipos:
        return jsonify({"error": "Lista de tipos inválida"}), 400

    cant_base = cantidad // len(tipos)
    resto = cantidad % len(tipos)
    distribucion = {t: cant_base + (1 if i < resto else 0) for i, t in enumerate(tipos)}

    prompt = f"""
    {PERFILES_MATERIA['higiene_upe']}
    Genera {cantidad} preguntas de: {contenido}.
    Distribución: {distribucion}.
    REGLA: En Choice, 'respuesta_correcta' es el TEXTO de la opción.
    JSON: 'preguntas' [id, tipo, pregunta, opciones, respuesta_correcta, justificacion_tecnica].
    """

    try:
        resp_json = llamar_groq(prompt)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    for p in resp_json.get("preguntas", []):
        if p.get("tipo") == "Opción Múltiple" and isinstance(p.get("opciones"), list):
            random.shuffle(p["opciones"])

    if not descontar_consulta(u):
        return jsonify({"error": "Error de base de datos"}), 500
    return jsonify(resp_json)

# --- RUTAS: RED Y ESCRITO (Sincronizadas) ---

@app.route("/api/concept/map", methods=["POST"])
def generar_red():
    u = get_usuario_actual()
    if not u or u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({"error": "No autorizado o sin créditos"}), 403

    data = request.json or {}
    texto, err = obtener_campo(data, "texto", requerido=True)
    if err: return jsonify({"error": err}), 400

    prompt = f"Genera una red conceptual: {texto}. JSON: 'nodos' (id, label), 'enlaces' (source, target, label)."

    try:
        resultado = llamar_groq(prompt)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    descontar_consulta(u)
    return jsonify(resultado)

@app.route("/api/text/correct", methods=["POST"])
def corregir_escrito():
    u = get_usuario_actual()
    if not u or u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({"error": "No autorizado o sin créditos"}), 403

    data = request.json or {}
    texto, err = obtener_campo(data, "texto", requerido=True)
    if err: return jsonify({"error": err}), 400

    prompt = f"{PERFILES_MATERIA['higiene_upe']} Evalúa este informe: {texto}. JSON: 'texto_corregido', 'observaciones_legales', 'nota'."

    try:
        resultado = llamar_groq(prompt)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    descontar_consulta(u)
    return jsonify(resultado)

# --- RUTAS EXISTENTES ---

@app.route("/api/usuario")
def info_usuario():
    u = get_usuario_actual()
    if not u: return jsonify({"logueado": False})
    return jsonify({"logueado": True, "email": u.email, "restantes": consultas_permitidas(u) - u.consultas_usadas})

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