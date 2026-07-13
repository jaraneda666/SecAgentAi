#!/usr/bin/env python3
"""
secagent.py - Agente de reconocimiento con Ollama y Nmap.
- Instalación de motor Ollama a nivel OS y librerías Python.
- Herramienta unificada (Fat Tool) para evitar alucinaciones.
- Menú inteligente dinámico (Prioriza modelos locales instalados).
- Escaneo Nmap en modo consulta estricto (-sT -Pn).
"""

import sys
import subprocess
import os
import json
import shutil
import time

# =====================================================================
# BLOQUE 1: AUTO-INSTALACIÓN DE LIBRERÍAS (PYTHON)
# =====================================================================
def verificar_dependencias():
    req_file = "requirements.txt"
    try:
        import nmap
        import ollama
    except ImportError:
        print("[!] Faltan dependencias de Python. Iniciando instalación automática...")
        if not os.path.exists(req_file):
            print(f"[X] Error: No se encontró '{req_file}' en el directorio actual.")
            sys.exit(1)
        
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", req_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )
            print("[+] Dependencias instaladas correctamente.\n")
        except subprocess.CalledProcessError as e:
            print(f"[X] Falló la instalación de dependencias. Detalle: {e}")
            sys.exit(1)

verificar_dependencias()

import nmap
import ollama

