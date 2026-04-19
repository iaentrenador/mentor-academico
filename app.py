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

# Agregamos supports_credentials=True para que las cookies de sesión funcionen con CORS
CORS(app, origins=allowed_origins, supports_credentials=True)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    secret_key = "dev_secret_key_provisional"
app.secret_key = secret_key

# --- CONFIGURACIÓN DE BASE DE DATOS (ADAPTADA PARA SUPABASE) ---
basedir = os.path.abspath(os.path.dirname(__file__))

# Priorizamos SUPABASE_DATABASE_URL para evitar conflictos con Render
db_uri_raw = os.environ.get("SUPABASE_DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("NEONDB_OWNER")

if not db_uri_raw:
    db_uri = 'sqlite:///' + os.path.join(basedir, 'local.db')
else:
    db_uri = db_uri_raw.strip()
    # Estandarizamos el protocolo para SQLAlchemy y psycopg2-binary
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    elif db_uri.startswith("postgresql+pg8000://"):
        db_uri = db_uri.replace("postgresql+pg8000://", "postgresql://", 1)
    
    # Eliminamos parámetros que puedan interferir con la configuración manual de SSL
    if "?" in db_uri:
        db_uri = db_uri.split("?")[0]

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "connect_args": {"sslmode": "require"} # Conexión segura obligatoria para Supabase
}
# Aseguramos que la sesión dure y sea válida
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

# --- CONFIGURACIÓN DE CORREO (Flask-Mail) ---
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

# --- INICIALIZACIÓN DE BD ---
try:
    with app.app_context():
        db.create_all()
        logger.info("Base de datos verificada/creada.")
except Exception as e:
    logger.error("Error al conectar/crear la base de datos: %s", repr(e))

# --- HELPERS ---
def get_usuario_actual():
    uid = session.get("usuario_id")
    if not uid: return None
    # Usamos session.get para evitar errores si la sesión es vieja
    return db.session.get(Usuario, uid)

def resetear_si_nuevo_dia(u):
    ahora = datetime.datetime.now(datetime.timezone.utc)
    ultima = u.ultima_consulta
    if ultima:
        if ultima.tzinfo is None:
            ultima = ultima.replace(tzinfo=datetime.timezone.utc)
        if (ahora - ultima).total_seconds() > 86_400:
            u.consultas_usadas = 0
            u.bloques_publicidad_vistos = 0
            u.ultima_consulta = ahora
            db.session.commit()

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
    resetear_si_nuevo_dia(u)
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
        return jsonify({
            "success": True, 
            "restantes": consultas_permitidas(u) - u.consultas_usadas,
            "url_ad": ADSTERRA_URL
        })
    return jsonify({"error": "Límite alcanzado"}), 400

# --- NAVEGACIÓN Y AUTH ---
@app.route("/")
def index(): return send_from_directory(app.static_folder, "index.html")

@app.route("/login")
def login(): 
    # Forzamos la URL de callback correcta que pusimos en Google Console
    redirect_uri = url_for("callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/callback")
def callback():
    try:
        token = google.authorize_access_token()
        # CORRECCIÓN: Obtenemos el usuario de forma más segura para evitar Error 500
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
        
        email = userinfo.get("email")
        u = Usuario.query.filter_by(email=email).first()
        
        if not u:
            u = Usuario(email=email)
            db.session.add(u)
            db.session.commit() # Guardamos inmediatamente en Supabase
            logger.info(f"Nuevo usuario creado: {email}")
        
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
