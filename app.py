# ================== app.py – Mentor IA Beta 5.3 ==================

import os
import datetime
import threading
import google.generativeai as genai
from flask import Flask, request, jsonify, session, send_file, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import chromadb
from sentence_transformers import SentenceTransformer
import fitz

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================
app.secret_key = os.environ.get("SECRET_KEY", "clave_segura_default")
FRONTEND_KEY = os.environ.get("FRONTEND_KEY")
MAX_MATERIAL = 200000

# ================= RATE LIMIT =================
limiter = Limiter(get_remote_address, app=app, default_limits=["60 per minute"])

# ================= BASE DE DATOS =================
db_uri = os.environ.get("DATABASE_URL")
if not db_uri:
    raise RuntimeError("ERROR: DATABASE_URL no está configurada.")

if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy()
db.init_app(app)

# ================= GOOGLE AUTH =================
client_id = os.environ.get("GOOGLE_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=client_id,
    client_secret=client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile", "prompt": "select_account"},
)

# ================= GEMINI =================
API_KEY = os.environ.get("API_KEY")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

MAX_CONSULTAS_SIMULTANEAS = 3
semaforo_ia = threading.Semaphore(MAX_CONSULTAS_SIMULTANEAS)

# ================= CACHE IA =================
CACHE_RESPUESTAS = {}

# ================= RAG =================
modelo_embeddings = SentenceTransformer("all-MiniLM-L6-v2")

cliente_vector = chromadb.PersistentClient(path="./chroma_db")
coleccion = cliente_vector.get_or_create_collection(name="memoria_academica")

# ================= PERSONA =================
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

# ================= MODELOS =================

class Usuario(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    tipo_usuario = db.Column(db.String(20), default="normal")
    consultas_usadas = db.Column(db.Integer, default=0)
    ultima_consulta = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bloques_publicidad_vistos = db.Column(db.Integer, default=0)
    material = db.Column(db.Text)
    perfil_aprendizaje = db.Column(db.Text, default="")


class LogConsulta(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer)
    tarea = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)


with app.app_context():
    db.create_all()

# ================= FUNCIONES RAG =================

def dividir_texto(texto, tamaño=500, solapamiento=50):

    palabras = texto.split()
    fragmentos = []
    paso = tamaño - solapamiento

    for i in range(0, len(palabras), paso):
        fragmento = " ".join(palabras[i:i+tamaño])
        fragmentos.append(fragmento)

    return fragmentos


def indexar_material(usuario_id, texto):

    try:

        try:
            coleccion.delete(where={"usuario_id": str(usuario_id)})
        except:
            pass

        fragmentos = dividir_texto(texto)

        vectores = modelo_embeddings.encode(fragmentos)

        for i, vector in enumerate(vectores):

            coleccion.add(
                embeddings=[vector.tolist()],
                documents=[fragmentos[i]],
                ids=[f"{usuario_id}_{i}"],
                metadatas=[{"usuario_id": str(usuario_id)}]
            )

    except Exception as e:
        print("Error indexando material:", e)


def buscar_contexto(pregunta, usuario_id):

    try:

        vector = modelo_embeddings.encode(pregunta).tolist()

        resultados = coleccion.query(
            query_embeddings=[vector],
            where={"usuario_id": str(usuario_id)},
            n_results=4
        )

        docs = resultados.get("documents", [[]])[0]

        return "\n".join(docs)

    except:
        return ""

# ================= DIAGNÓSTICO PEDAGÓGICO =================

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

# ================= INFORME PROGRESO =================

def generar_informe_progreso(usuario):

    historial = usuario.perfil_aprendizaje or "Sin datos suficientes."

    prompt = f"""
Analiza el siguiente historial de aprendizaje de un estudiante y genera
un informe docente breve que incluya:

- fortalezas
- debilidades
- evolución del estudiante
- recomendación pedagógica

Historial:
{historial}
"""

    try:

        with semaforo_ia:
            respuesta = model.generate_content(prompt)

        if respuesta.text:
            return respuesta.text

    except Exception as e:
        print("Error generando informe:", e)

    return "No se pudo generar informe."

# ================= DETECCIÓN DE POSIBLE PLAGIO =================

def detectar_posible_plagio(texto_estudiante, usuario_id, umbral=0.85, max_resultados=3):

    try:

        vector_estudiante = modelo_embeddings.encode(texto_estudiante).tolist()

        resultados = coleccion.query(
            query_embeddings=[vector_estudiante],
            where={"usuario_id": str(usuario_id)},
            n_results=max_resultados
        )

        documentos = resultados.get("documents", [[]])[0]
        distancias = resultados.get("distances", [[]])[0]

        coincidencias = []

        for doc, distancia in zip(documentos, distancias):

            similitud = 1 - distancia

            if similitud >= umbral:

                coincidencias.append({
                    "similitud": round(similitud, 3),
                    "fragmento": doc[:500]
                })

        if coincidencias:

            return {
                "posible_plagio": True,
                "coincidencias": coincidencias
            }

        return {
            "posible_plagio": False,
            "coincidencias": []
        }

    except Exception as e:

        print("Error detección plagio:", e)

        return {
            "posible_plagio": False,
            "coincidencias": []
        }

# ================= PERFIL PEDAGÓGICO =================

def condensar_perfil_si_es_necesario(usuario):

    if len(usuario.perfil_aprendizaje) > 5000:

        try:

            prompt = f"""
Resume este historial de aprendizaje del estudiante manteniendo únicamente:

- tendencias de errores
- progresos del estudiante
- debilidades recurrentes

Historial:
{usuario.perfil_aprendizaje}
"""

            with semaforo_ia:
                respuesta = model.generate_content(prompt)

            if respuesta.text:
                usuario.perfil_aprendizaje = respuesta.text
                db.session.commit()

        except Exception as e:
            print("Error condensando perfil:", e)


def actualizar_perfil_aprendizaje(usuario, texto, respuesta):

    try:

        resumen = f"\nConsulta: {texto[:300]}...\nObservación: {respuesta[:300]}..."

        usuario.perfil_aprendizaje = (usuario.perfil_aprendizaje or "") + resumen

        db.session.commit()

        condensar_perfil_si_es_necesario(usuario)

    except Exception as e:
        print("Error actualizando perfil:", e)

# ================= FUNCIONES IA =================

def ejecutar_tarea_ia(tarea, texto, material, usuario):

    clave_cache = f"{tarea}:{texto[:200]}"

    if clave_cache in CACHE_RESPUESTAS:
        return CACHE_RESPUESTAS[clave_cache]

    contexto = buscar_contexto(texto, usuario.id) or material
    perfil = usuario.perfil_aprendizaje or "Sin historial previo."
    diagnostico = diagnosticar_estudiante(usuario)

    prompt = f"""
{ACADEMIC_COACH_PERSONA}

Diagnóstico pedagógico:
{diagnostico}

Perfil del estudiante:
{perfil}

Contexto relevante:
{contexto}

Acción:
{tarea}

Texto del estudiante:
{texto}
"""

    try:

        with semaforo_ia:

            respuesta = model.generate_content(prompt)

            if hasattr(respuesta, "text") and respuesta.text:

                actualizar_perfil_aprendizaje(usuario, texto, respuesta.text)

                CACHE_RESPUESTAS[clave_cache] = respuesta.text

                return respuesta.text

            return "La IA no devolvió respuesta."

    except Exception as e:

        print("Error IA:", e)

        return "Error temporal."


# ... el resto de tus rutas Flask permanecen exactamente iguales ...


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