# =====================================================================
# BLOQUE 2: VERIFICACIÓN E INSTALACIÓN DE OLLAMA (OS / SERVICIO)
# =====================================================================
def verificar_servicio_ollama():
    print("\n" + "="*50)
    print("   Verificación de Motor Ollama (OS)")
    print("="*50)
    
    # 1. Comprobar si el binario de Ollama existe en el sistema
    if shutil.which("ollama") is None:
        print("[!] Ollama no está instalado en el sistema.")
        print("[*] Iniciando instalación oficial de Linux (requiere curl). Te pedirá contraseña de sudo...")
        try:
            # Comando oficial de instalación para Linux
            subprocess.check_call("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
            print("\n[+] Ollama instalado correctamente en el sistema operativo.")
        except subprocess.CalledProcessError as e:
            print(f"\n[X] Falló la instalación de Ollama. Asegúrate de tener 'curl' instalado. Detalle: {e}")
            sys.exit(1)
    else:
        print("[+] Binario de Ollama detectado en el sistema.")

    # 2. Comprobar si el servicio está respondiendo
    try:
        # Ejecutar 'ollama list' silenciosamente. Si falla, el daemon está abajo.
        subprocess.check_output(["ollama", "list"], stderr=subprocess.STDOUT)
        print("[+] El servicio de Ollama ya se encuentra en ejecución.")
    except subprocess.CalledProcessError:
        print("[!] El servicio de Ollama está detenido. Intentando iniciarlo...")
        try:
            # Intentar iniciar vía systemd (común en Linux, pedirá sudo)
            subprocess.check_call(["sudo", "systemctl", "start", "ollama"])
            print("[+] Servicio de Ollama iniciado exitosamente mediante systemctl.")
        except subprocess.CalledProcessError:
            # Fallback: Lanzar 'ollama serve' en segundo plano si systemctl no está disponible
            print("[*] systemctl falló o no existe. Iniciando 'ollama serve' en segundo plano...")
            subprocess.Popen(
                ["ollama", "serve"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            # Damos 3 segundos al servicio para que levante y asigne los puertos
            time.sleep(3)
            print("[+] Motor de Ollama iniciado en segundo plano.")

verificar_servicio_ollama()

# =====================================================================
# BLOQUE 3: MENÚ INTELIGENTE Y GESTIÓN DEL MODELO LLM
# =====================================================================
MODELOS_RECOMENDADOS = [
    "hf.co/AlicanKiraz0/Titus-CybersecurityLLM-v1.0-Q4_K_M-No-MTP-GGUF:Q4_K_M",
    "iaprofesseur/SuperGemma4-26b-uncensored-Q4:latest",
    "llama3.1:latest",
    "qwen2.5-coder:7b",
    "qwen2.5:7b",
    "dolphin-llama3:latest",
    "command-r:latest",
    "gemma4:latest",
    "nemotron:latest"
]

def configurar_modelo() -> str:
    print("\n" + "="*50)
    print("   Configuración de Inteligencia Artificial")
    print("="*50)
    
    nombres_modelos_locales = []
    try:
        respuesta = ollama.list()
        
        if hasattr(respuesta, 'models'):
            lista_modelos = respuesta.models
        elif isinstance(respuesta, dict):
            lista_modelos = respuesta.get('models', [])
        else:
            lista_modelos = []

        for m in lista_modelos:
            if isinstance(m, dict):
                nombre = m.get('model', m.get('name'))
            else:
                nombre = getattr(m, 'model', getattr(m, 'name', None))
            if nombre:
                nombres_modelos_locales.append(nombre)
                
    except Exception as e:
        print(f"[X] Error al conectar con Ollama. Detalle: {e}")
        sys.exit(1)

    opciones_menu = []
    contador_opciones = 1

    if nombres_modelos_locales:
        print("\n[+] Modelos instalados en tu sistema (Listos para usar):")
        for modelo in nombres_modelos_locales:
            print(f"  {contador_opciones}. {modelo}")
            opciones_menu.append(modelo)
            contador_opciones += 1
    else:
        print("\n[!] No se encontraron modelos locales instalados.")

    modelos_para_descargar = [m for m in MODELOS_RECOMENDADOS if m not in nombres_modelos_locales]
    
    if modelos_para_descargar:
        print("\n[*] Modelos recomendados (Requieren descarga):")
        for modelo in modelos_para_descargar:
            print(f"  {contador_opciones}. {modelo}")
            opciones_menu.append(modelo)
            contador_opciones += 1

    opcion_manual = contador_opciones
    print(f"\n  {opcion_manual}. Otro (Ingresar nombre manualmente)")
    print("-" * 50)
    
    seleccion = input(f"Elige una opción (1-{opcion_manual}) [default: 1]: ").strip()
    
    if not seleccion:
        modelo_elegido = opciones_menu[0] if opciones_menu else MODELOS_RECOMENDADOS[0]
    elif seleccion.isdigit():
        opcion = int(seleccion)
        if 1 <= opcion <= len(opciones_menu):
            modelo_elegido = opciones_menu[opcion - 1]
        elif opcion == opcion_manual:
            modelo_elegido = input("Introduce el nombre exacto del modelo en Ollama: ").strip()
        else:
            print(f"[X] Opción inválida. Usando '{opciones_menu[0]}' por defecto.")
            modelo_elegido = opciones_menu[0]
    else:
        print(f"[X] Entrada inválida. Usando '{opciones_menu[0]}' por defecto.")
        modelo_elegido = opciones_menu[0]

    modelo_busqueda = modelo_elegido if ":" in modelo_elegido else f"{modelo_elegido}:latest"

    if modelo_busqueda not in nombres_modelos_locales and modelo_elegido not in nombres_modelos_locales:
        print(f"\n[*] El modelo '{modelo_elegido}' no está instalado.")
        print(f"[*] Iniciando 'ollama pull {modelo_elegido}' (esto puede tardar)...\n")
        try:
            subprocess.check_call(["ollama", "pull", modelo_elegido])
            print(f"\n[+] Modelo '{modelo_elegido}' descargado y listo para usar.")
        except subprocess.CalledProcessError:
            print(f"\n[X] Error al descargar '{modelo_elegido}'. Revisa tu conexión o el nombre del repositorio.")
            sys.exit(1)
        except FileNotFoundError:
            print("\n[X] El comando 'ollama' no se encuentra en el PATH del sistema.")
            sys.exit(1)
    else:
        print(f"\n[+] Modelo '{modelo_elegido}' cargado con éxito.")
        
    return modelo_elegido

MODEL = configurar_modelo()

# =====================================================================
# BLOQUE 4: LÓGICA UNIFICADA DE RECONOCIMIENTO ("FAT TOOL")
# =====================================================================
COMMON = {
    "web":    [80, 443, 8080, 8443],
    "remote": [22, 23, 3389, 5900],
    "db":     [3306, 5432, 1433, 27017, 6379],
    "mail":   [25, 110, 143, 465, 587, 993, 995],
    "top":    [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 8080],
}

def scan_target(ip: str, port_group: str = "top", custom_ports = None) -> dict:
    nm = nmap.PortScanner()
    
    if custom_ports:
        if isinstance(custom_ports, str):
            port_str = custom_ports.strip("[]'\" ")
        elif isinstance(custom_ports, list):
            port_str = ",".join(map(str, custom_ports))
        else:
            port_str = str(custom_ports)
    else:
        puertos_lista = COMMON.get(port_group, COMMON["top"])
        port_str = ",".join(map(str, puertos_lista))

    open_ports = []
    
    try:
        nm.scan(hosts=ip, ports=port_str, arguments='-Pn -sT -T4')
        if ip in nm.all_hosts():
            for proto in nm[ip].all_protocols():
                lport = nm[ip][proto].keys()
                for port in sorted(lport):
                    state = nm[ip][proto][port]['state']
                    if state == 'open':
                        svc = nm[ip][proto][port].get('name', 'unknown')
                        open_ports.append({"port": port, "service": svc})
    except nmap.PortScannerError as e:
        return {"error": f"Error de Nmap: {str(e)}"}
    except Exception as e:
        return {"error": f"Excepción inesperada: {str(e)}"}

    return {"ip": ip, "scanned_ports": port_str, "open": open_ports}

# =====================================================================
# BLOQUE 5: DEFINICIÓN DE HERRAMIENTAS Y ORQUESTACIÓN (PROMPT)
# =====================================================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scan_target",
            "description": "Escanea una IP para encontrar puertos abiertos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string", 
                        "description": "IP objetivo, ej. 192.168.1.1"
                    },
                    "port_group": {
                        "type": "string",
                        "enum": ["top", "web", "db", "remote", "mail"],
                        "description": "Usa 'top' por defecto. Usa 'web' para HTTP/S, 'db' para BBDD."
                    },
                    "custom_ports": {
                        "type": "string",
                        "description": "SOLO usar si el usuario pide puertos específicos. Ej: '80,443'."
                    }
                },
                "required": ["ip"]
            },
        },
    }
]

