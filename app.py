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

# --- CONSTANTES Y PERFILES (ACTUALIZADOS) ---
TAREAS_VALIDAS = {
    "explicar", "resumir", "evaluar", "cargar_material",
    "preparar_oratoria", "generar_examen", "generar_rap", "generar_red",
    "corregir_escrito", "corregir_resumen", "explicar_concepto", "evaluar_simulacro",
    "generar_resumen"
}
MAX_TEXTO, MAX_MATERIAL, PERFIL_MAX = 15_000, 50_000, 3_000
CONSULTAS_BASE, CONSULTAS_POR_AD, MAX_BLOQUES_PUBLICIDAD = 5, 5, 2

ACADEMIC_COACH_PERSONA = """Eres un entrenador académico universitario especializado en comprensión de textos y desarrollo conceptual.
Tu objetivo no es hacer las tareas por el estudiante, sino entrenar su pensamiento académico.
Comportate como un docente universitario que evalúa y orienta el aprendizaje."""

PERFILES_MATERIA = {
    "higiene_upe": "ROL: Inspector Técnico de Higiene y Seguridad (UPE). REGLA: Exige rigor en Ley 19587 y Decretos 351/911.",
    "politica_upe": "ROL: Mentor de Política y Sociedad (UPE). REGLA: Usa conceptos de Estado, Poder y Ciudadanía.",
    "alfabetizacion_upe": "ROL: Especialista en Alfabetización Académica (UPE). REGLA: Evalúa cohesión y normas APA.",
    "abogacia_unlz": "ROL: Profesor de la Facultad de Derecho UNLZ. Rigor jurídico máximo (Código Civil y Comercial).",
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

# --- IA LOGIC (MODIFICADA PARA RED CONCEPTUAL) ---
def ejecutar_tarea_ia(tarea, texto, material, usuario, materia="general", consigna="", query=""):
    perfil_materia = PERFILES_MATERIA.get(materia, "ROL: Mentor Académico Universitario.")

    response_format = {"type": "text"}
    prompt_sistema = f"{ACADEMIC_COACH_PERSONA}\n{perfil_materia}"

    if tarea == "explicar_concepto":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}
Responde ESTRICTAMENTE con este JSON:
{{"explanation": "...", "examples": [], "keyTakeaways": [], "relatedConcepts": []}}"""
        content = f"MATERIAL DE ESTUDIO: {texto}\nDUDA ESPECÍFICA DEL ALUMNO: {query}\nCONTEXTO ADICIONAL: {material}"
        response_format = {"type": "json_object"}

    elif tarea == "generar_resumen":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}
Responde ESTRICTAMENTE con este JSON:
{{"title": "...", "executiveSummary": "...", "keyConcepts": [{{"concept": "...", "definition": "..."}}], "conclusions": "..."}}"""
        content = f"TITULO SUGERIDO: {query}\nCONTENIDO PARA RESUMIR: {texto}"
        response_format = {"type": "json_object"}

    elif tarea == "corregir_resumen":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}
Compara el texto original con el resumen del alumno y responde ESTRICTAMENTE con este JSON:
{{"grade": 0-10, "status": "Excelente/Satisfactorio/Insuficiente", "performanceAnalysis": "...", "strengths": [], "weaknesses": [], "omissions": [], "improvementSuggestions": [], "suggestedRetry": "...", "improvedVersion": "..."}}"""
        content = f"TEXTO FUENTE: {texto}\nRESUMEN DEL ALUMNO: {query}"
        response_format = {"type": "json_object"}

    elif tarea == "generar_examen":
        prompt_sistema = f"""{perfil_materia}\nResponde ESTRICTAMENTE con JSON: {{"title": "...", "questions": []}}"""
        content = f"MATERIAL: {material if material else texto}"
        response_format = {"type": "json_object"}

    elif tarea == "corregir_escrito":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}\nResponde ESTRICTAMENTE con JSON: {{"grade": 0-10, "performanceAnalysis": "...", "strengths": [], "weaknesses": [], "improvementSuggestions": []}}"""
        content = f"CONSIGNA: {consigna}\nMATERIAL: {material}\nESCRITO: {texto}"
        response_format = {"type": "json_object"}

    elif tarea == "generar_rap":
        prompt_sistema += '\nResponde en JSON: {"title": "...", "verses": [], "evaluation": {"totalScore": 0-100, "professorFeedback": "..."}}'
        content = f"TEXTO: {material if material else texto}"
        response_format = {"type": "json_object"}

    elif tarea == "generar_red":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}\n{perfil_materia}
