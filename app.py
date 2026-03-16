import os
import datetime
import google.generativeai as genai
from flask import Flask, request, jsonify, session, send_file, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Google Auth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Gemini
genai.configure(api_key=os.environ.get("API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    consultas_usadas = db.Column(db.Integer, default=0)
    ultima_consulta = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bloques_publicidad_vistos = db.Column(db.Integer, default=0)
    material = db.Column(db.Text, default="")
    perfil_aprendizaje = db.Column(db.Text, default="")

with app.app_context():
    db.create_all()

def ejecutar_tarea_ia(tarea, texto, material, usuario):
    prompt = f"""
    Eres un docente universitario. Analiza al estudiante según su historial.
    Historial pedagógico: {usuario.perfil_aprendizaje}
    
    Contexto académico: {material}
    Acción: {tarea}
    Estudiante: {texto}
    """
    try:
        resp = model.generate_content(prompt)
        res = resp.text if hasattr(resp, "text") else "Error en respuesta."
        
        # Actualizar perfil (Guardamos solo lo último para ahorrar memoria)
        usuario.perfil_aprendizaje = (f"Q: {texto[:100]}... A: {res[:100]}..." + usuario.perfil_aprendizaje)[-1000:]
        db.session.commit()
        return res
    except:
        return "Error en la conexión con la IA."

@app.route('/login')
def login():
    return google.authorize_redirect(url_for('callback', _external=True))

@app.route('/callback')
def callback():
    token = google.authorize_access_token()
    email = google.parse_id_token(token)['email']
    u = Usuario.query.filter_by(email=email).first() or Usuario(email=email)
    db.session.add(u)
    db.session.commit()
    session['usuario_id'] = u.id
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear() # Cierra sesión y permite cambiar de cuenta
    return redirect('/')

@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    u = Usuario.query.get(session.get("usuario_id"))
    if not u: return jsonify({"error": "No logueado"}), 401
    
    # Lógica de monetización simple
    ahora = datetime.datetime.utcnow()
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86400:
        u.consultas_usadas = 0
        u.bloques_publicidad_vistos = 0
    
    if u.consultas_usadas >= (5 + (u.bloques_publicidad_vistos * 5)):
        return jsonify({"error": "Consultas agotadas. Mira un anuncio."}), 403

    texto = request.json.get("texto", "") if tarea != "cargar_material" else ""
    if tarea == "cargar_material":
        u.material = request.json.get("material", "")
        db.session.commit()
        return jsonify({"res": "Material actualizado"})
    
    res = ejecutar_tarea_ia(tarea, texto, u.material, u)
    u.consultas_usadas += 1
    u.ultima_consulta = ahora
    db.session.commit()
    return jsonify({"resultado": res})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    