DISPATCH = {"scan_target": scan_target}

SYSTEM = (
    "Eres un experto en ciberseguridad defensiva y auditoría de infraestructuras. "
    "Tu tarea es analizar los objetivos solicitados utilizando la herramienta `scan_target`. "
    "Por defecto, confía en el parámetro 'port_group' y no uses 'custom_ports' a menos que te lo pidan. "
    "Resume los hallazgos en español y entrega recomendaciones de mitigación (hardening) concisas."
)

# =====================================================================
# BLOQUE 6: BUCLE PRINCIPAL DEL AGENTE
# =====================================================================
def run_agent(prompt: str):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]

    for _ in range(8):  
        resp = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp["message"]
        messages.append(msg)

        calls = msg.get("tool_calls")
        
        if not calls:
            print("\n=== RESULTADO ===\n" + (msg.get("content") or "").strip())
            return

        for call in calls:
            fn = call["function"]["name"]
            args = call["function"]["arguments"]
            
            if isinstance(args, str):
                args = json.loads(args)
            
            print(f"[*] Ejecutando reconocimiento en segundo plano...", end="\r")
            
            try:
                result = DISPATCH[fn](**args)
            except Exception as e:
                result = {"error": str(e)}
            
            messages.append({"role": "tool", "content": json.dumps(result)})

    print("\n[!] Límite de pasos alcanzado.")

# =====================================================================
# BLOQUE 7: PUNTO DE ENTRADA (MAIN)
# =====================================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_agent(" ".join(sys.argv[1:]))
    else:
        print(f"\nAgente listo (Modelo activo: {MODEL}). Ctrl+C para salir.")
        while True:
            try:
                run_agent(input("\n> "))
            except (KeyboardInterrupt, EOFError):
                print("\nAdiós.")
                break
