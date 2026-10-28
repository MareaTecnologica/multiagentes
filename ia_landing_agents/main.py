import hashlib
import json
import os
import sqlite3
import time
import urllib.request
import concurrent.futures

# Configuración de Ollama en Local (Respetando tu URL y modelo actuales)
OLLAMA_URL = "http://192.168.1.6:11434/api/generate"
MODEL_NAME = "llama3.2"
MODEL_NAME2 = "gemma4:12b"

DB_NAME = "landing_generator.db"
CONTEXT_FILE = "contexto.txt"


# ==========================================
# CLIENTE OLLAMA LOCAL
# ==========================================
def call_ollama(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("response", "").strip()
    except Exception as e:
        print(f"[Error Ollama] No se pudo conectar con el servidor local en {OLLAMA_URL}: {e}")
        return ""



def call_gema(prompt):
    payload = {
        "model": MODEL_NAME2,
        "prompt": prompt,
        "stream": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("response", "").strip()
    except Exception as e:
        print(f"[Error Ollama] No se pudo conectar con el servidor local en {OLLAMA_URL}: {e}")
        return ""



# ==========================================
# CONFIGURACIÓN Y CONTROL DE BASE DE DATOS
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS web_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context_hash TEXT UNIQUE,
            context_text TEXT,
            color TEXT,
            title TEXT,
            body TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_context_text():
    if not os.path.exists(CONTEXT_FILE):
        raise FileNotFoundError(f"No se encontró el archivo {CONTEXT_FILE}. Créalo con la descripción de tu proyecto.")
    with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def compute_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ==========================================
# AGENTE 1: ANALISTA DE COLOR Y ESTILO
# ==========================================
def agent_1_color(context_text, context_hash):
    print("[Agente 1] Analizando el contexto para definir el color principal...")
    prompt = f"""
    Basándote en el siguiente contexto de mercado, define UN SOLO código de color hexadecimal vibrante y moderno (ej. #2563EB, #7C3AED o #059669) que mejor transmita la emoción de este producto. Responde ÚNICAMENTE con el código hexadecimal, sin explicaciones ni texto adicional.
    Contexto: {context_text}
    """
    color = call_ollama(prompt).strip()
    if not color.startswith("#") or len(color) != 7:
        color = "#2563EB"  # Fallback seguro corporativo

    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("UPDATE web_projects SET color = ? WHERE context_hash = ?", (color, context_hash))
    conn.commit()
    conn.close()
    print(f"[Agente 1] Color seleccionado y guardado: {color}")


# ==========================================
# AGENTE 2: REDACTOR DE TÍTULOS
# ==========================================
def agent_2_title(context_text, context_hash):
    print("[Agente 2] Analizando el contexto para redactar el título principal (H1)...")
    prompt = f"""
    Basándote en el siguiente contexto, crea un título (H1) comercial, magnético y de alto impacto para una landing page. Responde ÚNICAMENTE con el texto del título, sin comillas ni explicaciones.
    Contexto: {context_text}
    """
    title = call_ollama(prompt).replace('"', '').strip()

    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("UPDATE web_projects SET title = ? WHERE context_hash = ?", (title, context_hash))
    conn.commit()
    conn.close()
    print(f"[Agente 2] Título seleccionado y guardado: {title}")


# ==========================================
# AGENTE 3: CREADOR DE CONTENIDO (BODY)
# ==========================================
def agent_3_body(context_text, context_hash):
    print("[Agente 3] Analizando el contexto para estructurar el contenido de valor...")
    prompt = f"""
    Basándote en el siguiente contexto, genera 3 beneficios o características clave en formato HTML limpio utilizando etiquetas <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100"> para cada tarjeta, con un título <h3> y un párrafo <p>. No incluyas etiquetas html ni body globales, solo las tarjetas de contenido interior.
    Contexto: {context_text}
    """
    body_content = call_ollama(prompt)

    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("UPDATE web_projects SET body = ? WHERE context_hash = ?", (body_content, context_hash))
    conn.commit()
    conn.close()
    print("[Agente 3] Cuerpo HTML generado y guardado en SQLite.")


# ==========================================
# AGENTE 4: CONSTRUCTOR Y DISEÑADOR MAESTRO (UI/UX)
# ==========================================
def agent_4_builder(context_hash):
    print("[Agente 4] Iniciando ensamblaje de la Landing Page con diseño profesional...")

    while True:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT color, title, body, status FROM web_projects WHERE context_hash = ?", (context_hash,))
        row = cursor.fetchone()
        conn.close()

        if row:
            color, title, body, status = row

            if status == "COMPLETED":
                print("[Agente 4] La landing page ya fue construida anteriormente.")
                return True

            if color and title and body:
                print("[Agente 4] ¡Insumos listos! Renderizando plantilla web de alta gama...")

                # Plantilla HTML maestra con diseño profesional (Tailwind CSS, efectos visuales, interactividad JS)
                html_content = call_gema(f"dame una pagina web atractiva en html con tailwind css, con un diseño actractivo con el titulo {title} y el contenido debe ser del tema del titulo, devuelve el codigo html puro con css y js, no agregues explicaciones ni comentarios, solo el codigo html completo")

                with open("index.html", "w", encoding="utf-8") as f:
                    f.write(html_content)

                print("[Agente 4] ¡Página web de alta gama generada con éxito en index.html!")
                return True
            else:
                print("[Agente 4] Esperando a que los agentes 1, 2 y 3 terminen... Reintentando en 5s...")
        else:
            print("[Agente 4] Proyecto no encontrado en la base de datos.")

        time.sleep(5)


# ==========================================
# ORQUESTADOR PRINCIPAL
# ==========================================
def main():
    init_db()

    context_text = get_context_text()
    context_hash = compute_hash(context_text)

    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM web_projects WHERE context_hash = ?", (context_hash,))
    row = cursor.fetchone()

    if row and row[0] == "COMPLETED":
        conn.close()
        print("[Orquestador] Esta idea ya fue procesada y validada por completo.")
        return

    if not row:
        cursor.execute("INSERT INTO web_projects (context_hash, context_text, status) VALUES (?, ?, ?)",
                       (context_hash, context_text, "IN_PROGRESS"))
        conn.commit()
    conn.close()

    print("[Orquestador] Ejecutando Agentes 1, 2 y 3 en paralelo...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_color = executor.submit(agent_1_color, context_text, context_hash)
        f_title = executor.submit(agent_2_title, context_text, context_hash)
        f_body = executor.submit(agent_3_body, context_text, context_hash)
        concurrent.futures.wait([f_color, f_title, f_body])

    print("[Orquestador] Fases paralelas finalizadas.")

    # Agente 4 construye la página con plantilla maestra profesional
    built_success = agent_4_builder(context_hash)

    if built_success:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("UPDATE web_projects SET status = 'COMPLETED' WHERE context_hash = ?", (context_hash,))
        conn.commit()
        conn.close()
        print("[Orquestador] ¡Ciclo completo de los agentes finalizado con éxito! Abre 'index.html' en tu navegador.")


if __name__ == "__main__":
    main()