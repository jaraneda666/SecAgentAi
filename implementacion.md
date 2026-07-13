# 📐 Implementación Técnica — SecAgent

> Documento técnico que describe la arquitectura, diseño y decisiones de implementación del agente **SecAgent**.

---

## 1. Visión General

SecAgent es un **agente de reconocimiento autónomo** construido sobre el patrón **ReAct** (Reason + Act). El LLM razona sobre la solicitud del usuario, decide qué herramienta llamar, ejecuta la herramienta (Nmap), recibe los resultados y genera una respuesta final con análisis y recomendaciones.

```
Usuario ──► [LLM Ollama] ──► [Tool Call: scan_target] ──► [Nmap] ──► [LLM Ollama] ──► Análisis
```

---

## 2. Arquitectura del Sistema

### Diagrama de flujo

```
┌─────────────────────────────────────────────────────────┐
│                        secagent.py                      │
│                                                         │
│  BLOQUE 1: Auto-instalación de librerías Python         │
│      ↓                                                  │
│  BLOQUE 2: Verificación e inicio del servicio Ollama    │
│      ↓                                                  │
│  BLOQUE 3: Menú inteligente de selección de modelo LLM  │
│      ↓                                                  │
│  BLOQUE 4: Fat Tool - scan_target (Nmap)                │
│      ↓                                                  │
│  BLOQUE 5: Definición de Tools + System Prompt          │
│      ↓                                                  │
│  BLOQUE 6: Bucle principal del agente (ReAct loop)      │
│      ↓                                                  │
│  BLOQUE 7: Main — CLI / Modo interactivo                │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Descripción de Bloques

### Bloque 1 — Auto-instalación de Dependencias Python

**Función:** `verificar_dependencias()`

Intenta importar `nmap` y `ollama`. Si alguno falla con `ImportError`, ejecuta automáticamente:

```python
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
```

Esto garantiza que el script sea autónomo y no requiera intervención manual del usuario para instalar dependencias.

**Dependencias requeridas:**
```
python-nmap>=0.7.1    # Wrapper Python para Nmap
ollama>=0.2.0         # SDK oficial de Ollama
```

---

### Bloque 2 — Verificación e Inicio del Servicio Ollama

**Función:** `verificar_servicio_ollama()`

Implementa tres niveles de verificación y auto-recuperación:

| Paso | Verificación | Acción si falla |
|------|-------------|-----------------|
| 1 | `shutil.which("ollama")` — ¿Existe el binario? | Instala Ollama vía `curl` (Linux) |
| 2 | `subprocess.check_output(["ollama", "list"])` — ¿Responde el daemon? | Intenta `sudo systemctl start ollama` |
| 3 | Si `systemctl` falla | Lanza `ollama serve` como proceso hijo con `subprocess.Popen()` |

```python
subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)  # Espera 3s para que el puerto quede disponible
```

---

### Bloque 3 — Menú Inteligente de Selección de Modelo

**Función:** `configurar_modelo() -> str`

Implementa un menú dinámico que:
1. Consulta los modelos instalados con `ollama.list()`.
2. Separa los modelos en dos categorías: **instalados** (listos para usar) y **recomendados** (requieren descarga).
3. Si el usuario selecciona un modelo no instalado, ejecuta `ollama pull <modelo>`.
4. Soporta entrada manual de nombre de modelo personalizado.

```python
respuesta = ollama.list()
# Maneja tanto respuestas dict como objetos con atributo .models
if hasattr(respuesta, 'models'):
    lista_modelos = respuesta.models
elif isinstance(respuesta, dict):
    lista_modelos = respuesta.get('models', [])
