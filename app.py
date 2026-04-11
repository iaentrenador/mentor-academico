import os
import logging
import datetime
import json
from groq import Groq
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update                          # FIX: necesario para update atómico
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message

# --- CONFIGURACIÓN E INFRAESTRUCTURA ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# FIX: CORS siempre con lista explícita; "*" solo si no hay origins configurados y se advierte
allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
if not allowed_origins_raw:
    logger.warning("ALLOWED_ORIGINS no configurado — CORS restringido a localhost por defecto")
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

# OAuth
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
TAREAS_VALIDAS = {"explicar", "resumir", "evaluar", "cargar_material", "preparar_oratoria", "generar_examen"}
MAX_TEXTO, MAX_MATERIAL, PERFIL_MAX = 15_000, 50_000, 3_000
CONSULTAS_BASE, CONSULTAS_POR_AD, MAX_BLOQUES_PUBLICIDAD = 5, 5, 2

PERFILES_MATERIA = {
    "higiene": "ROL: Inspector Técnico de Higiene y Seguridad. REGLA: Exige rigor legal (Ley 19587/72 y decretos).",
    "matematica": "ROL: Tutor de Matemática UPE. Explica pasos y teclas de calculadora científica. Usa andamiaje.",
    "politica": "ROL: Mentor de Oratoria y Política. Enfócate en conceptos de Estado, Poder y argumentación.",
    "alfabetizacion": """ROL: Especialista en Alfabetización Académica y Lingüística Universitaria.
    REGLAS DE EVALUACIÓN:
    1. PROPIEDADES: Evalúa Cohesión (conectores, sinónimos), Coherencia e Intertextualidad.
    2. ENUNCIACIÓN: Analiza construcción de Enunciador y Enunciatario.
    3. POLIFONÍA: Distingue citas directas/indirectas y penaliza el plagio.
    4. COMUNIDADES DISCURSIVAS: Evalúa identificación de léxico especializado y objetivos compartidos según John Swales.
    5. SECUENCIAS: Identifica tipos de texto (Narrativo, Descriptivo, Expositivo, Argumentativo, Instructivo).""",
    "abogacia": """ROL: Profesor de la UNLZ (Facultad de Derecho).
    REGLAS: Rigor jurídico máximo, citas de artículos (CN, CCyCN), terminología técnica y Plan de Estudios UNLZ.""",
}

# --- MODELO ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    consultas_usadas = db.Column(db.Integer, default=0, nullable=False)
    ultima_consulta = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))  # FIX: utcnow deprecado
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
    ahora = datetime.datetime.now(datetime.timezone.utc)  # FIX: utcnow deprecado
    ultima = u.ultima_consulta
    # FIX: comparar timezone-aware vs naive de forma segura
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

    escala_notas = """
    SISTEMA DE CALIFICACIÓN (Rigor Universitario):
    - 0% a 69% correcto: Nota 1 a 3 (Insuficiente/Reprobado).
    - 70% correcto: Nota 4 (Aprobado - Derecho a Final).
    - 71% a 89% correcto: Nota 5 a 6 (Bueno).
    - 90% a 100% correcto: Nota 7 a 10 (Promoción Directa).
    """

    try:
        cognitivo = json.loads(usuario.perfil_aprendizaje)
    except (json.JSONDecodeError, TypeError):
        logger.warning("perfil_aprendizaje inválido para usuario %s — usando vacío", usuario.id)  # FIX: no silenciar
        cognitivo = {}

    prompt_sistema = f"""{perfil_materia}
Eres el 'Mentor IA'. Tu objetivo es el entrenamiento cognitivo y la excelencia académica.
{escala_notas}

REGLAS GENERALES:
1. ANTI-MEMORIA: Si detectas que el alumno responde de memoria sin procesar, baja la nota.
2. PENALIZACIÓN DE PLAGIO: Máximo 5.0 si hay copy-paste del material.
3. ANDAMIAJE: No des soluciones directas, guía el pensamiento."""

    if tarea == "generar_examen":
        prompt_sistema += """
        TAREA: Generar un examen único.
        Si la materia es 'alfabetizacion', genera un texto nuevo basado en una comunidad discursiva aleatoria o usa el material para pedir:
        - Identificación de Enunciador/Enunciatario.
        - Análisis de Secuencia Textual predominante.
        - Extracción de Idea Principal y Secundaria.
        - Contexto (Ámbito de circulación, fecha, autor).

        Responde ÚNICAMENTE en JSON:
        {
          "examen": [
            { "id": 1, "pregunta": "...", "tipo": "choice/desarrollo/justificacion", "opciones": [...], "respuesta_correcta": "..." }
          ]
        }"""
        content = f"MATERIAL BASE: {material}\nConfiguración adicional: {consigna}\nGenerar examen dinámico."
        response_format = {"type": "json_object"}

    elif tarea == "evaluar":
        prompt_sistema += """
        TAREA: Evaluar con rigor del 70% para aprobar.
        Responde ESTRICTAMENTE con este JSON:
        {
          "grade": nota_final_segun_escala,
          "status": "Promocionado/Aprobado/Insuficiente",
          "performanceAnalysis": "Análisis pedagógico profundo",
          "sections": {
            "mainIdeas": {"score": 0-10, "feedback": "..."},
            "cohesion_coherence": {"score": 0-10, "feedback": "..."},
            "academic_rigor": {"score": 0-10, "feedback": "..."}
          },
          "improvedVersion": "Cómo debería haber sido la respuesta",
          "isPromoted": true/false
        }"""
        content = f"CONSIGNA: {consigna}\nMATERIAL: {material}\nRESPUESTA ALUMNO: {texto}"
        response_format = {"type": "json_object"}
    else:
        content = f"CONTEXTO: {material}\nACCIÓN: {tarea}\nENTRADA: {texto}"
        response_format = {"type": "text"}

    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": content},
            ],
            temperature=0.8,
            response_format=response_format,
        )
        res = completion.choices[0].message.content

        if tarea == "evaluar":
            try:
                data_eval = json.loads(res)
                # FIX: actualizar perfil con debilidades reales extraídas de la evaluación
                debilidades = {}
                secciones = data_eval.get("sections", {})
                for key, val in secciones.items():
                    score = val.get("score", 10)
                    if score < 6:
                        debilidades[key] = val.get("feedback", "")
                cognitivo.update(debilidades)
                # Mantener solo los últimos 10 ítems
                cognitivo_reducido = dict(list(cognitivo.items())[-10:])
                usuario.perfil_aprendizaje = json.dumps(cognitivo_reducido)
                db.session.commit()
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning("No se pudo actualizar perfil cognitivo: %s", e)  # FIX: no silenciar

        return res

    except Exception as e:
        logger.error("Error Groq: %s", repr(e))
        return None

