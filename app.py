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
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
CORS(app, origins=allowed_origins)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise ValueError("Falta la variable de entorno SECRET_KEY")
app.secret_key = secret_key

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///local.db").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

app.config.update(
    MAIL_SERVER=os.environ.get("MAIL_SERVER", 'smtp.gmail.com'),
    MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD")
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
TAREAS_VALIDAS = {"explicar", "resumir", "evaluar", "cargar_material", "preparar_oratoria"}
MAX_TEXTO, MAX_MATERIAL, PERFIL_MAX = 15_000, 50_000, 3_000
CONSULTAS_BASE, CONSULTAS_POR_AD, MAX_BLOQUES_PUBLICIDAD = 5, 5, 2

PERFILES_MATERIA = {
    "higiene": "ROL: Inspector Técnico de Higiene y Seguridad. REGLA: Exige rigor legal (Ley 19587/72 y decretos).",
    "matematica": "ROL: Tutor de Matemática UPE. Explica pasos y teclas de calculadora científica. Usa andamiaje.",
    "politica": "ROL: Mentor de Oratoria y Política. Enfócate en conceptos de Estado, Poder y argumentación.",
    "abogacia": """ROL: Profesor de la UNLZ (Facultad de Derecho). 
    REGLAS ESPECÍFICAS: 
    1. Aplica rigor jurídico máximo basado en la Legislación Argentina y la Constitución Nacional. 
    2. Exige fundamento legal citando artículos específicos (CN, CCyCN, CP, etc.). 
    3. Utiliza terminología técnica precisa. 
    4. Conoce el Plan de Estudios UNLZ (1ero a 6to año) para contextualizar el nivel de la respuesta.
    5. Si corriges un escrito, evalúa la solidez argumentativa y la jerarquía de las normas."""
}

# --- MODELO ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    consultas_usadas = db.Column(db.Integer, default=0, nullable=False)
    ultima_consulta = db.Column(db.DateTime, default=datetime.datetime.utcnow)
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
    ahora = datetime.datetime.utcnow()
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86_400:
        u.consultas_usadas = 0
        u.bloques_publicidad_vistos = 0
        db.session.commit()

def consultas_permitidas(u):
    return CONSULTAS_BASE + u.bloques_publicidad_vistos * CONSULTAS_POR_AD

# --- IA LOGIC ---
def ejecutar_tarea_ia(tarea, texto, material, usuario, materia="general", consigna=""):
    perfil_materia = PERFILES_MATERIA.get(materia, "ROL: Mentor Académico Universitario.")

    # FIX: except especificado correctamente
    try:
        cognitivo = json.loads(usuario.perfil_aprendizaje)
    except (json.JSONDecodeError, TypeError):
        cognitivo = {}

    prompt_sistema = f"""{perfil_materia}
Eres el 'Mentor IA'. Tu objetivo es el entrenamiento cognitivo y la excelencia académica.

REGLAS DE EVALUACIÓN:
1. PENALIZACIÓN DE PLAGIO: Detecta si el alumno copió frases literales del MATERIAL sin elaborar. Si hay copy-paste, la nota no debe superar 5.0. 
   - EXCEPCIÓN: En 'abogacia' o si la consigna pide 'transcribir', premia la literalidad de leyes o artículos.
2. ANDAMIAJE: No des respuestas directas en dudas, da pistas que guíen al alumno.
3. FORMATO JSON: Si la tarea es 'evaluar', responde ESTRICTAMENTE con este JSON:
{{
  "grade": nota_0_a_10,
  "status": "Excelente/Satisfactorio/Insuficiente",
  "performanceAnalysis": "Análisis pedagógico corto",
  "sections": {{
    "mainIdeas": {{"score": 0-10, "feedback": "..."}},
    "vocabulary": {{"score": 0-10, "feedback": "..."}},
    "originality": {{"score": 0-10, "feedback": "..."}}
  }},
  "strengths": ["punto1", "punto2"],
  "weaknesses": ["punto1", "punto2"],
  "omissions": ["Conceptos clave del material que el alumno olvidó"],
  "improvedVersion": "Cómo debería haber sido la respuesta ideal",
  "suggestedRetry": "Qué debe repasar para la próxima"
}}

HISTORIAL COGNITIVO DEL ALUMNO (Fortalezas/Debilidades previas): {json.dumps(cognitivo)}"""

    if tarea == "evaluar":
        content = f"CONSIGNA: {consigna}\nMATERIAL BASE: {material}\nRESPUESTA DEL ALUMNO: {texto}\nCompara la respuesta con el material y la consigna. Evalúa rigor y originalidad."
        response_format = {"type": "json_object"}
    else:
        content = f"CONTEXTO: {material}\nACCIÓN: {tarea}\nENTRADA: {texto}"
        response_format = {"type": "text"}

    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": content}],
            temperature=0.6,
            response_format=response_format
        )
        res = completion.choices[0].message.content

        # Actualización del mapa cognitivo
        if tarea == "evaluar":
            # FIX: except especificado correctamente
            try:
                data_eval = json.loads(res)
                for w in data_eval.get("weaknesses", []):
                    cognitivo[w[:20]] = "reforzar"
                for s in data_eval.get("strengths", []):
                    cognitivo[s[:20]] = "dominado"
                nuevo_perfil = dict(list(cognitivo.items())[-10:])
                usuario.perfil_aprendizaje = json.dumps(nuevo_perfil)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

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
        "restantes": max(0, permitidas - u.consultas_usadas)
    })

@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    if tarea not in TAREAS_VALIDAS:
        return jsonify({"error": "Tarea inválida"}), 400
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json(silent=True) or {}

    # Persistencia de material
    nuevo_material = data.get("material")
    if nuevo_material:
        if len(nuevo_material) > MAX_MATERIAL:
            return jsonify({"error": "Material muy largo"}), 400
        u.material = nuevo_material
        db.session.commit()
        if tarea == "cargar_material":
            return jsonify({"res": "Material guardado correctamente."})

    resetear_si_nuevo_dia(u)
    permitidas = consultas_permitidas(u)
    if u.consultas_usadas >= permitidas:
        return jsonify({"error": "Consultas agotadas por hoy."}), 403

    texto = data.get("writing", data.get("texto", "")).strip()
    materia = data.get("materia", "general")
    consigna = data.get("prompt", "")

    if not texto and tarea != "cargar_material":
        return jsonify({"error": "Falta el contenido para procesar."}), 400

    # FIX: Validación de longitud de texto restaurada
    if len(texto) > MAX_TEXTO:
        return jsonify({"error": "Texto muy largo"}), 400

    res = ejecutar_tarea_ia(tarea, texto, u.material, u, materia, consigna)

    if res is None:
        return jsonify({"error": "Error de conexión con la IA."}), 503

    if tarea == "evaluar":
        try:
            resultado = json.loads(res)
        except (json.JSONDecodeError, TypeError):
            resultado = {"grade": 0, "performanceAnalysis": "Error al parsear evaluación.", "raw": res}
    else:
        resultado = res

    u.consultas_usadas += 1
    u.ultima_consulta = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({
        "resultado": resultado,
        "restantes": permitidas - u.consultas_usadas
    })

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
    # FIX: except con logging del error
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
        # FIX: string sin salto de línea
        return jsonify({"error": "Máximo diario alcanzado"}), 403
    u.bloques_publicidad_vistos += 1
    db.session.commit()
    return jsonify({"res": "Anuncio registrado", "restantes": consultas_permitidas(u) - u.consultas_usadas})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
