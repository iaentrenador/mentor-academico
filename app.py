import os
import logging
import datetime
import google.generativeai as genai
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message  # Nueva dependencia para correos

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App & extensions
# ---------------------------------------------------------------------------
app = Flask(__name__)

CORS(app, origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","))

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    os.environ.get("DATABASE_URL", "sqlite:///local.db")
    .replace("postgres://", "postgresql://", 1)
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- CONFIGURACIÓN DE CORREO OFICIAL ---
app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER", 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'acmementor.noreply@gmail.com' # Correo Oficial
app.config['MAIL_PASSWORD'] = '5deseptiembre' # Contraseña integrada
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
genai.configure(api_key=os.environ.get("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
TAREAS_VALIDAS = {"explicar", "resumir", "evaluar", "cargar_material", "preparar_oratoria"}
MAX_TEXTO = 2_000       
MAX_MATERIAL = 10_000   
CONSULTAS_BASE = 5
CONSULTAS_POR_AD = 5
PERFIL_MAX = 1_000      

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
# Rutas de navegación y Auth
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
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
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------------------------------------------------------------------
# Helpers y Lógica de IA con Perfiles de Materia
# ---------------------------------------------------------------------------
def get_usuario_actual() -> Usuario | None:
    uid = session.get("usuario_id")
    return db.session.get(Usuario, uid) if uid else None

def resetear_si_nuevo_dia(u: Usuario) -> None:
    ahora = datetime.datetime.utcnow()
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86_400:
        u.consultas_usadas = 0

def consultas_permitidas(u: Usuario) -> int:
    return CONSULTAS_BASE + u.bloques_publicidad_vistos * CONSULTAS_POR_AD

def ejecutar_tarea_ia(tarea: str, texto: str, material: str, usuario: Usuario, materia: str = "general") -> str:
    # --- Lógica de Prompts por Materia (Perfiles V.A.L.F.) ---
    perfil_materia = ""
    if materia == "higiene":
        perfil_materia = (
            "ROL: Inspector Técnico de Higiene y Seguridad. REGLA: Si el alumno no cita Ley/Año (ej. 19587/72) "
            "o no utiliza conceptos de la Tríada Ecológica (Agente-Huésped-Ambiente), debes rechazar la respuesta "
            "amablemente indicando la falta de rigor legal."
        )
    elif materia == "matematica":
        perfil_materia = (
            "ROL: Tutor de Matemática UPE. REGLA: Explica paso a paso. Para ejercicios de cálculo, genera "
            "un MODELO SIMILAR (no el mismo) y detalla exactamente qué TECLAS de la calculadora científica "
            "debe tocar el alumno (ej: [EXP], [x10^x], [SHIFT]+[LOG])."
        )
    elif materia == "politica":
        perfil_materia = (
            "ROL: Mentor de Oratoria y Política. REGLA: Prepara guiones para exposiciones virtuales. "
            "Enfócate en conceptos de Estado, Poder y el programa total de la materia."
        )

    prompt = (
        f"Eres el Mentor Académico. {perfil_materia}\n"
        f"Historial del alumno: {usuario.perfil_aprendizaje}\n"
        f"Contexto/Material: {material}\n"
        f"Acción: {tarea}\n"
        f"Entrada del Estudiante: {texto}"
    )

    try:
        resp = model.generate_content(prompt)
        res = resp.text if hasattr(resp, "text") else "Error en respuesta."
        nueva_entrada = f"Q: {texto[:50]}... A: {res[:50]}..."
        usuario.perfil_aprendizaje = (nueva_entrada + usuario.perfil_aprendizaje)[:PERFIL_MAX]
        db.session.commit()
        return res
    except Exception as e:
        logger.error("Error Gemini: %s", e)
        db.session.rollback()
        return "Error de conexión con la IA."

# ---------------------------------------------------------------------------
# Rutas de Tareas y Nuevas Funciones
# ---------------------------------------------------------------------------
@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea: str):
    if tarea not in TAREAS_VALIDAS:
        return jsonify({"error": "Tarea inválida"}), 400
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401
    
    if tarea == "cargar_material":
        material = request.json.get("material", "")
        if len(material) > MAX_MATERIAL: return jsonify({"error": "Material muy largo"}), 400
        u.material = material
        db.session.commit()
        return jsonify({"res": "Material actualizado"})

    resetear_si_nuevo_dia(u)
    if u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({"error": "Consultas agotadas."}), 403

    data = request.get_json(silent=True) or {}
    texto = data.get("texto", "").strip()
    materia = data.get("materia", "general") # Captura la materia seleccionada en el front
    
    if not texto: return jsonify({"error": "Texto obligatorio"}), 400
    if len(texto) > MAX_TEXTO: return jsonify({"error": "Texto muy largo"}), 400

    res = ejecutar_tarea_ia(tarea, texto, u.material, u, materia)
    u.consultas_usadas += 1
    u.ultima_consulta = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify({"resultado": res})

# --- RUTA: NOTIFICACIÓN DE EXAMEN ---
@app.route("/configurar_examen", methods=["POST"])
def configurar_examen():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401
    
    data = request.get_json()
    materia = data.get("materia")
    fecha = data.get("fecha")
    email_destino = data.get("email", u.email)
    
    try:
        msg = Message(f"Recordatorio de Examen: {materia}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email_destino])
        msg.body = f"Hola!\n\nTu Mentor Académico te recuerda tu fecha de examen/entrega para {materia}.\nFecha: {fecha}\n\n¡Muchos éxitos!"
        mail.send(msg)
        return jsonify({"res": "Notificación enviada"})
    except Exception as e:
        logger.error("Error Mail: %s", e)
        return jsonify({"error": "Error al enviar correo"}), 500

# --- RUTA: TIENDA FANTASMA ---
@app.route("/tienda")
def tienda():
    mensaje = "Función en desarrollo. Estamos ajustando los packs de consultas según costos de API e Inflación en Argentina."
    return jsonify({
        "status": "proximamente",
        "mensaje": mensaje,
        "opciones": ["Pack Parcialito", "Pack Promoción", "Pack Final"]
    })

@app.route("/ver_anuncio", methods=["POST"])
def ver_anuncio():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401
    u.bloques_publicidad_vistos += 1
    db.session.commit()
    return jsonify({"res": "Anuncio registrado"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
        