```

**Variable global resultante:** `MODEL` — Contiene el nombre del modelo activo para toda la sesión.

---

### Bloque 4 — Fat Tool: `scan_target`

**Función:** `scan_target(ip: str, port_group: str = "top", custom_ports = None) -> dict`

Este es el núcleo de la capacidad de reconocimiento. Se implementa como una **Fat Tool** (herramienta única y robusta) en lugar de múltiples herramientas pequeñas, para **reducir alucinaciones** del LLM.

**Grupos de puertos predefinidos:**

```python
COMMON = {
    "web":    [80, 443, 8080, 8443],
    "remote": [22, 23, 3389, 5900],
    "db":     [3306, 5432, 1433, 27017, 6379],
    "mail":   [25, 110, 143, 465, 587, 993, 995],
    "top":    [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 8080],
}
```

**Flags de Nmap utilizados:** `-Pn -sT -T4`
- `-Pn`: Omite el ping previo (trata el host como activo siempre).
- `-sT`: TCP Connect Scan (no requiere privilegios de root).
- `-T4`: Velocidad agresiva (reduce tiempos de espera).

**Formato de retorno:**
```python
{
    "ip": "192.168.1.1",
    "scanned_ports": "21,22,80,443,...",
    "open": [
        {"port": 22, "service": "ssh"},
        {"port": 80, "service": "http"}
    ]
}
```

**Manejo de errores:**
```python
except nmap.PortScannerError as e:
    return {"error": f"Error de Nmap: {str(e)}"}
except Exception as e:
    return {"error": f"Excepción inesperada: {str(e)}"}
```

---

### Bloque 5 — Definición de Tools y System Prompt

#### Tool Schema (JSON Schema para Ollama)

```python
TOOLS = [{
    "type": "function",
    "function": {
        "name": "scan_target",
        "parameters": {
            "type": "object",
            "properties": {
                "ip":           {"type": "string"},
                "port_group":   {"type": "string", "enum": ["top","web","db","remote","mail"]},
                "custom_ports": {"type": "string"}
            },
            "required": ["ip"]
        }
    }
}]
```

**Dispatch table** para mapear nombre de función → función Python:
```python
DISPATCH = {"scan_target": scan_target}
```

#### System Prompt

```
Eres un experto en ciberseguridad defensiva y auditoría de infraestructuras.
Tu tarea es analizar los objetivos solicitados utilizando la herramienta `scan_target`.
Por defecto, confía en el parámetro 'port_group' y no uses 'custom_ports' a menos que te lo pidan.
Resume los hallazgos en español y entrega recomendaciones de mitigación (hardening) concisas.
```

El prompt instruye al modelo a:
- Usar `port_group` por defecto (evita sobrecarga con puertos personalizados).
- Responder siempre en español.
- Entregar análisis + recomendaciones de hardening.

---

### Bloque 6 — Bucle Principal del Agente (ReAct Loop)

**Función:** `run_agent(prompt: str)`

Implementa el patrón **ReAct** con un límite de 8 iteraciones para prevenir bucles infinitos.

```
Iteración:
  1. Enviar messages a ollama.chat() con tools disponibles
  2. Si el modelo NO llama a una tool → imprimir respuesta final y retornar
  3. Si el modelo llama a una tool:
     a. Extraer nombre y argumentos de la tool_call
     b. Deserializar args si vienen como string JSON
     c. Ejecutar la función vía DISPATCH[fn](**args)
     d. Agregar resultado al historial como rol "tool"
     e. Repetir desde paso 1
```

**Historial de mensajes (Context Window):**
```python
messages = [
    {"role": "system",  "content": SYSTEM},
    {"role": "user",    "content": prompt},
    # ↓ Se agregan dinámicamente:
    {"role": "assistant", "tool_calls": [...]},  # Respuesta del LLM
    {"role": "tool",    "content": json.dumps(result)},  # Resultado de herramienta
    # ... hasta respuesta final
]
```

---

### Bloque 7 — Punto de Entrada (Main)

Soporta dos modos de operación:

**Modo CLI (argumento directo):**
```bash
python secagent.py "Escanea 10.0.0.1 en puertos web"
# → Equivalente a: run_agent("Escanea 10.0.0.1 en puertos web")
```

**Modo interactivo (loop infinito):**
```bash
python secagent.py
# → Prompt interactivo con Ctrl+C para salir
```

```python
while True:
    try:
        run_agent(input("\n> "))
    except (KeyboardInterrupt, EOFError):
        print("\nAdiós.")
        break
