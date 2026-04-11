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
    "preparar_oratoria", "generar_examen", "generar_rap", "generar_red",
    # NUEVAS TAREAS portadas desde AI Studio
    "corregir_escrito", "corregir_resumen", "explicar_concepto"
}
MAX_TEXTO, MAX_MATERIAL, PERFIL_MAX = 15_000, 50_000, 3_000
CONSULTAS_BASE, CONSULTAS_POR_AD, MAX_BLOQUES_PUBLICIDAD = 5, 5, 2

# Persona académica base portada desde AI Studio
ACADEMIC_COACH_PERSONA = """Eres un entrenador académico universitario especializado en comprensión de textos, desarrollo conceptual y mejora de respuestas escritas.
Tu objetivo no es hacer las tareas por el estudiante, sino entrenar su pensamiento académico.
Siempre debes comportarte como un docente universitario que evalúa y orienta el aprendizaje.

REGLAS IMPORTANTES:
1. Nunca escribas la respuesta completa al ejercicio por el estudiante.
2. No resuelvas consignas directamente.
3. Tu tarea es evaluar, orientar y explicar.
4. Puedes aclarar conceptos, dar ejemplos y sugerir mejoras.
5. El estudiante debe construir su propia respuesta.

Cuando evalúes una respuesta debes usar SIEMPRE la siguiente estructura en tus campos de retroalimentación:
1. Calificación estimada: Indica una calificación aproximada sobre 10.
2. Análisis del desempeño: Explica qué tan bien comprendió el estudiante el contenido.
3. Fortalezas: Indica qué aspectos de la respuesta están bien logrados.
4. Aspectos a mejorar: Señala conceptos faltantes, errores o problemas en la explicación.
5. Sugerencias de mejora: Explica cómo podría mejorar su respuesta.
6. Reintento sugerido: Invita al estudiante a mejorar su respuesta y volver a intentarlo."""

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

    try:
        cognitivo = json.loads(usuario.perfil_aprendizaje)
    except (json.JSONDecodeError, TypeError):
        cognitivo = {}

    response_format = {"type": "text"}
    prompt_sistema = f"{ACADEMIC_COACH_PERSONA}\n{perfil_materia}"

    # --- TAREA: CORREGIR ESCRITO (portada desde correctWriting de AI Studio) ---
    if tarea == "corregir_escrito":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}
{perfil_materia}

