🧠 Mentor IA Premium Académico
Una herramienta educativa con IA que ayuda a estudiantes a mejorar comprensión y producción académica, corrigiendo textos, explicando conceptos y generando resúmenes o mapas conceptuales.
🚀 Funcionalidades principales
🔑 Login Google – Acceso rápido y seguro.
👑 Súper usuario – gunmachine786@gmail.com puede usar todas las funciones y monitorear el sistema.
📊 Gestión de consultas – Cada acción gasta consultas; límite diario para usuarios gratuitos.
✍️ Corrección académica – Penaliza copia-pega y ausencia de conectores; premia reformulación propia.
📝 Resumen automático – Resume textos o PDFs proporcionados por el alumno.
🧩 Mapa conceptual – Genera red conceptual automática del material ingresado.
🎤 Rap académico – Convierte contenido académico en rap respetando el material original.
📚 Carga de material – PDFs o texto de consulta; no consume consultas.
🗂 Estructura del proyecto
app.py → Servidor principal (Flask).
templates/ → Archivos HTML para la interfaz.
.env → Variables: API_KEY, Google Client ID, Secret Key.
mentor_db.sqlite → Base de datos local SQLite.
⚙️ Variables de entorno
Plain text
Copiar código
API_KEY=<tu_api_key>
GOOGLE_CLIENT_ID=<tu_cliente_id_google>
SECRET_KEY=<clave_secreta_para_sesiones>
🖥 Cómo probar rápidamente
Instalar dependencias:
Bash
Copiar código
pip install -r requirements.txt
Ejecutar servidor:
Bash
Copiar código
python app.py
Abrir navegador:
Plain text
Copiar código
http://localhost:5000
Probar funciones desde la interfaz o mediante POST a las rutas:
/login_google – Login con tu correo.
/analizar – Corrige y analiza textos.
/resumen – Genera resúmenes automáticos.
/corregir – Corrige ejercicios/respuestas del alumno.
/desbloquear_publicidad – Incrementa consultas para usuarios gratuitos.
