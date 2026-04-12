import os
import logging
import datetime
import json
from groq import Groq
from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message

# --- CONFIGURACIÓN E INFRAESTRUCTURA ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aseguramos que la carpeta dist exista antes de inicializar Flask
dist_path = os.path.join(os.path.dirname(__file__), 'dist')
if not os.path.exists(dist_path):
    os.makedirs(dist_path, exist_ok=True)
    with open(os.path.join(dist_path, 'index.html'), 'w') as f:
        f.write("<html><body>Cargando Mentor IA... Por favor, recarga en un momento.</body></html>")

app = Flask(__name__, static_folder=dist_path, static_url_path='/')

allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
if not allowed_origins_raw:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
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
    "preparar_oratoria", "generar_examen", "generar_rap", "generar_red",
    "corregir_escrito", "corregir_resumen", "explicar_concepto", "evaluar_simulacro"
}
MAX_TEXTO, MAX_MATERIAL, PERFIL_MAX = 15_000, 50_000, 3_000
CONSULTAS_BASE, CONSULTAS_POR_AD, MAX_BLOQUES_PUBLICIDAD = 5, 5, 2

ACADEMIC_COACH_PERSONA = """Eres un entrenador académico universitario especializado en comprensión de textos, desarrollo conceptual y mejora de respuestas escritas.
Tu objetivo no es hacer las tareas por el estudiante, sino entrenar su pensamiento académico.
Siempre debes comportarte como un docente universitario que evalúa y orienta el aprendizaje.

REGLAS IMPORTANTES:
1. Nunca escribas la respuesta completa al ejercicio por el estudiante.
2. No resuelvas consignas directamente.
3. Tu tarea es evaluar, orientar y explicar.
4. Puedes aclarar conceptos, dar ejemplos y sugerir mejoras.
5. El estudiante debe construir su propia respuesta.

Cuando evalúes una respuesta debes usar SIEMPRE la siguiente estructura:
1. Calificación estimada (0-10)
2. Análisis del desempeño
3. Fortalezas
4. Aspectos a mejorar
5. Sugerencias de mejora
6. Reintento sugerido"""

PERFILES_MATERIA = {
    "higiene": "ROL: Inspector Técnico de Higiene y Seguridad. REGLA: Exige rigor legal (Ley 19587/72 y decretos).",
    "matematica": "ROL: Tutor de Matemática UPE. Explica pasos y teclas de calculadora científica. Usa andamiaje.",
    "politica": "ROL: Mentor de Oratoria y Política. Enfócate en conceptos de Estado, Poder y argumentación.",
    "alfabetizacion": "ROL: Especialista en Alfabetización Académica. Evalúa Cohesión, Coherencia, Enunciación y Polifonía.",
    "abogacia": "ROL: Profesor de la UNLZ (Facultad de Derecho). Rigor jurídico máximo (CN, CCyCN).",
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

    try:
        cognitivo = json.loads(usuario.perfil_aprendizaje)
    except (json.JSONDecodeError, TypeError):
        cognitivo = {}

    response_format = {"type": "text"}
    prompt_sistema = f"{ACADEMIC_COACH_PERSONA}\n{perfil_materia}"

    if tarea == "generar_examen":
        prompt_sistema = f"""{perfil_materia}
Eres un Profesor Universitario creando un examen de opción múltiple.
Utiliza el material proporcionado para crear preguntas desafiantes.
Responde ESTRICTAMENTE con este JSON:
{{
  "title": "Nombre del Examen",
  "questions": [
    {{
      "id": 1,
      "question": "Pregunta...",
      "answerOptions": ["opcion A", "opcion B", "opcion C", "opcion D"],
      "correctAnswerIndex": 0
    }}
  ]
}}"""
        content = f"MATERIAL: {material if material else 'Generar preguntas generales de ' + materia}"
        response_format = {"type": "json_object"}

    elif tarea == "evaluar_simulacro":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}
TAREA: Evaluar resultados del simulacro. Responde ESTRICTAMENTE con este JSON:
{{
  "grade": 0-10, "status": "Excelente/Satisfactorio/Insuficiente",
  "performanceAnalysis": "...", "strengths": [], "weaknesses": [],
  "improvementSuggestions": [], "suggestedRetry": "...",
  "sections": {{
    "teoria": {{"score": 0-10, "feedback": "..."}},
    "aplicacion": {{"score": 0-10, "feedback": "..."}}
  }}
}}"""
        content = f"MATERIAL: {material}\nRESULTADOS: {texto}"
        response_format = {"type": "json_object"}

    elif tarea == "corregir_escrito":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}
TAREA: Corregir el escrito. Responde ESTRICTAMENTE con este JSON:
{{
  "grade": 0-10, "status": "...", "performanceAnalysis": "...",
  "strengths": [], "weaknesses": [], "improvementSuggestions": [],
  "suggestedRetry": "...", "omissions": [], "improvedVersion": "...",
  "sections": {{
    "structure": {{"score": 0-10, "feedback": "..."}},
    "content": {{"score": 0-10, "feedback": "..."}},
    "vocabulary": {{"score": 0-10, "feedback": "..."}},
    "originality": {{"score": 0-10, "feedback": "..."}}
  }}
}}"""
        content = f"CONSIGNA: {consigna}\nMATERIAL: {material}\nESCRITO: {texto}"
        response_format = {"type": "json_object"}

    elif tarea == "corregir_resumen":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}
