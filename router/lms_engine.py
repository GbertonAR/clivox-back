import sqlite3
import os
import json
import random
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
import google.generativeai as genai

# Configurar Gemini
GEN_API_KEY = os.getenv("GEMINI_API_KEY")
if GEN_API_KEY:
    genai.configure(api_key=GEN_API_KEY)

router = APIRouter(prefix="/lms", tags=["LMS Engine"])
DB_PATH = "clivox.db"
UPLOAD_DIR = "uploads/resguardos_examenes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Models for Exams ---
class Opcion(BaseModel):
    id: Optional[int] = None
    texto: str
    es_correcta: bool

class Pregunta(BaseModel):
    id: Optional[int] = None
    enunciado: str
    tipo: str # 'multiple_choice', 'verdadero_falso'
    opciones: List[Opcion]
    audio_url: Optional[str] = None
    video_hint: Optional[str] = None

class RespuestaUsuario(BaseModel):
    id_usuario: str
    id_pregunta: int
    id_opcion_seleccionada: int

class ExamenSubmit(BaseModel):
    id_usuario: str
    id_capacitacion: int
    id_definicion: Optional[int] = None # Para exámenes generados por IA
    respuestas: List[RespuestaUsuario]

class AIDefinition(BaseModel):
    id_capacitacion: int
    temas: str
    cantidad_preguntas: int = 10
    nota_minima: int = 60
    intentos_maximos: int = 5

# --- Attendance Logic ---

