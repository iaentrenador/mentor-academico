# ================== app.py – Mentor IA Beta 1 ==================
import os, datetime, google.generativeai as genai
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# Configuración Gemini
genai.configure(api_key=os.environ.get("API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Persona Académica para el Entrenador
ACADEMIC_COACH_PERSONA = """
Eres un entrenador académico universitario especializado en comprensión de textos, desarrollo conceptual y mejora de respuestas escritas.
Tu objetivo no es hacer las tareas por el estudiante, sino entrenar su pensamiento académico.
SIEMPRE compórtate como un docente universitario.

REGLAS OBLIGATORIAS:
1. Nunca escribas la respuesta completa al ejercicio.
2. No resuelvas consignas directamente.
3. Evalúa, orienta y explica.
4. Proporciona ejemplos similares pero diferentes si se trata de ejercicios.
5. El estudiante debe construir su propia respuesta.
"""

# Base de Datos
db_path = os.path.join(os.path.dirname(__file__), "mentor_db.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    tipo_usuario = db.Column(db.String(20), default="normal")
    consultas_usadas = db.Column(db.Integer, default=0)
    ultima_consulta = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bloques_publicidad_vistos = db.Column(db.Integer, default=0) 
    material = db.Column(db.Text)

with app.app_context():
    db.create_all()

def puede_usar_consulta(u):
    if u.tipo_usuario == "super": return True
    ahora = datetime.datetime.utcnow()
    if u.ultima_consulta and (ahora - u.ultima_consulta).total_seconds() > 86400:
        u.consultas_usadas = 0
        u.bloques_publicidad_vistos = 0
        db.session.commit()
    total_permitido = 5 + (u.bloques_publicidad_vistos * 5)
    return u.consultas_usadas < total_permitido

# Diccionario de funciones del Entrenador
def ejecutar_tarea_ia(tarea, texto, material):
    instrucciones = {
        "analizar": f"{ACADEMIC_COACH_PERSONA}\n\nContexto: {material}\n\nSolicitud: Analiza y explica el siguiente texto: {texto}",
        "evaluar": f"{ACADEMIC_COACH_PERSONA}\n\nContexto: {material}\n\nEvalúa la respuesta: '{texto}'. Estructura: 1. Calificación, 2. Análisis, 3. Fortalezas, 4. Aspectos a mejorar, 5. Sugerencias, 6. Reintento sugerido.",
        "resumen": f"{ACADEMIC_COACH_PERSONA}\n\nContexto: {material}\n\nGenera un resumen profesional, jerárquico y con conceptos clave del texto: {texto}",
        "mapa_conceptual": f"{ACADEMIC_COACH_PERSONA}\n\nContexto: {material}\n\nCrea una estructura de red conceptual para: {texto}",
        "rap": f"{ACADEMIC_COACH_PERSONA}\n\nContexto: {material}\n\nCrea un 'Rap Técnico' para memorización técnica de: {texto}. Usa lenguaje literal y términos académicos.",
        "explicar": f"{ACADEMIC_COACH_PERSONA}\n\nContexto: {material}\n\nExplica con profundidad académica la siguiente pregunta/consigna: {texto}",
        "aleatorio": f"{ACADEMIC_COACH_PERSONA}\n\nContexto: {material}\n\nGenera un ejercicio práctico o concepto complejo relacionado con el material proporcionado."
    }
    prompt = instrucciones.get(tarea, f"{ACADEMIC_COACH_PERSONA}\n\nProcesa: {texto}")
    return model.generate_content(prompt).text



@app.route("/cargar_material", methods=["POST"])
def cargar_material():
    u = Usuario.query.get(session.get("usuario_id"))
    if not u: return jsonify({"error": "No logueado"}), 401
    data = request.json
    u.material = data.get("material", "")
    db.session.commit()
    return jsonify({"resultado": "Material cargado exitosamente."})

@app.route("/confirmar_publicidad", methods=["POST"])
def confirmar_publicidad():
    u = Usuario.query.get(session.get("usuario_id"))
    if not u: return jsonify({"error": "No logueado"}), 401
    if u.bloques_publicidad_vistos < 2:
        u.bloques_publicidad_vistos += 1
        db.session.commit()
        return jsonify({"resultado": "Bloque de consultas activado."})
    return jsonify({"error": "Límite alcanzado"}), 400

@app.route("/<tarea>", methods=["POST"])
def manejar_tarea(tarea):
    if tarea == "cargar_material": return cargar_material()
    
    u = Usuario.query.get(session.get("usuario_id"))
    if not u or not puede_usar_consulta(u): 
        return jsonify({"error": "Consultas agotadas."}), 403
    
    data = request.json
    resultado = ejecutar_tarea_ia(tarea, data.get("texto", ""), u.material or "")
    
    if u.tipo_usuario != "super":
        u.consultas_usadas += 1
        u.ultima_consulta = datetime.datetime.utcnow()
        db.session.commit()
    return jsonify({"resultado": resultado})

if __name__ == "__main__": app.run()
    