TAREA: Corregir el escrito del estudiante con criterios universitarios.
Evalúa con rigor académico siguiendo la estructura de 6 puntos.
Responde ESTRICTAMENTE con este JSON:
{{
  "grade": nota_0_a_10,
  "status": "Excelente/Satisfactorio/Insuficiente",
  "performanceAnalysis": "Análisis del desempeño",
  "strengths": ["fortaleza1", "fortaleza2"],
  "weaknesses": ["debilidad1", "debilidad2"],
  "improvementSuggestions": ["sugerencia1", "sugerencia2"],
  "suggestedRetry": "Invitación a mejorar",
  "omissions": ["concepto omitido1", "concepto omitido2"],
  "improvedVersion": "Ejemplo de cómo mejorar sin resolver completamente",
  "sections": {{
    "structure": {{"score": 0-10, "feedback": "..."}},
    "content": {{"score": 0-10, "feedback": "..."}},
    "vocabulary": {{"score": 0-10, "feedback": "..."}},
    "originality": {{"score": 0-10, "feedback": "..."}}
  }}
}}"""
        content = f"CONSIGNA DEL PROFESOR: {consigna}\nMATERIAL DE REFERENCIA: {material}\nESCRITO DEL ESTUDIANTE: {texto}"
        response_format = {"type": "json_object"}

    # --- TAREA: CORREGIR RESUMEN (portada desde evaluateSummary de AI Studio) ---
    elif tarea == "corregir_resumen":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}
{perfil_materia}

TAREA: Evaluar el resumen del estudiante comparándolo con el texto fuente.
Responde ESTRICTAMENTE con este JSON:
{{
  "grade": nota_0_a_10,
  "status": "Excelente/Satisfactorio/Insuficiente",
  "performanceAnalysis": "Análisis del desempeño",
  "strengths": ["fortaleza1", "fortaleza2"],
  "weaknesses": ["aspecto a mejorar1", "aspecto a mejorar2"],
  "improvementSuggestions": ["sugerencia1", "sugerencia2"],
  "suggestedRetry": "Invitación a mejorar",
  "omissions": ["idea clave omitida1", "idea clave omitida2"],
  "improvedVersion": "Versión superadora de ejemplo (sin resolver todo)"
}}"""
        content = f"TEXTO FUENTE ORIGINAL: {material}\nRESUMEN DEL ESTUDIANTE: {texto}"
        response_format = {"type": "json_object"}

    # --- TAREA: EXPLICAR CONCEPTO (portada desde explainConcept de AI Studio) ---
    elif tarea == "explicar_concepto":
        prompt_sistema = f"""{ACADEMIC_COACH_PERSONA}
{perfil_materia}

INSTRUCCIONES ESPECÍFICAS:
1. Si la solicitud es una pregunta conceptual, explícala con profundidad académica y ejemplos.
2. SI LA SOLICITUD ES UNA CONSIGNA DE EJERCICIO O TAREA:
   - NO LA RESUELVAS.
   - Identifica los conceptos teóricos necesarios para resolverla.
   - Explica esos conceptos de forma clara.
   - Proporciona ejemplos similares pero diferentes al ejercicio planteado.
   - Guía al estudiante sobre qué pasos lógicos debe seguir para llegar a la solución por su cuenta.
3. Mantén siempre el tono de un mentor universitario.

Responde ESTRICTAMENTE con este JSON:
{{
  "explanation": "Explicación didáctica completa",
  "examples": ["ejemplo1", "ejemplo2"],
  "keyTakeaways": ["punto clave1", "punto clave2"],
  "relatedConcepts": ["concepto relacionado1", "concepto relacionado2"]
}}"""
        content = f"CONTEXTO DE ESTUDIO: {material}\nSOLICITUD DEL ESTUDIANTE: {texto}"
        response_format = {"type": "json_object"}

    # --- TAREA: GENERAR EXAMEN ---
    elif tarea == "generar_examen":
        prompt_sistema += "\nTAREA: Generar examen único basado EXCLUSIVAMENTE en el material."
        content = f"MATERIAL: {material}\nCONFIGURACIÓN: {consigna}\nGenera el examen."
        response_format = {"type": "json_object"}

    # --- TAREA: EVALUAR ---
    elif tarea == "evaluar":
        prompt_sistema += f"""
        TAREA: Evaluar la respuesta del alumno contra la CONSIGNA y el MATERIAL base.
        Responde ESTRICTAMENTE con este JSON:
        {{
          "grade": nota_0_a_10,
          "status": "Excelente/Satisfactorio/Insuficiente",
          "performanceAnalysis": "Análisis pedagógico",
          "sections": {{
            "mainIdeas": {{"score": 0-10, "feedback": "..."}},
            "cohesion_coherence": {{"score": 0-10, "feedback": "..."}},
            "academic_rigor": {{"score": 0-10, "feedback": "..."}}
          }},
          "strengths": ["..."], "weaknesses": ["..."], "improvementSuggestions": ["..."],
          "omissions": ["..."], "improvedVersion": "...", "suggestedRetry": "...",
          "isPromoted": true/false
        }}
        HISTORIAL COGNITIVO: {json.dumps(cognitivo)}"""
        content = f"CONSIGNA: {consigna}\nMATERIAL: {material}\nRESPUESTA ALUMNO: {texto}"
        response_format = {"type": "json_object"}

    # --- TAREA: GENERAR RAP ---
    elif tarea == "generar_rap":
        prompt_sistema += """
        TAREA: Crear un 'Rap Técnico' para memorización.
        REGLAS: Mantén el orden lógico, incluye TODAS las fechas y términos técnicos.
        Usa lenguaje literal (nada de metáforas poéticas).
        Responde en JSON:
        {"title": "...", "verses": ["verso1", "verso2"],
         "evaluation": {"totalScore": 0-100, "status": "...", "professorFeedback": "...",
           "rubric": {"fidelity": 0-40, "order": 0-20, "terminology": 0-20, "data": 0-10, "clarity": 0-10}}}"""
        content = f"TEXTO BASE: {material if material else texto}"
        response_format = {"type": "json_object"}

    # --- TAREA: GENERAR RED CONCEPTUAL ---
    elif tarea == "generar_red":
        prompt_sistema += """
        TAREA: Construir una Red Conceptual detallada.
        Responde en JSON:
        {"title": "...", "summary": "...",
         "nodes": [{"id": "...", "label": "...", "type": "core/main/secondary"}],
         "edges": [{"from": "...", "to": "...", "label": "..."}]}"""
        content = f"TEXTO: {material if material else texto}"
        response_format = {"type": "json_object"}

    # --- TAREA: EXPLICAR ---
    elif tarea == "explicar":
        prompt_sistema += "\nSi es una consigna, NO la resuelvas. Explica conceptos y da ejemplos similares."
        content = f"CONTEXTO: {material}\nSOLICITUD: {texto}"

    # --- RESTO DE TAREAS ---
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

        # Actualización del mapa cognitivo solo en evaluaciones
        if tarea in ["evaluar", "corregir_escrito", "corregir_resumen"]:
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

    tareas_sin_texto = ["cargar_material", "generar_examen", "generar_rap", "generar_red"]
    if not texto and tarea not in tareas_sin_texto:
        return jsonify({"error": "Falta contenido."}), 400
    if len(texto) > MAX_TEXTO:
        return jsonify({"error": "Texto muy largo"}), 400

    # IA se llama ANTES de descontar la consulta
    res = ejecutar_tarea_ia(tarea, texto, u.material, u, materia, consigna)
    if res is None:
        return jsonify({"error": "Error de conexión con la IA. No se descontó tu consulta."}), 503

    # Tareas que devuelven JSON estructurado
    tareas_json = ["evaluar", "generar_examen", "generar_rap", "generar_red",
                   "corregir_escrito", "corregir_resumen", "explicar_concepto"]
    try:
        resultado = json.loads(res) if tarea in tareas_json else res
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
    if u.bloques_publicidad_vistos >= MAX_BLOQUES_PUBLICIDAD:
        return jsonify({"error": "Límite diario de anuncios alcanzado. Volvé mañana."}), 403
    u.bloques_publicidad_vistos += 1
    db.session.commit()
    return jsonify({"res": "Anuncio registrado", "restantes": consultas_permitidas(u) - u.consultas_usadas})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
