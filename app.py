import os
import logging
import datetime
import json
from groq import Groq
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message

# --- CONFIGURACIÓN E INFRAESTRUCTURA ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
if not allowed_origins_raw:
    allowed_origins = ["http://localhost:5000", "http://127.0.0.1:5000"]
else:
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]
CORS(app, origins=allowed_origins)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise ValueError("Falta la variable de entorno SECRET_KEY")
app.secret_key = secret_key

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///local.db").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)

app.config.update(
    MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
    MAIL_USE_TLS=True,
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
    "preparar_oratoria", "generar_examen", "generar_rap", "generar_red"
}
MAX_TEXTO, MAX_MATERIAL, PERFIL_MAX = 15_000, 50_000, 3_000
CONSULTAS_BASE, CONSULTAS_POR_AD, MAX_BLOQUES_PUBLICIDAD = 5, 5, 2

PERFILES_MATERIA = {
    "higiene": "ROL: Inspector Técnico de Higiene y Seguridad. REGLA: Exige rigor legal (Ley 19587/72 y decretos).",
    "matematica": "ROL: Tutor de Matemática UPE. Explica pasos y teclas de calculadora científica. Usa andamiaje.",
    "politica": "ROL: Mentor de Oratoria y Política. Enfócate en conceptos de Estado, Poder y argumentación.",
    "alfabetizacion": """ROL: Especialista en Alfabetización Académica y Lingüística Universitaria.
    REGLAS: Evalúa Cohesión, Coherencia, Enunciación y Polifonía. Penaliza el plagio.""",
    "abogacia": """ROL: Profesor de la UNLZ (Facultad de Derecho). Rigor jurídico máximo (CN, CCyCN).""",
}

# --- MODELO ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    consultas_usadas = db.Column(db.Integer, default=0, nullable=False)
    ultima_consulta = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    bloques_publicidad_vistos = db.Column(db.Integer, default=0, nullable=False)
    material = db.Column(db.Text, default="")
    perfil_aprendizaje = db.Column(db.Text, default="{}")

with app.app_context():
    db.create_all()

# --- HELPERS ---
def get_usuario_actual():
    uid = session.get("usuario_id")
    return db.session.get(Usuario, uid) if uid else None

def resetear_si_nuevo_dia(u):
    ahora = datetime.datetime.now(datetime.timezone.utc)
    ultima = u.ultima_consulta
    if ultima:
        if ultima.tzinfo is None:
            ultima = ultima.replace(tzinfo=datetime.timezone.utc)
        if (ahora - ultima).total_seconds() > 86_400:
            u.consultas_usadas = 0
            u.bloques_publicidad_vistos = 0
            db.session.commit()

def consultas_permitidas(u):
    return CONSULTAS_BASE + u.bloques_publicidad_vistos * CONSULTAS_POR_AD

# --- IA LOGIC ---
def ejecutar_tarea_ia(tarea, texto, material, usuario, materia="general", consigna=""):
    perfil_materia = PERFILES_MATERIA.get(materia, "ROL: Mentor Académico Universitario.")

    persona_academica = """
    REGLAS DE ENTRENADOR:
    1. Nunca resuelvas la tarea directamente.
    2. Si es una pregunta conceptual, explica con profundidad y ejemplos.
    3. Si es una consigna, identifica conceptos necesarios y guía los pasos lógicos.
    4. Usa siempre la estructura de evaluación de 6 puntos:
       - Nota (0-10)
       - Análisis desempeño
       - Fortalezas
       - Aspectos a mejorar
       - Sugerencias
       - Reintento sugerido.
    """

    prompt_sistema = f"{perfil_materia}\n{persona_academica}"
    response_format = {"type": "text"}

    if tarea == "generar_examen":
        prompt_sistema += "\nTAREA: Generar examen único en JSON."
        content = f"MATERIAL: {material}\nGenerar examen dinámico."
        response_format = {"type": "json_object"}

    elif tarea == "evaluar":
        prompt_sistema += """
        TAREA: Evaluar con rigor del 70%.
        Responde ESTRICTAMENTE con este JSON que incluye tu estructura de 6 puntos:
        {
          "grade": nota, "status": "...", "performanceAnalysis": "...",
          "strengths": [], "weaknesses": [], "improvementSuggestions": [],
          "suggestedRetry": "...", "improvedVersion": "...", "isPromoted": bool,
          "sections": {
            "mainIdeas": {"score": 0-10, "feedback": "..."},
            "cohesion_coherence": {"score": 0-10, "feedback": "..."},
            "academic_rigor": {"score": 0-10, "feedback": "..."}
          }
        }"""
        content = f"CONSIGNA: {consigna}\nMATERIAL: {material}\nRESPUESTA ALUMNO: {texto}"
        response_format = {"type": "json_object"}

    elif tarea == "generar_rap":
        prompt_sistema += """
        TAREA: Crear un 'Rap Técnico' para memorización.
        REGLAS: Mantén el orden lógico, incluye TODAS las fechas y términos técnicos.
        Usa lenguaje literal (nada de metáforas poéticas).
        Responde en JSON con campos: 'title', 'verses' (lista) y 'evaluation' (rúbrica de 100 pts)."""
        content = f"TEXTO BASE: {material if material else texto}"
        response_format = {"type": "json_object"}

    elif tarea == "generar_red":
        prompt_sistema += """
        TAREA: Construir una Red Conceptual.
        Responde en JSON:
        { "title": "...", "nodes": [{"id": "...", "label": "...", "type": "core/main/secondary"}],
          "edges": [{"from": "...", "to": "...", "label": "..."}], "summary": "..." }"""
        content = f"TEXTO: {material if material else texto}"
        response_format = {"type": "json_object"}

    elif tarea == "explicar":
        prompt_sistema += "\nSi es una consigna, NO la resuelvas. Explica conceptos y da ejemplos similares."
        content = f"CONTEXTO: {material}\nSOLICITUD: {texto}"

    else:
        content = f"CONTEXTO: {material}\nACCIÓN: {tarea}\nENTRADA: {texto}"

    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": content}],
            temperature=0.7,
            response_format=response_format,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error("Error IA: %s", repr(e))
        return None

