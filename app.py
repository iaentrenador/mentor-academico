import os
import logging
import datetime
import json
from groq import Groq
from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from authlib.integrations.flask_client import OAuth
# --- CORRECCIÓN: Volvemos a Flask-Mail para evitar conflictos de dependencias en Render ---
from flask_mail import Mail, Message

# --- CONFIGURACIÓN E INFRAESTRUCTURA ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway asigna un puerto dinámico mediante la variable de entorno PORT
port = int(os.environ.get("PORT", 5000))

dist_path = os.path.join(os.path.dirname(__file__), 'dist')
if not os.path.exists(dist_path):
    os.makedirs(dist_path, exist_ok=True)
    with open(os.path.join(dist_path, 'index.html'), 'w') as f:
        f.write("<html><body>Cargando Mentor IA... Por favor, recarga en un momento.</body></html>")

app = Flask(__name__, static_folder=dist_path, static_url_path='/')

allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
if not allowed_origins_raw:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173", "https://mentor-academico-0cn1.onrender.com"]
else:
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

CORS(app, origins=allowed_origins, supports_credentials=True)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    secret_key = "dev_secret_key_provisional"
app.secret_key = secret_key

# --- CONFIGURACIÓN DE BASE DE DATOS (AJUSTADA PARA RAILWAY) ---
db_uri_raw = os.environ.get("DATABASE_URL")