@router.get("/asistencia-automatica/{id_capacitacion}")
def calcular_asistencia(id_capacitacion: int):
    """
    Calcula la asistencia automática basada en llamada_eventos.
    Asume que el campo 'sala_id' en llamada_eventos corresponde a la 'link_sala' o ID de la capacitación.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Obtener la sala vinculada a la capacitación
    cursor.execute("SELECT link_sala FROM capacitaciones WHERE id = ?", (id_capacitacion,))
    cap = cursor.fetchone()
    if not cap:
        conn.close()
        raise HTTPException(status_code=404, detail="Capacitación no encontrada")
    
    sala_id = cap['link_sala'] # O usar un mapeo más complejo si es necesario
    
    # 2. Obtener eventos para esa sala
    cursor.execute("""
        SELECT user_id, evento, timestamp 
        FROM llamada_eventos 
        WHERE sala_id = ? 
        ORDER BY user_id, timestamp
    """, (sala_id,))
    eventos = cursor.fetchall()
    
    asistencias = {} # {user_id: total_segundos}
    user_state = {} # {user_id: last_join_time}
    
    for ev in eventos:
        uid = ev['user_id']
        evt = ev['evento'].lower()
        ts = datetime.fromisoformat(ev['timestamp'])
        
        if evt == 'join' or evt == 'participantjoined':
            user_state[uid] = ts
        elif (evt == 'leave' or evt == 'participantleft') and uid in user_state:
            delta = (ts - user_state[uid]).total_seconds()
            asistencias[uid] = asistencias.get(uid, 0) + delta
            del user_state[uid]
            
    # Guardar resultados en la tabla asistencias (opcional, o devolver)
    # Por ahora devolvemos el resumen
    conn.close()
    return asistencias

# --- Exam Logic ---

@router.get("/examen/{id_capacitacion}", response_model=List[Pregunta])
def obtener_examen(id_capacitacion: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM examenes_preguntas WHERE id_capacitacion = ?", (id_capacitacion,))
    preguntas_rows = cursor.fetchall()
    
    examen = []
    for p in preguntas_rows:
        cursor.execute("SELECT * FROM examenes_opciones WHERE id_pregunta = ?", (p['id'],))
        opciones = [dict(o) for o in cursor.fetchall()]
        examen.append({
            "id": p['id'],
            "enunciado": p['enunciado'],
            "tipo": p['tipo'],
            "opciones": opciones
        })
        
    conn.close()
    return examen

# --- AI Exam Generation Logic ---

@router.post("/examen/ia/configurar")
async def configurar_examen_ia(
    id_capacitacion: int = Form(...),
    temas: str = Form(...),
    cantidad_preguntas: int = Form(10),
    nota_minima: int = Form(60),
    intentos_maximos: int = Form(5),
    archivo: Optional[UploadFile] = File(None)
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    ruta_archivo = None
    if archivo:
        ruta_archivo = os.path.join(UPLOAD_DIR, f"cap_{id_capacitacion}_{archivo.filename}")
        with open(ruta_archivo, "wb") as f:
            f.write(await archivo.read())
            
    try:
        cursor.execute("""
            INSERT INTO examenes_definiciones (id_capacitacion, temas, cantidad_preguntas, nota_minima, intentos_maximos, ruta_documento_resguardo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_capacitacion, temas, cantidad_preguntas, nota_minima, intentos_maximos, ruta_archivo))
        definicion_id = cursor.lastrowid
        conn.commit()
        
        # Disparar generación inicial de pool de preguntas (opcional o lazy)
        # Por ahora lo dejamos listo para el primer alumno
        
        return {"id_definicion": definicion_id, "mensaje": "Configuración de examen IA guardada exitosamente."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/examen/ia/generar-pool/{id_definicion}")
async def generar_pool_preguntas(id_definicion: int):
    """
    Usa la IA para generar un pool de preguntas basadas en la definición.
    """
    if not GEN_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key no configurada")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM examenes_definiciones WHERE id = ?", (id_definicion,))
    def_row = cursor.fetchone()
    if not def_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Definición de examen no encontrada")
    
    prompt = f"""
    Genera un examen técnico sobre los siguientes temas: {def_row['temas']}.
    Necesito exactamente {def_row['cantidad_preguntas'] * 2} preguntas para tener variedad.
    Formato JSON:
    [
      {{
        "enunciado": "...",
        "tipo": "multiple_choice",
        "opciones": [
          {{"texto": "...", "es_correcta": true}},
          {{"texto": "...", "es_correcta": false}}
        ],
        "audio_scenario_desc": "Descripción detallada para TTS (opcional)",
        "video_scenario_url": "URL de video de referencia (opcional)"
      }},
      ...
    ]
    Asegúrate de que las preguntas sean profesionales. Si el curso lo requiere, inventa escenarios realistas.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        # Limpiar la respuesta de posibles bloques de código markdown
        text = response.text.replace("```json", "").replace("```", "").strip()
        preguntas_ia = json.loads(text)
        
        for p in preguntas_ia:
            cursor.execute("""
                INSERT INTO examenes_preguntas_ia (id_definicion, enunciado, tipo, audio_url, video_hint)
                VALUES (?, ?, ?, ?, ?)
            """, (id_definicion, p['enunciado'], p['tipo'], p.get('audio_scenario_desc'), p.get('video_scenario_url')))
            p_id = cursor.lastrowid
            
            for o in p['opciones']:
                cursor.execute("""
                    INSERT INTO examenes_opciones_ia (id_pregunta, texto, es_correcta)
                    VALUES (?, ?, ?)
                """, (p_id, o['texto'], o.get('es_correcta', False)))
        
        conn.commit()
        return {"mensaje": f"Se generaron {len(preguntas_ia)} preguntas exitosamente."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error con la IA: {str(e)}")
    finally:
        conn.close()

@router.get("/examen/ia/obtener/{id_usuario}/{id_definicion}")
async def obtener_examen_ia(id_usuario: str, id_definicion: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Verificar intentos
    cursor.execute("""
        SELECT COUNT(*) as cuenta FROM examenes_intentos 
        WHERE id_usuario = ? AND id_definicion = ?
    """, (id_usuario, id_definicion))
    intentos = cursor.fetchone()['cuenta']
    
    cursor.execute("SELECT intentos_maximos, cantidad_preguntas FROM examenes_definiciones WHERE id = ?", (id_definicion,))
    def_row = cursor.fetchone()
    
    if intentos >= def_row['intentos_maximos']:
        conn.close()
        raise HTTPException(status_code=403, detail="Has alcanzado el límite de intentos para este examen.")
    
    # 2. Obtener pool de preguntas
    cursor.execute("SELECT id FROM examenes_preguntas_ia WHERE id_definicion = ?", (id_definicion,))
    pool_ids = [r['id'] for r in cursor.fetchall()]
    
    if not pool_ids:
        conn.close()
        return {"mensaje": "No hay preguntas generadas. Contacte al instructor."}

    # 3. Seleccionar set único para este intento
    # Ver qué preguntas se usaron en intentos anteriores para tratar de no repetirlas
    cursor.execute("SELECT preguntas_json FROM examenes_intentos WHERE id_usuario = ? AND id_definicion = ?", (id_usuario, id_definicion))
    ids_usados = []
    for row in cursor.fetchall():
        ids_usados.extend(json.loads(row['preguntas_json']))
    
    ids_disponibles = [pid for pid in pool_ids if pid not in ids_usados]
    
    # Si no quedan suficientes nuevas, mezclamos
    if len(ids_disponibles) < def_row['cantidad_preguntas']:
        random.shuffle(pool_ids)
        ids_seleccionados = pool_ids[:def_row['cantidad_preguntas']]
    else:
        random.shuffle(ids_disponibles)
        ids_seleccionados = ids_disponibles[:def_row['cantidad_preguntas']]
        
    # 4. Cargar datos de las preguntas seleccionadas
    examen_final = []
    for pid in ids_seleccionados:
        cursor.execute("SELECT * FROM examenes_preguntas_ia WHERE id = ?", (pid,))
        p = cursor.fetchone()
        cursor.execute("SELECT id, texto FROM examenes_opciones_ia WHERE id_pregunta = ?", (pid,))
        opciones = [dict(o) for o in cursor.fetchall()]
        examen_final.append({
            "id": p['id'],
            "enunciado": p['enunciado'],
            "tipo": p['tipo'],
            "opciones": opciones,
            "audio_url": p['audio_url'],
            "video_hint": p['video_hint']
        })
    
    conn.close()
    return {
        "id_definicion": id_definicion,
        "n_intento": intentos + 1,
        "preguntas": examen_final,
        "ids_set": ids_seleccionados
    }

@router.post("/examen/ia/submit")
async def entregar_examen_ia(entrega: ExamenSubmit):
    if not entrega.id_definicion:
        raise HTTPException(status_code=400, detail="Falta id_definicion")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    aciertos = 0
    total = len(entrega.respuestas)
    
    try:
        for resp in entrega.respuestas:
            cursor.execute("SELECT es_correcta FROM examenes_opciones_ia WHERE id = ?", (resp.id_opcion_seleccionada,))
            row = cursor.fetchone()
            if row and row[0]:
                aciertos += 1
        
        puntaje = int((aciertos / total) * 100) if total > 0 else 0
        
        cursor.execute("SELECT nota_minima FROM examenes_definiciones WHERE id = ?", (entrega.id_definicion,))
        nota_minima = cursor.fetchone()[0]
        aprobado = puntaje >= nota_minima
        
        # Registrar intento
        cursor.execute("SELECT COUNT(*) FROM examenes_intentos WHERE id_usuario = ? AND id_definicion = ?", 
                       (entrega.id_usuario, entrega.id_definicion))
        n_intento = cursor.fetchone()[0] + 1
        
        cursor.execute("""
            INSERT INTO examenes_intentos (id_usuario, id_definicion, numero_intento, puntaje, aprobado, fecha, preguntas_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entrega.id_usuario, entrega.id_definicion, n_intento, puntaje, aprobado, datetime.utcnow(), 
              json.dumps([r.id_pregunta for r in entrega.respuestas])))
        
        # También registrar en la tabla global de 'examenes' para compatibilidad con certificados
        cursor.execute("""
            INSERT INTO examenes (id_usuario, id_capacitacion, puntaje, aprobado, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (entrega.id_usuario, entrega.id_capacitacion, puntaje, aprobado, datetime.utcnow()))
        
        conn.commit()
        return {"puntaje": puntaje, "aprobado": aprobado, "intento": n_intento}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- Certificate Generation ---

@router.get("/certificado/{id_usuario}/{id_capacitacion}")
def generar_certificado(id_usuario: str, id_capacitacion: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Verificar si aprobó
    cursor.execute("""
        SELECT aprobado FROM examenes 
        WHERE id_usuario = ? AND id_capacitacion = ? 
        ORDER BY fecha DESC LIMIT 1
    """, (id_usuario, id_capacitacion))
    examen = cursor.fetchone()
    if not examen or not examen['aprobado']:
        conn.close()
        raise HTTPException(status_code=403, detail="El usuario no ha aprobado la capacitación o no tiene registros.")

    # 2. Obtener datos para el diploma
    cursor.execute("SELECT nombre, apellido FROM usuarios WHERE id = ?", (id_usuario,))
    user = cursor.fetchone()
    cursor.execute("SELECT titulo FROM capacitaciones WHERE id = ?", (id_capacitacion,))
    cap = cursor.fetchone()

    if not user or not cap:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario o Capacitación no encontrados")

    # 3. Generar PDF
    cert_folder = "public/certificados"
    os.makedirs(cert_folder, exist_ok=True)
    filename = f"certificado_{id_usuario}_{id_capacitacion}.pdf"
    filepath = os.path.join(cert_folder, filename)

    c = canvas.Canvas(filepath, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Diseño Estético Premium
    # Borde exterior
    c.setStrokeColor(HexColor("#2563eb"))
    c.setLineWidth(5)
    c.rect(1*cm, 1*cm, width-2*cm, height-2*cm)
    
    # Fondo sutil
    c.setFillColor(HexColor("#f8fafc"))
    c.rect(1.5*cm, 1.5*cm, width-3*cm, height-3*cm, fill=1)

    # Título
    c.setFillColor(HexColor("#1e293b"))
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(width/2, height - 5*cm, "CERTIFICADO DE APROBACIÓN")

    # Cuerpo
    c.setFont("Helvetica", 18)
    c.drawCentredString(width/2, height - 8*cm, "Se otorga el presente a:")
    
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(HexColor("#2563eb"))
    c.drawCentredString(width/2, height - 10*cm, f"{user['nombre']} {user['apellido']}")

    c.setFillColor(HexColor("#1e293b"))
    c.setFont("Helvetica", 18)
    c.drawCentredString(width/2, height - 12*cm, "Por haber completado con éxito la capacitación en:")
    
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 14*cm, f"\"{cap['titulo']}\"")

    # Fecha y Firma
    fecha_str = datetime.now().strftime("%d de %B de %Y")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 17*cm, f"Emitido el {fecha_str}")

    # Logo / Marca de agua Clivox
    c.setFont("Helvetica-Bold", 60)
    c.setStrokeColor(HexColor("#cbd5e1"))
    c.setFillAlpha(0.1)
    c.drawCentredString(width/2, height/2, "CLIVOX")
    
    c.save()

    # 4. Registrar emisión en DB
    cursor.execute("""
        INSERT INTO certificados_emitidos (id_usuario, id_capacitacion, ruta_certificado, fecha_emision)
        VALUES (?, ?, ?, ?)
    """, (id_usuario, id_capacitacion, filepath, datetime.utcnow()))
    conn.commit()
    conn.close()

    return FileResponse(filepath, media_type='application/pdf', filename=filename)