# --- RUTAS ---
@app.route("/")
def index():
    u = get_usuario_actual()
    return render_template("index.html", usuario=u)

@app.route("/login")
def login():
    return google.authorize_redirect(url_for("callback", _external=True))

@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    userinfo = token.get("userinfo") or google.userinfo()
    u = Usuario.query.filter_by(email=userinfo["email"]).first()
    if not u:
        u = Usuario(email=userinfo["email"])
        db.session.add(u)
    db.session.commit()
    session["usuario_id"] = u.id
    # FIX: session.permanent restaurado
    session.permanent = True
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/api/usuario")
def info_usuario():
    u = get_usuario_actual()
    if not u:
        return jsonify({"logueado": False})
    resetear_si_nuevo_dia(u)
    return jsonify({
        "logueado": True,
        "email": u.email,
        "restantes": max(0, consultas_permitidas(u) - u.consultas_usadas)
    })

# FIX: ruta restaurada a /<tarea> para compatibilidad con el frontend
@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    if tarea not in TAREAS_VALIDAS:
        return jsonify({"error": "Tarea inválida"}), 400
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json(silent=True) or {}

    # Manejo de material base
    nuevo_material = data.get("material")
    if nuevo_material:
        if len(nuevo_material) > MAX_MATERIAL:
            return jsonify({"error": "Material muy largo"}), 400
        u.material = nuevo_material
        db.session.commit()
        if tarea == "cargar_material":
            return jsonify({"res": "Material guardado."})

    resetear_si_nuevo_dia(u)
    permitidas = consultas_permitidas(u)
    if u.consultas_usadas >= permitidas:
        return jsonify({"error": "Consultas agotadas."}), 403

    texto = data.get("writing", data.get("texto", "")).strip()
    materia = data.get("materia", "general")
    consigna = data.get("prompt", "")

    if not texto and tarea not in ["cargar_material", "generar_examen", "generar_rap", "generar_red"]:
        return jsonify({"error": "Falta contenido."}), 400
    if len(texto) > MAX_TEXTO:
        return jsonify({"error": "Texto muy largo"}), 400

    # FIX: la IA se llama ANTES de descontar la consulta
    res = ejecutar_tarea_ia(tarea, texto, u.material, u, materia, consigna)
    if res is None:
        return jsonify({"error": "Error de conexión con la IA. No se descontó tu consulta."}), 503

    # FIX: except especificado correctamente
    try:
        resultado = json.loads(res) if tarea in ["evaluar", "generar_examen", "generar_rap", "generar_red"] else res
    except (json.JSONDecodeError, TypeError):
        resultado = res

    # Solo se descuenta si la IA respondió correctamente
    u.consultas_usadas += 1
    u.ultima_consulta = datetime.datetime.now(datetime.timezone.utc)
    db.session.commit()

    return jsonify({
        "resultado": resultado,
        "restantes": permitidas - u.consultas_usadas
    })

# --- RUTA: NOTIFICACIÓN DE EXAMEN ---
@app.route("/configurar_examen", methods=["POST"])
def configurar_examen():
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401
    data = request.get_json()
    try:
        msg = Message(f"Recordatorio de Examen: {data.get('materia')}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[u.email])
        msg.body = f"Examen de {data.get('materia')}\nFecha: {data.get('fecha')}\n¡A estudiar!"
        mail.send(msg)
        return jsonify({"res": "Notificación enviada"})
    except Exception as e:
        logger.error("Error Mail: %s", e)
        return jsonify({"error": "Error al enviar correo"}), 500

# --- RUTA: TIENDA ---
@app.route("/tienda")
def tienda():
    mensaje = "Función en desarrollo. Estamos ajustando los packs."
    return jsonify({"status": "proximamente", "mensaje": mensaje, "opciones": ["Pack Parcialito", "Pack Final"]})

# --- RUTA: VER ANUNCIO ---
@app.route("/ver_anuncio", methods=["POST"])
def ver_anuncio():
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401
    # FIX: límite de MAX_BLOQUES_PUBLICIDAD restaurado
    if u.bloques_publicidad_vistos >= MAX_BLOQUES_PUBLICIDAD:
        return jsonify({"error": "Límite diario de anuncios alcanzado. Volvé mañana."}), 403
    # FIX: salto de línea eliminado
    u.bloques_publicidad_vistos += 1
    db.session.commit()
    return jsonify({"res": "Anuncio registrado", "restantes": consultas_permitidas(u) - u.consultas_usadas})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