if db_uri_raw:
    # Ajuste de protocolo: Railway usa postgres://, SQLAlchemy requiere postgresql://
    db_uri = db_uri_raw.replace("postgres://", "postgresql://", 1).split("?")[0]
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {"sslmode": "require"} # Indispensable para la seguridad de Railway
    }
    logger.info("SISTEMA: Configuración de PostgreSQL (Railway) detectada.")
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_uri = 'sqlite:///' + os.path.join(basedir, 'local.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    logger.warning("SISTEMA: DATABASE_URL no encontrada. Usando SQLite local.")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

# --- CONFIGURACIÓN DE CORREO ---
app.config.update(
    MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
)

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
TAREAS_VALIDAS = {
    "explicar", "resumir", "evaluar", "cargar_material",
    "preparar_oratoria", "generar_examen", "generar_rap", "generar_red",
    "corregir_escrito", "corregir_resumen", "explicar_concepto", "evaluar_simulacro",
    "generar_resumen", "math_explain", "math_correct"
}
CONSULTAS_BASE = 4 
ADSTERRA_URL = "https://www.profitablecpmratenetwork.com/n2r78m21y?key=53d8cbd50aefa22ac6dd367853c1809e"
LIMITE_USUARIOS = 50

ACADEMIC_COACH_PERSONA = """Eres un entrenador académico universitario especializado en comprensión de textos y desarrollo conceptual."""

PERFILES_MATERIA = {
    "higiene_upe": "ROL: Inspector Técnico de Higiene y Seguridad (UPE).",
    "politica_upe": "ROL: Mentor de Política y Sociedad (UPE).",
    "alfabetizacion_upe": "ROL: Especialista en Alfabetización Académica (UPE).",
    "abogacia_unlz": "ROL: Profesor de la Facultad de Derecho UNLZ.",
}

# --- MODELO ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    consultas_usadas = db.Column(db.Integer, default=0, nullable=False)
    ultima_consulta = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    bloques_publicidad_vistos = db.Column(db.Integer, default=0, nullable=False)
    creditos_comprados = db.Column(db.Integer, default=0, nullable=False)
    material = db.Column(db.Text, default="")
    perfil_aprendizaje = db.Column(db.Text, default="{}")

# --- INICIALIZACIÓN DE BD CON FALLBACK ---
try:
    with app.app_context():
        db.create_all()
        logger.info("Base de datos: Sincronización exitosa.")
except Exception as e:
    logger.error(f"Error crítico en DB: {e}")
    # Si Postgres falla, intentamos levantar con SQLite para evitar que el deploy muera
    with app.app_context():
        app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///emergency.db'
        db.create_all()
    logger.warning("SISTEMA: La aplicación arrancó con base de datos de emergencia.")

# --- HELPERS ---
def get_usuario_actual():
    uid = session.get("usuario_id")
    if not uid: return None
    return db.session.get(Usuario, uid)

def consultas_permitidas(u):
    total = CONSULTAS_BASE
    if u.bloques_publicidad_vistos >= 1: total += 3
    if u.bloques_publicidad_vistos >= 2: total += 2
    return total + u.creditos_comprados

# --- RUTAS DE API ---

@app.route("/api/usuario")
def info_usuario():
    u = get_usuario_actual()
    if not u: 
        return jsonify({"logueado": False, "restantes": 0, "total_hoy": 0})
    return jsonify({
        "logueado": True,
        "email": u.email,
        "restantes": max(0, consultas_permitidas(u) - u.consultas_usadas),
        "total_hoy": consultas_permitidas(u),
        "bloques_ad": u.bloques_publicidad_vistos,
        "url_ad": ADSTERRA_URL
    })

@app.route("/api/registrar_ad", methods=["POST"])
def registrar_ad():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401
    if u.bloques_publicidad_vistos < 2:
        u.bloques_publicidad_vistos += 1
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Límite alcanzado"}), 400

@app.route("/api/explicar_concepto", methods=["POST"])
def explicar_concepto():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401
    if u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({"error": "Créditos agotados"}), 403

    data = request.json
    texto = data.get("texto", "")
    pregunta = data.get("pregunta", "")
    modo_legal = data.get("modo_legal", False)
    materia = data.get("materia", "higiene_upe")

    perfil = PERFILES_MATERIA.get(materia, PERFILES_MATERIA["higiene_upe"])
    instrucciones_legales = "Utiliza terminología técnica y cita leyes si es pertinente." if modo_legal else "Usa un lenguaje claro y pedagógico."

    prompt = f"""
    {ACADEMIC_COACH_PERSONA}
    {perfil}
    
    CONSIGNA: El estudiante quiere comprender un concepto basado en el siguiente texto.
    TEXTO: {texto}
    DUDA DEL ESTUDIANTE: {pregunta}
    
    {instrucciones_legales}
    
    IMPORTANTE: Si el estudiante envió una consigna de examen, NO la resuelvas directamente. Explica la teoría detrás para que él pueda resolverla.
    
    RESPONDE ESTRICTAMENTE EN FORMATO JSON con la siguiente estructura:
    {{
      "explanation": "Texto de la explicación detallada",
      "examples": ["Ejemplo 1", "Ejemplo 2"],
      "keyTakeaways": ["Punto clave 1", "Punto clave 2"],
      "relatedConcepts": ["Concepto A", "Concepto B"]
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_ID,
            response_format={"type": "json_object"}
        )
        resultado = json.loads(chat_completion.choices[0].message.content)
        
        u.consultas_usadas += 1
        db.session.commit()
        
        return jsonify({
            "resultado": resultado,
            "restantes": consultas_permitidas(u) - u.consultas_usadas
        })
    except Exception as e:
        logger.error(f"Error en explainer: {str(e)}")
        return jsonify({"error": "Error al procesar la solicitud"}), 500

@app.route("/api/generar_resumen", methods=["POST"])
def generar_resumen():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401
    if u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({"error": "Créditos agotados"}), 403

    data = request.json
    texto = data.get("texto", "")
    materia = data.get("materia", "higiene_upe")

    perfil = PERFILES_MATERIA.get(materia, PERFILES_MATERIA["higiene_upe"])

    prompt = f"""
    {ACADEMIC_COACH_PERSONA}
    {perfil}
    
    CONSIGNA: Crea un resumen universitario profesional del siguiente texto técnico.
    TEXTO: {texto}
    
    RESPONDE ESTRICTAMENTE EN FORMATO JSON:
    {{
      "title": "Título sugerido del resumen",
      "executiveSummary": "Párrafo de síntesis principal",
      "keyConcepts": [
        {{ "concept": "Nombre del concepto", "definition": "Definición técnica" }}
      ],
      "conclusions": "Síntesis final de importancia para la materia"
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_ID,
            response_format={"type": "json_object"}
        )
        resultado = json.loads(chat_completion.choices[0].message.content)
        
        u.consultas_usadas += 1
        db.session.commit()
        
        return jsonify({
            "resultado": resultado,
            "restantes": consultas_permitidas(u) - u.consultas_usadas
        })
    except Exception as e:
        logger.error(f"Error en resumen: {str(e)}")
        return jsonify({"error": "Error al procesar el resumen"}), 500

# --- NAVEGACIÓN Y AUTH ---
@app.route("/")
def index(): return send_from_directory(app.static_folder, "index.html")

@app.route("/login")
def login(): 
    redirect_uri = url_for("callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/callback")
def callback():
    try:
        token = google.authorize_access_token()
        userinfo = token.get("userinfo") or google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
        email = userinfo.get("email")
        
        u = Usuario.query.filter_by(email=email).first()
        
        if not u:
            u = Usuario(email=email)
            db.session.add(u)
            db.session.commit()
            logger.info(f"Nuevo usuario creado en base de datos: {email}")
        
        session["usuario_id"] = u.id
        session.permanent = True
        return redirect("/")
    except Exception as e:
        logger.error(f"Error en callback: {str(e)}")
        return "Error en la autenticación", 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    # Importante: Railway requiere host 0.0.0.0 y el puerto dinámico de la variable PORT
    app.run(host="0.0.0.0", port=port)