# ================== app.py – Mentor IA Beta 2 Optimizada para Render ==================
import os
import datetime
import google.generativeai as genai
from flask import Flask, request, jsonify, session, send_file, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
CORS(app)

# ================== CONFIG ==================
app.secret_key = os.environ.get("SECRET_KEY", "una_clave_muy_segura_y_larga_por_defecto")
db_uri = os.environ.get("DATABASE_URL")

if not db_uri:
    raise RuntimeError("ERROR: DATABASE_URL no está configurada en Render.")

if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy()
db.init_app(app)

# ================== GOOGLE AUTH ==================
client_id = os.environ.get("GOOGLE_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

if not client_id or not client_secret:
    print("ADVERTENCIA: Las variables de Google no están cargadas correctamente.")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile', 'prompt': 'select_account'}
)

# ================== GEMINI IA ==================
API_KEY = os.environ.get("API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ================== PERSONA DEL ENTRENADOR ==================
ACADEMIC_COACH_PERSONA = """
Eres un entrenador académico universitario especializado en comprensión de textos,
desarrollo conceptual y mejora de respuestas escritas.
SIEMPRE compórtate como un docente universitario.

REGLAS:
- No resuelvas consignas directamente
- Orienta al estudiante
- Fomenta pensamiento crítico
- Corrige de manera pedagógica
"""

# ================== MODELOS ==================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    tipo_usuario = db.Column(db.String(20), default="normal")
    consultas_usadas = db.Column(db.Integer, default=0)
    ultima_consulta = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bloques_publicidad_vistos = db.Column(db.Integer, default=0)
    material = db.Column(db.Text)
    perfil_aprendizaje = db.Column(db.Text, default="")  # Histórico limitado

# Crear tablas al iniciar
try:
    with app.app_context():
        db.create_all()
        print("INFO: Base de datos inicializada correctamente.")
except Exception as e:
    print(f"DEBUG: Error al crear tablas: {e}")

# ================== FUNCIONES DEL ENTRENADOR ==================
def diagnosticar_estudiante(usuario):
    historial = (usuario.perfil_aprendizaje or "").lower()
    diagnostico = []
    if historial.count("no entiendo") > 2 or historial.count("explica") > 3:
        diagnostico.append("Dificultades conceptuales detectadas")
    if historial.count("resumen") > 2:
        diagnostico.append("Dificultad para sintetizar información")
    if historial.count("corrige") > 2 or historial.count("redacción") > 2:
        diagnostico.append("Necesita mejorar redacción académica")
    if not diagnostico:
        diagnostico.append("Sin dificultades claras detectadas")
    return "; ".join(diagnostico)

def actualizar_perfil_aprendizaje(usuario, texto, respuesta):
    try:
        resumen = f"\nConsulta: {texto[:300]}...\nObservación: {respuesta[:300]}..."
        # Limitar histórico a últimas 3 consultas
        lineas = (usuario.perfil_aprendizaje or "").split("\nConsulta:")
        lineas = lineas[-3:]
        usuario.perfil_aprendizaje = "\nConsulta:".join(lineas) + resumen
        db.session.commit()
    except Exception as e:
        print("Error actualizando perfil:", e)

def ejecutar_tarea_ia(tarea, texto, material, usuario):
    prompt = f"""
{ACADEMIC_COACH_PERSONA}

Diagnóstico pedagógico:
{diagnosticar_estudiante(usuario)}

Perfil del estudiante:
{usuario.perfil_aprendizaje or 'Sin historial previo.'}

Contexto relevante:
{material or 'Sin material cargado'}

Acción:
{tarea}

Texto del estudiante:
{texto}
"""
    try:
        respuesta = model.generate_content(prompt)
        if hasattr(respuesta, "text") and respuesta.text:
            actualizar_perfil_aprendizaje(usuario, texto, respuesta.text)
            return respuesta.text
        return "La IA no devolvió respuesta."
    except Exception as e:
        print("Error IA:", e)
        return "Error temporal."

# ================== RUTAS ==================
@app.route('/login')
def login():
    return google.authorize_redirect(url_for('callback', _external=True))

@app.route('/callback')
def callback():
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token)
    email = user_info['email']
    u = Usuario.query.filter_by(email=email).first()
    if not u:
        u = Usuario(email=email, tipo_usuario="normal")
        db.session.add(u)
        db.session.commit()
    session['usuario_id'] = u.id
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route("/", methods=["GET"])
def health_check():
    try:
        return send_file(os.path.join("templates", "index.html"))
    except Exception:
        return jsonify({"status": "Mentor IA online"}), 200

def puede_usar_consulta(u):
    ahora = datetime.datetime.utcnow()
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86400:
        u.consultas_usadas = 0
        u.bloques_publicidad_vistos = 0
        db.session.commit()
    total_permitido = 5 + (u.bloques_publicidad_vistos * 5)
    return u.consultas_usadas < total_permitido

@app.route("/cargar_material", methods=["POST"])
def cargar_material():
    u = Usuario.query.get(session.get("usuario_id"))
    if not u: return jsonify({"error": "No logueado"}), 401
    u.material = request.json.get("material", "")
    db.session.commit()
    return jsonify({"resultado": "Material cargado exitosamente."})

@app.route("/confirmar_publicidad", methods=["POST"])
def confirmar_publicidad():
    u = Usuario.query.get(session.get("usuario_id"))
    if not u: return jsonify({"error": "No logueado"}), 401
    if u.bloques_publicidad_vistos < 2:
        u.bloques_publicidad_vistos += 1
        db.session.commit()
        return jsonify({"resultado": "Consultas desbloqueadas."})
    return jsonify({"error": "Límite alcanzado"}), 400

@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    if tarea == "cargar_material": return cargar_material()
    u = Usuario.query.get(session.get("usuario_id"))
    if not u: return jsonify({"error": "No logueado"}), 401
    if not puede_usar_consulta(u):
        return jsonify({"error": "Consultas agotadas."}), 403
    resultado = ejecutar_tarea_ia(tarea, request.json.get("texto", ""), u.material or "", u)
    u.consultas_usadas += 1
    u.ultima_consulta = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify({"resultado": resultado})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
