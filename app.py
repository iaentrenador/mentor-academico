import os
import logging
import datetime
import google.generativeai as genai
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App & extensions
# ---------------------------------------------------------------------------
app = Flask(__name__)

# CORS: restringir a tu dominio en producciÃ³n
CORS(app, origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","))

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    os.environ.get("DATABASE_URL", "sqlite:///local.db")
    .replace("postgres://", "postgresql://", 1)
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
TAREAS_VALIDAS = {"explicar", "resumir", "evaluar", "cargar_material"}
MAX_TEXTO = 2_000       # caracteres
MAX_MATERIAL = 10_000   # caracteres
CONSULTAS_BASE = 5
CONSULTAS_POR_AD = 5
PERFIL_MAX = 1_000      # caracteres guardados en historial


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
    """Devuelve el usuario autenticado o None."""
    uid = session.get("usuario_id")
    if uid is None:
        return None
    return db.session.get(Usuario, uid)


def resetear_si_nuevo_dia(u: Usuario) -> None:
    """Resetea sÃ³lo las consultas diarias; los anuncios acumulan entre dÃ­as."""
    ahora = datetime.datetime.utcnow()
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86_400:
        u.consultas_usadas = 0
        # NO se resetea bloques_publicidad_vistos: el usuario conserva su crÃ©dito


def consultas_permitidas(u: Usuario) -> int:
    return CONSULTAS_BASE + u.bloques_publicidad_vistos * CONSULTAS_POR_AD


def ejecutar_tarea_ia(tarea: str, texto: str, material: str, usuario: Usuario) -> str:
    prompt = f"""
Eres un docente universitario. Analiza al estudiante segÃºn su historial.
Historial pedagÃ³gico: {usuario.perfil_aprendizaje}

Contexto acadÃ©mico: {material}
AcciÃ³n: {tarea}
Estudiante: {texto}
"""
    try:
        resp = model.generate_content(prompt)
        res = resp.text if hasattr(resp, "text") else "Error en respuesta."

        # FIX: [:1000] para conservar los ÃšLTIMOS (mÃ¡s recientes) registros
        nueva_entrada = f"Q: {texto[:100]}... A: {res[:100]}..."
        usuario.perfil_aprendizaje = (nueva_entrada + usuario.perfil_aprendizaje)[:PERFIL_MAX]

        db.session.commit()
        return res

    except Exception as e:
        logger.error("Error al llamar a Gemini: %s", e)
        db.session.rollback()
        return "Error en la conexiÃ³n con la IA. Intenta mÃ¡s tarde."


# ---------------------------------------------------------------------------
# Rutas de autenticaciÃ³n
# ---------------------------------------------------------------------------
@app.route("/login")
def login():
    return google.authorize_redirect(url_for("callback", _external=True))


@app.route("/callback")
def callback():
    token = google.authorize_access_token()

    # FIX: parse_id_token estÃ¡ deprecado en Authlib â‰¥ 1.0; usar userinfo
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
# Ruta principal de tareas (allowlist explÃ­cita)
# ---------------------------------------------------------------------------
@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea: str):
    # FIX: validar tarea contra allowlist antes de cualquier otra cosa
    if tarea not in TAREAS_VALIDAS:
        return jsonify({"error": "Tarea invÃ¡lida"}), 400

    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    # --- Manejo especial: cargar material (no consume consulta) ---
    if tarea == "cargar_material":
        material = request.json.get("material", "")
        # FIX: limitar tamaÃ±o del material
        if len(material) > MAX_MATERIAL:
            return jsonify({"error": f"Material demasiado largo (mÃ¡x {MAX_MATERIAL} caracteres)"}), 400
        u.material = material
        db.session.commit()
        return jsonify({"res": "Material actualizado"})

    # --- LÃ³gica de monetizaciÃ³n ---
    resetear_si_nuevo_dia(u)

    if u.consultas_usadas >= consultas_permitidas(u):
        return jsonify({
            "error": "Consultas agotadas. Mira un anuncio para obtener mÃ¡s.",
            "consultas_usadas": u.consultas_usadas,
            "consultas_permitidas": consultas_permitidas(u),
        }), 403

    # --- Validar input ---
    data = request.get_json(silent=True) or {}
    texto = data.get("texto", "").strip()

    if not texto:
        return jsonify({"error": "El campo 'texto' es obligatorio"}), 400

    # FIX: limitar longitud del texto enviado a la IA
    if len(texto) > MAX_TEXTO:
        return jsonify({"error": f"Texto demasiado largo (mÃ¡x {MAX_TEXTO} caracteres)"}), 400

    # --- Ejecutar tarea ---
    res = ejecutar_tarea_ia(tarea, texto, u.material, u)

    u.consultas_usadas += 1
    u.ultima_consulta = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({
        "resultado": res,
        "consultas_usadas": u.consultas_usadas,
        "consultas_permitidas": consultas_permitidas(u),
    })


# ---------------------------------------------------------------------------
# Ruta auxiliar: registrar anuncio visto
# ---------------------------------------------------------------------------
@app.route("/ver_anuncio", methods=["POST"])
def ver_anuncio():
    """El frontend llama a este endpoint tras mostrar un anuncio."""
    u = get_usuario_actual()
    if not u:
        return jsonify({"error": "No autenticado"}), 401

    u.bloques_publicidad_vistos += 1
    db.session.commit()
    return jsonify({
        "res": "Anuncio registrado",
        "consultas_extra": CONSULTAS_POR_AD,
        "consultas_permitidas": consultas_permitidas(u),
    })


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