```

---

## 4. Decisiones de Diseño

### ¿Por qué una sola herramienta (Fat Tool)?

Los LLMs tienden a **alucinar** cuando tienen muchas herramientas disponibles, seleccionando las incorrectas o inventando parámetros. Al unificar toda la lógica de escaneo en `scan_target`, se reduce drásticamente la superficie de error del modelo.

### ¿Por qué `-sT` (TCP Connect) en lugar de `-sS` (SYN Scan)?

El TCP Connect Scan no requiere privilegios de root/administrador, lo que hace que el script sea más portable y fácil de usar sin configuración adicional. El SYN Scan requeriría ejecutar el script con `sudo`.

### ¿Por qué Ollama y no una API cloud?

- **Privacidad**: Los datos del escaneo nunca salen del sistema local.
- **Sin costo**: No se generan costos por tokens en APIs externas.
- **Offline**: Funciona sin conexión a internet una vez descargado el modelo.
- **Control**: El usuario elige exactamente qué modelo usar.

### ¿Por qué un límite de 8 iteraciones?

Para prevenir bucles infinitos en casos donde el LLM continúe llamando herramientas sin llegar a una conclusión. 8 iteraciones son suficientes para: 1 llamada inicial + hasta 7 rondas de tool calls, lo cual cubre casos complejos sin riesgo de ejecución indefinida.

---

## 5. Flujo de Ejecución Completo

```
1. Script inicia
2. verificar_dependencias() → instala nmap, ollama si faltan
3. verificar_servicio_ollama() → asegura que ollama esté corriendo
4. configurar_modelo() → usuario elige modelo → MODEL = "llama3.1:latest"
5. __main__ detecta modo (CLI vs interactivo)
6. Usuario ingresa prompt: "Escanea 192.168.1.50"
7. run_agent("Escanea 192.168.1.50"):
   a. Llama ollama.chat() → LLM genera tool_call: scan_target(ip="192.168.1.50")
   b. DISPATCH ejecuta scan_target("192.168.1.50", "top")
   c. Nmap escanea y retorna puertos abiertos
   d. Resultado se agrega al historial como rol "tool"
   e. Llama ollama.chat() de nuevo → LLM genera respuesta final en español
   f. Imprime análisis y recomendaciones de hardening
8. Loop regresa al prompt ">"
```

---

## 6. Tecnologías Utilizadas

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| Python | 3.8+ | Lenguaje base |
| Ollama | ≥0.2.0 | Motor LLM local + SDK Python |
| python-nmap | ≥0.7.1 | Wrapper Python para Nmap |
| Nmap | cualquiera | Motor de escaneo de puertos |
| JSON Schema | — | Definición de herramientas para el LLM |

---

## 7. Posibles Mejoras Futuras

- [ ] **Soporte multi-objetivo**: Escanear rangos de IPs (CIDR notation).
- [ ] **Exportación de reportes**: Generar informes en PDF o HTML.
- [ ] **Integración con CVE databases**: Cruzar servicios detectados con vulnerabilidades conocidas.
- [ ] **Modo verbose**: Mostrar el razonamiento paso a paso del agente.
- [ ] **Soporte para APIs externas**: OpenAI, Anthropic, Gemini como alternativa a Ollama.
- [ ] **Persistencia de sesión**: Guardar el historial de conversación entre sesiones.
- [ ] **Banner grabbing**: Detectar versiones de servicios además de puertos abiertos.
- [ ] **Sistema de plugins**: Agregar nuevas herramientas sin modificar el código base.