# --- RUTAS ---
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

@app.route("/api/usuario")
def info_usuario():
    u = get_usuario_actual()
    if not u:
        return jsonify({"logueado": False})
    resetear_si_nuevo_dia(u)
    return jsonify({
        "logueado": True,
        "email": u.email,
        "restantes": max(0, consultas_permitidas(u) - u.consultas_usadas),
    })

# FIX: ruta con prefijo /api/ para evitar colisiones con rutas estáticas o futuras
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

    # FIX: update atómico para evitar race condition entre requests simultáneos
    resultado_update = db.session.execute(
        update(Usuario)
        .where(Usuario.id == u.id)
        .where(Usuario.consultas_usadas < consultas_permitidas(u))
        .values(
            consultas_usadas=Usuario.consultas_usadas + 1,
            ultima_consulta=datetime.datetime.now(datetime.timezone.utc),
        )
    )
    db.session.commit()

    if resultado_update.rowcount == 0:
        return jsonify({"error": "Consultas agotadas."}), 403

    # Refrescar objeto en memoria tras el update atómico
    db.session.refresh(u)

    texto = data.get("writing", data.get("texto", "")).strip()
    materia = data.get("materia", "general")
    consigna = data.get("prompt", "")

    if not texto and tarea not in ["cargar_material", "generar_examen"]:
        # FIX: revertir el consumo si la validación falla
        db.session.execute(
            update(Usuario)
            .where(Usuario.id == u.id)
            .values(consultas_usadas=Usuario.consultas_usadas - 1)
        )
        db.session.commit()
        return jsonify({"error": "Falta contenido."}), 400

    res = ejecutar_tarea_ia(tarea, texto, u.material, u, materia, consigna)
    if res is None:
        # FIX: revertir el consumo si la IA falla
        db.session.execute(
            update(Usuario)
            .where(Usuario.id == u.id)
            .values(consultas_usadas=Usuario.consultas_usadas - 1)
        )
        db.session.commit()
        return jsonify({"error": "Error de conexión con la IA."}), 503

    try:
        resultado = json.loads(res) if tarea in ["evaluar", "generar_examen"] else res
    except json.JSONDecodeError as e:
        logger.warning("Respuesta IA no es JSON válido para tarea %s: %s", tarea, e)  # FIX: no silenciar
        resultado = {"raw": res}

    return jsonify({
        "resultado": resultado,
        "restantes": consultas_permitidas(u) - u.consultas_usadas,
    })

@app.route("/configurar_examen", methods=["POST"])
def configurar_examen():
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401
    data = request.get_json(silent=True) or {}
    try:
        msg = Message(
            f"Recordatorio de Examen: {data.get('materia')}",
            sender=app.config["MAIL_USERNAME"],
            recipients=[u.email],
        )
        msg.body = f"Examen de {data.get('materia')}\nFecha: {data.get('fecha')}\n¡A estudiar!"
        mail.send(msg)
        return jsonify({"res": "Notificación enviada"})
    except Exception as e:
        logger.error("Error Mail: %s", e)
        return jsonify({"error": "Error al enviar correo"}), 500

@app.route("/tienda")
def tienda():
    return jsonify({"status": "proximamente", "mensaje": "Packs Parcialito y Final en ajuste."})

@app.route("/ver_anuncio", methods=["POST"])
def ver_anuncio():
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    # FIX: update atómico con check de límite para evitar race condition
    resultado_update = db.session.execute(
        update(Usuario)
        .where(Usuario.id == u.id)
        .where(Usuario.bloques_publicidad_vistos < MAX_BLOQUES_PUBLICIDAD)
        .values(bloques_publicidad_vistos=Usuario.bloques_publicidad_vistos + 1)
    )
    db.session.commit()

    if resultado_update.rowcount == 0:
        return jsonify({"error": "Límite de anuncios alcanzado"}), 403  # FIX: bug de json\nify corregido

    db.session.refresh(u)
    return jsonify({
        "res": "Anuncio registrado",
        "restantes": consultas_permitidas(u) - u.consultas_usadas,
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