TAREA: Evaluar el resumen. Responde ESTRICTAMENTE con este JSON:
{{
  "grade": 0-10, "status": "...", "performanceAnalysis": "...",
  "strengths": [], "weaknesses": [], "improvementSuggestions": [],
  "suggestedRetry": "...", "omissions": [], "improvedVersion": "..."
}}"""
        content = f"FUENTE: {material}\nRESUMEN: {texto}"
        response_format = {"type": "json_object"}

    elif tarea == "explicar_concepto":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}
Responde ESTRICTAMENTE con este JSON:
{{"explanation": "...", "examples": [], "keyTakeaways": [], "relatedConcepts": []}}"""
        content = f"CONTEXTO: {material}\nSOLICITUD: {texto}"
        response_format = {"type": "json_object"}

    elif tarea == "evaluar":
        prompt_sistema += """
TAREA: Evaluar la respuesta. Responde ESTRICTAMENTE con este JSON:
{
  "grade": 0-10, "status": "...", "performanceAnalysis": "...",
  "sections": {
    "mainIdeas": {"score": 0-10, "feedback": "..."},
    "cohesion": {"score": 0-10, "feedback": "..."}
  },
  "strengths": [], "weaknesses": [], "improvementSuggestions": [],
  "omissions": [], "improvedVersion": "...", "suggestedRetry": "..."
}"""
        content = f"CONSIGNA: {consigna}\nMATERIAL: {material}\nRESPUESTA: {texto}"
        response_format = {"type": "json_object"}

    elif tarea == "generar_rap":
        prompt_sistema += '\nResponde en JSON: {"title": "...", "verses": [], "evaluation": {"totalScore": 0-100, "status": "...", "professorFeedback": "..."}}'
        content = f"TEXTO: {material if material else texto}"
        response_format = {"type": "json_object"}

    elif tarea == "generar_red":
        prompt_sistema += '\nResponde en JSON: {"title": "...", "summary": "...", "nodes": [], "edges": []}'
        content = f"TEXTO: {material if material else texto}"
        response_format = {"type": "json_object"}

    elif tarea == "explicar":
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
        res = completion.choices[0].message.content

        if tarea in ["evaluar", "corregir_escrito", "corregir_resumen", "evaluar_simulacro"]:
            try:
                data_eval = json.loads(res)
                for w in data_eval.get("weaknesses", []):
                    cognitivo[w[:20]] = "reforzar"
                for s in data_eval.get("strengths", []):
                    cognitivo[s[:20]] = "dominado"
                usuario.perfil_aprendizaje = json.dumps(dict(list(cognitivo.items())[-10:]))
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        return res
    except Exception as e:
        logger.error("Error IA: %s", repr(e))
        return None

# ===========================================================================
# RUTAS REACT (SPA) — Sirven el frontend compilado
# Estas rutas NO deben interferir con las rutas /api/
# ===========================================================================

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

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
    session.permanent = True
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.errorhandler(404)
def not_found(e):
    # Para rutas de React (SPA), siempre devolver index.html
    # EXCEPTO si la ruta empieza con /api/
    if request.path.startswith("/api/"):
        return jsonify({"error": "Ruta no encontrada"}), 404
    return send_from_directory(app.static_folder, "index.html")

# ===========================================================================
# RUTAS DE API — Todas bajo /api/ para no chocar con React
# ===========================================================================

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

@app.route("/api/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    if tarea not in TAREAS_VALIDAS:
        return jsonify({"error": "Tarea inválida"}), 400
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json(silent=True) or {}
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

    if len(texto) > MAX_TEXTO:
        return jsonify({"error": "Texto muy largo"}), 400

    res = ejecutar_tarea_ia(tarea, texto, u.material, u, materia, consigna)
    if res is None:
        return jsonify({"error": "Error de conexión con la IA. No se descontó tu consulta."}), 503

    tareas_json = ["evaluar", "generar_examen", "generar_rap", "generar_red",
                   "corregir_escrito", "corregir_resumen", "explicar_concepto", "evaluar_simulacro"]
    try:
        resultado = json.loads(res) if tarea in tareas_json else res
    except (json.JSONDecodeError, TypeError):
        resultado = res

    u.consultas_usadas += 1
    u.ultima_consulta = datetime.datetime.now(datetime.timezone.utc)
    db.session.commit()

    return jsonify({"resultado": resultado, "restantes": permitidas - u.consultas_usadas})

@app.route("/api/configurar_examen", methods=["POST"])
def configurar_examen():
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401
    data = request.get_json()
    try:
        msg = Message(
            f"Recordatorio de Examen: {data.get('materia')}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[u.email]
        )
        msg.body = f"Examen de {data.get('materia')}\nFecha: {data.get('fecha')}\n¡A estudiar!"
        mail.send(msg)
        return jsonify({"res": "Notificación enviada"})
    except Exception as e:
        logger.error("Error Mail: %s", e)
        return jsonify({"error": "Error al enviar correo"}), 500

@app.route("/api/tienda")
def tienda():
    return jsonify({
        "status": "proximamente",
        "mensaje": "Función en desarrollo. Estamos ajustando los packs.",
        "opciones": ["Pack Parcialito", "Pack Final"]
    })

@app.route("/api/ver_anuncio", methods=["POST"])
def ver_anuncio():
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401
    if u.bloques_publicidad_vistos >= MAX_BLOQUES_PUBLICIDAD:
        return jsonify({"error": "Límite diario alcanzado. Volvé mañana."}), 403
    u.bloques_publicidad_vistos += 1
    db.session.commit()
    return jsonify({"res": "Anuncio registrado", "restantes": consultas_permitidas(u) - u.consultas_usadas})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
