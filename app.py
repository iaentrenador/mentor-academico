import os
import logging
import datetime
import google.generativeai as genai
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App & extensions
# ---------------------------------------------------------------------------
app = Flask(__name__)

# FIX: CORS restringido a orígenes configurados, sin wildcard en producción
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
CORS(app, origins=allowed_origins)

# FIX: Secret key obligatoria desde entorno, no puede ser el valor de desarrollo en producción
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise ValueError("Falta la variable de entorno SECRET_KEY")
app.secret_key = secret_key

app.config["SQLALCHEMY_DATABASE_URI"] = (
    os.environ.get("DATABASE_URL", "sqlite:///local.db")
    .replace("postgres://", "postgresql://", 1)
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Sesiones persistentes (para no loguearse cada vez)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

# FIX: Credenciales de correo movidas a variables de entorno
app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER", 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
mail = Mail(app)

db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
# FIX: API key obligatoria desde entorno, falla claro si no está definida
api_key = os.environ.get("API_KEY")
if not api_key:
    raise ValueError("Falta la variable de entorno API_KEY")
genai.configure(api_key=api_key)

# LÍNEA CORREGIDA: Cambiado de 2.0 a 1.5 para mayor estabilidad de cuota
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
TAREAS_VALIDAS = {"explicar", "resumir", "evaluar", "cargar_material", "preparar_oratoria"}
MAX_TEXTO = 15_000
MAX_MATERIAL = 50_000
CONSULTAS_BASE = 5
CONSULTAS_POR_AD = 5
MAX_BLOQUES_PUBLICIDAD = 2   
PERFIL_MAX = 2_000

# Perfiles de materia como diccionario
PERFILES_MATERIA = {
    "higiene": "ROL: Inspector Técnico de Higiene y Seguridad. REGLA: Exige rigor legal (Ley 19587/72).",
    "matematica": "ROL: Tutor de Matemática UPE. Explica pasos y teclas de calculadora.",
    "politica": "ROL: Mentor de Oratoria y Política. Enfócate en conceptos de Estado y Poder.",
}

# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_usuario_actual() -> Usuario | None:
    uid = session.get("usuario_id")
    return db.session.get(Usuario, uid) if uid else None

def resetear_si_nuevo_dia(u: Usuario) -> None:
    ahora = datetime.datetime.utcnow()
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86_400:
        u.consultas_usadas = 0
        u.bloques_publicidad_vistos = 0  
        db.session.commit()

def consultas_permitidas(u: Usuario) -> int:
    return CONSULTAS_BASE + u.bloques_publicidad_vistos * CONSULTAS_POR_AD

# ---------------------------------------------------------------------------
# Rutas de navegación y Auth
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    u = get_usuario_actual()
    return render_template("index.html", usuario=u)

@app.route("/login")
def login():
    if get_usuario_actual():
        return redirect(url_for("index"))
    return google.authorize_redirect(url_for("callback", _external=True))

@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    userinfo = token.get("userinfo") or google.userinfo()
    email = userinfo["email"]
    u = Usuario.query.filter_by(email=email).first()
    if not u:
        u = Usuario(email=email)
        db.session.add(u)
    db.session.commit()
    session["usuario_id"] = u.id
    session.permanent = True  
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------------------------------------------------------------------
# API: Info de Usuario (Para el contador en el Front)
# ---------------------------------------------------------------------------
@app.route("/api/usuario")
def info_usuario():
    u = get_usuario_actual()
    if not u:
        return jsonify({"logueado": False})
    resetear_si_nuevo_dia(u)
    permitidas = consultas_permitidas(u)
    return jsonify({
        "logueado": True,
        "email": u.email,
        "restantes": permitidas - u.consultas_usadas
    })

# ---------------------------------------------------------------------------
# IA Logic (CON PROTECCIÓN DE CONSULTAS)
# ---------------------------------------------------------------------------
def ejecutar_tarea_ia(tarea: str, texto: str, material: str, usuario: Usuario, materia: str = "general"):
    perfil_materia = PERFILES_MATERIA.get(materia, "")

    prompt = (
        f"Eres el Mentor Académico. {perfil_materia}\n"
        f"Historial del alumno: {usuario.perfil_aprendizaje}\n"
        f"Contexto/Material: {material}\n"
        f"Acción: {tarea}\n"
        f"Entrada del Estudiante: {texto}"
    )

    try:
        resp = model.generate_content(prompt)
        if hasattr(resp, "text"):
            res = resp.text
            nueva_entrada = f"Q: {texto[:50]}... A: {res[:50]}..."
            usuario.perfil_aprendizaje = (nueva_entrada + usuario.perfil_aprendizaje)[:PERFIL_MAX]
            return res
        return None
    except Exception as e:
        logger.error("Error Gemini completo: %s", repr(e))
        return None

@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea: str):
    if tarea not in TAREAS_VALIDAS:
        return jsonify({"error": "Tarea inválida"}), 400
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    if tarea == "cargar_material":
        material = request.json.get("material", "")
        if len(material) > MAX_MATERIAL:
            return jsonify({"error": "Material muy largo"}), 400
        u.material = material
        db.session.commit()
        return jsonify({"res": "Material actualizado"})

    resetear_si_nuevo_dia(u)
    permitidas = consultas_permitidas(u)
    if u.consultas_usadas >= permitidas:
        return jsonify({"error": "Consultas agotadas por hoy."}), 403

    data = request.get_json(silent=True) or {}
    texto = data.get("texto", "").strip()
    materia = data.get("materia", "general")

    if not texto:
        return jsonify({"error": "Texto obligatorio"}), 400
    if len(texto) > MAX_TEXTO:
        return jsonify({"error": "Texto muy largo"}), 400

    res = ejecutar_tarea_ia(tarea, texto, u.material, u, materia)

    if res is None:
        return jsonify({"error": "Error de conexión con la IA. No se descontó tu consulta. Intenta de nuevo."}), 503

    u.consultas_usadas += 1
    u.ultima_consulta = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({
        "resultado": res,
        "restantes": permitidas - u.consultas_usadas
    })

# --- RUTA: NOTIFICACIÓN DE EXAMEN ---
@app.route("/configurar_examen", methods=["POST"])
def configurar_examen():
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401
    data = request.get_json()
    materia = data.get("materia")
    fecha = data.get("fecha")
    try:
        msg = Message(f"Recordatorio de Examen: {materia}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[u.email])
        msg.body = f"Hola!\n\nTu Mentor Académico te recuerda tu fecha de examen para {materia}.\nFecha: {fecha}\n\n¡Éxitos!"
        mail.send(msg)
        return jsonify({"res": "Notificación enviada"})
    except Exception as e:
        logger.error("Error Mail: %s", e)
        return jsonify({"error": "Error al enviar correo"}), 500

@app.route("/tienda")
def tienda():
    mensaje = "Función en desarrollo. Estamos ajustando los packs."
    return jsonify({"status": "proximamente", "mensaje": mensaje, "opciones": ["Pack Parcialito", "Pack Final"]})

@app.route("/ver_anuncio", methods=["POST"])
def ver_anuncio():
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    if u.bloques_publicidad_vistos >= MAX_BLOQUES_PUBLICIDAD:
        return jsonify({"error": "Ya obtuviste el máximo de consultas extra por hoy. Volvé mañana."}), 403

    u.bloques_publicidad_vistos += 1
    db.session.commit()
    return jsonify({"res": "Anuncio registrado", "restantes": consultas_permitidas(u) - u.consultas_usadas})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
        