Estructura el texto en una red jerárquica. Responde ÚNICAMENTE con este JSON:
{{
  "title": "Título de la red",
  "summary": "Análisis estructural de la red",
  "nodes": [
    {{"id": "1", "label": "Concepto Núcleo", "type": "core"}},
    {{"id": "2", "label": "Concepto Principal", "type": "main"}},
    {{"id": "3", "label": "Concepto Secundario", "type": "secondary"}}
  ],
  "edges": [
    {{"from": "1", "to": "2", "label": "verbo de enlace"}}
  ]
}}
REGLAS: Solo un nodo 'core'. Nodos 'main' derivan del core. 'secondary' son detalles de los main."""
        content = f"TEXTO A MAPEAR: {texto}"
        response_format = {"type": "json_object"}
    
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

# --- RUTAS DE NAVEGACIÓN ---
@app.route("/api/health")
def health():
    return jsonify({"status": "ok"}), 200

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
    if request.path.startswith("/api/"):
        return jsonify({"error": "Ruta no encontrada"}), 404
    return send_from_directory(app.static_folder, "index.html")

# --- RUTAS DE API ---
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

@app.route("/api/generar_resumen", methods=["POST"])
def api_generar_resumen():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401
    data = request.json
    res = ejecutar_tarea_ia("generar_resumen", data.get("content", ""), "", u, query=data.get("title", ""))
    if not res: return jsonify({"error": "Error IA"}), 500
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": json.loads(res), "restantes": consultas_permitidas(u) - u.consultas_usadas})

@app.route("/api/corregir_resumen", methods=["POST"])
def api_corregir_resumen():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401
    data = request.json
    res = ejecutar_tarea_ia("corregir_resumen", data.get("sourceText", ""), "", u, query=data.get("userSummary", ""))
    if not res: return jsonify({"error": "Error IA"}), 500
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": json.loads(res), "restantes": consultas_permitidas(u) - u.consultas_usadas})

@app.route("/api/generar_red", methods=["POST"])
def api_generar_red():
    u = get_usuario_actual()
    if not u: return jsonify({"error": "No autenticado"}), 401
    data = request.json
    res = ejecutar_tarea_ia("generar_red", data.get("texto", ""), "", u, materia=data.get("materia", "general"))
    if not res: return jsonify({"error": "Error IA"}), 500
    u.consultas_usadas += 1
    db.session.commit()
    return jsonify({"resultado": json.loads(res), "restantes": consultas_permitidas(u) - u.consultas_usadas})

@app.route("/api/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    if tarea not in TAREAS_VALIDAS:
        return jsonify({"error": "Tarea inválida"}), 400
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json(silent=True) or {}
    texto = data.get("writing", data.get("texto", "")).strip()
    materia = data.get("materia", "general")
    query_usuario = data.get("query", "")

    if u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({"error": "Consultas agotadas."}), 403

    res = ejecutar_tarea_ia(tarea, texto, u.material, u, materia, query=query_usuario)
    if res is None:
        return jsonify({"error": "Error de conexión con la IA."}), 503

    tareas_json = ["generar_examen", "generar_rap", "generar_red", "corregir_escrito", "explicar_concepto", "generar_resumen", "corregir_resumen"]
    try:
        resultado = json.loads(res) if tarea in tareas_json else res
    except:
        resultado = res

    u.consultas_usadas += 1
    u.ultima_consulta = datetime.datetime.now(datetime.timezone.utc)
    db.session.commit()
    return jsonify({"resultado": resultado, "restantes": consultas_permitidas(u) - u.consultas_usadas})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
