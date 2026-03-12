# ================== app.py – Mentor IA Premium Académico ==================
from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import os, datetime, requests

# ================== CARGAR VARIABLES DE ENTORNO ==================
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# ================== BASE DE DATOS ==================
db_path = os.path.join(os.path.dirname(__file__), "mentor_db.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ================== MODELOS ==================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    tipo_usuario = db.Column(db.String(20), default="normal")
    consultas_usadas = db.Column(db.Integer, default=0)
    ultima_consulta = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    material = db.Column(db.Text)  # Contenido de PDFs o material de referencia

class Estadistica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer)
    tipo_consulta = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# ================== CONFIGURACIÓN ==================
CONSULTAS_MAX = 10
CONSULTAS_PUBLICIDAD = 5
API_KEY = os.environ.get("API_KEY")
API_BASE_URL = "https://api.tuentrenador.com"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
SUPER_EMAIL = "gunmachine786@gmail.com"

# ================== FUNCIONES AUXILIARES ==================
def verificar_token_google(token):
    try:
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            return None
        return idinfo
    except Exception:
        return None

def puede_usar_consulta(usuario):
    ahora = datetime.datetime.utcnow()
    if not usuario.ultima_consulta or (ahora - usuario.ultima_consulta).total_seconds() > 86400:
        usuario.consultas_usadas = 0
        usuario.ultima_consulta = ahora
        db.session.commit()
    if usuario.tipo_usuario == "super":
        return True
    return usuario.consultas_usadas < CONSULTAS_MAX

def registrar_consulta(usuario, tipo):
    if usuario.tipo_usuario != "super":
        usuario.consultas_usadas += 1
        usuario.ultima_consulta = datetime.datetime.utcnow()
        db.session.commit()
    stat = Estadistica(usuario_id=usuario.id, tipo_consulta=tipo)
    db.session.add(stat)
    db.session.commit()

def llamada_api(endpoint, texto, respuesta=None):
    payload = {"texto": texto}
    if respuesta:
        payload["respuesta"] = respuesta
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        r = requests.post(f"{API_BASE_URL}/{endpoint}", json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.json().get("resultado","✅ Sin resultado")
        return f"❌ Error API: {r.status_code}"
    except Exception as e:
        return f"❌ Excepción API: {str(e)}"

def evaluar_texto(usuario, texto, tipo, respuesta=None, endpoint="analizar"):
    if not puede_usar_consulta(usuario):
        return False, "Has alcanzado tu límite diario."
    registrar_consulta(usuario, tipo)
    resultado = llamada_api(endpoint, texto, respuesta)
    return True, resultado

# ================== RUTAS ==================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login_google", methods=["POST"])
def login_google():
    data = request.json
    token_google = data.get("token")
    info = verificar_token_google(token_google)
    if not info:
        return jsonify({"error": "Token inválido"}), 401
    email = info["email"]
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        usuario = Usuario(email=email)
        if email == SUPER_EMAIL:
            usuario.tipo_usuario = "super"
        db.session.add(usuario)
        db.session.commit()
    session["usuario_id"] = usuario.id
    return jsonify({"resultado": "Login exitoso", "tipo_usuario": usuario.tipo_usuario})

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"resultado": "Sesión cerrada"})

@app.route("/estado_usuario")
def estado_usuario():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Usuario no logueado"}), 401
    usuario = Usuario.query.get(usuario_id)
    restantes = CONSULTAS_MAX - usuario.consultas_usadas if usuario.tipo_usuario != "super" else "Ilimitadas"
    return jsonify({"tipo_usuario": usuario.tipo_usuario, "consultas_usadas": usuario.consultas_usadas, "consultas_restantes": restantes})

@app.route("/desbloquear_publicidad", methods=["POST"])
def desbloquear_publicidad():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Usuario no logueado"}), 401
    usuario = Usuario.query.get(usuario_id)
    if usuario.tipo_usuario == "super":
        return jsonify({"resultado": "El súper usuario no necesita desbloquear publicidad."})
    usuario.consultas_usadas = max(0, usuario.consultas_usadas - CONSULTAS_PUBLICIDAD)
    db.session.commit()
    return jsonify({"resultado": f"Consultas incrementadas en {CONSULTAS_PUBLICIDAD} por publicidad."})

# ================== FUNCIONES DEL ENTRENADOR ==================
@app.route("/cargar_material", methods=["POST"])
def cargar_material():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Usuario no logueado"}), 401
    usuario = Usuario.query.get(usuario_id)
    data = request.json
    contenido = data.get("material","")
    usuario.material = contenido
    db.session.commit()
    return jsonify({"resultado": "Material de referencia cargado correctamente."})

@app.route("/analizar", methods=["POST"])
def analizar():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Usuario no logueado"}), 401
    usuario = Usuario.query.get(usuario_id)
    texto = request.json.get("texto","")
    ok, resultado = evaluar_texto(usuario, texto, "analizar", endpoint="analizar")
    return jsonify({"resultado": resultado})

@app.route("/resumen", methods=["POST"])
def resumen():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Usuario no logueado"}), 401
    usuario = Usuario.query.get(usuario_id)
    texto = request.json.get("texto","")
    ok, resultado = evaluar_texto(usuario, texto, "resumen", endpoint="resumen")
    return jsonify({"resultado": resultado})

@app.route("/rap_academico", methods=["POST"])
def rap_academico():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Usuario no logueado"}), 401
    usuario = Usuario.query.get(usuario_id)
    texto = usuario.material or ""
    ok, resultado = evaluar_texto(usuario, texto, "rap_academico", endpoint="rap_academico")
    return jsonify({"resultado": resultado})

@app.route("/mapa_conceptual", methods=["POST"])
def mapa_conceptual():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Usuario no logueado"}), 401
    usuario = Usuario.query.get(usuario_id)
    texto = usuario.material or ""
    ok, resultado = evaluar_texto(usuario, texto, "mapa_conceptual", endpoint="mapa_conceptual")
    return jsonify({"resultado": resultado})

@app.route("/corregir", methods=["POST"])
def corregir():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Usuario no logueado"}), 401
    usuario = Usuario.query.get(usuario_id)
    data = request.json
    texto = data.get("texto","")
    respuesta = data.get("respuesta","")
    ok, resultado = evaluar_texto(usuario, texto, "corregir", respuesta=respuesta, endpoint="corregir")
    return jsonify({"resultado": resultado})

# ================== RUN ==================
if __name__ == "__main__":
    app.run()
