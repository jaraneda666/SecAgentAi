# 🔐 SecAgent — Agente de Reconocimiento con IA y Nmap

> Agente autónomo de reconocimiento de redes impulsado por modelos de lenguaje locales (Ollama) y Nmap, diseñado para auditorías de infraestructura en entornos controlados.

---

## 📋 Descripción

**SecAgent** es una herramienta de ciberseguridad que combina el poder de los **Modelos de Lenguaje Grande (LLM)** ejecutados localmente mediante [Ollama](https://ollama.com) con el motor de escaneo de puertos **Nmap**. El agente recibe instrucciones en lenguaje natural, decide de forma autónoma qué herramienta usar y cómo interpretar los resultados, entregando un análisis de hallazgos y recomendaciones de hardening en español.

Este proyecto fue desarrollado como tarea de la **Sesión 8** del curso *Hacking con IA* de **8dot8**.

---

## ✨ Características principales

- 🤖 **Agente IA autónomo** — Usa LLMs locales a través de Ollama para razonar y decidir qué escaneos ejecutar.
- 🔍 **Escaneo inteligente con Nmap** — Implementa una *Fat Tool* unificada (`scan_target`) que evita alucinaciones del modelo.
- 🧠 **Menú dinámico de modelos** — Detecta automáticamente los modelos instalados en el sistema y prioriza su uso.
- 📦 **Auto-instalación de dependencias** — Instala automáticamente las librerías Python requeridas si no están presentes.
- 🔧 **Auto-inicio de Ollama** — Verifica e inicia el servicio Ollama automáticamente (vía `systemctl` o `ollama serve`).
- 🌐 **Soporte para múltiples grupos de puertos** — `top`, `web`, `db`, `remote`, `mail` y puertos personalizados.
- 🗣️ **Interacción en lenguaje natural** — Se puede usar como CLI con argumentos o en modo interactivo.

---

## 🛠️ Requisitos previos

| Requisito | Versión mínima | Descripción |
|-----------|---------------|-------------|
| Python | 3.8+ | Lenguaje de ejecución |
| Nmap | Cualquiera | Motor de escaneo (debe estar instalado en el SO) |
| Ollama | Cualquiera | Motor LLM local (el script lo instala si no está) |
| curl | Cualquiera | Necesario para la instalación automática de Ollama en Linux |

---

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/secagent.git
cd secagent
```

### 2. Instalar dependencias Python

Las dependencias se instalan **automáticamente** al ejecutar el script. Si prefieres hacerlo manualmente:

```bash
pip install -r requirements.txt
```

### 3. Instalar Nmap (si no está instalado)

```bash
# Ubuntu / Debian
sudo apt-get install nmap

# macOS
brew install nmap

# Windows: https://nmap.org/download.html
```

### 4. Instalar Ollama (si no está instalado)

```bash
# Linux (instalación oficial)
curl -fsSL https://ollama.com/install.sh | sh

# macOS / Windows: https://ollama.com/download
```

---

## 🚀 Uso

### Modo interactivo

```bash
python secagent.py
```

Al iniciar, el agente:
1. Verifica e instala dependencias de Python.
2. Verifica e inicia el servicio de Ollama.
3. Muestra un menú de modelos disponibles para elegir.
4. Entra en modo de chat interactivo.

### Modo de línea de comandos (CLI)

```bash
python secagent.py "Escanea 192.168.1.1 y dime qué servicios tiene expuestos"
```

### Ejemplos de consultas

```
> Escanea 10.0.0.5 en los puertos más comunes
> Analiza 192.168.1.100 buscando servicios web
> Escanea 172.16.0.1 en puertos de base de datos
> Revisa el host 10.10.10.10 en los puertos 22 y 8080
```

---

## 📁 Estructura del proyecto

```
Tarea/
├── secagent.py         # Script principal del agente
├── requirements.txt    # Dependencias Python
├── README.md           # Este archivo
└── implementacion.md   # Documento técnico de implementación
```

---

## 🔌 Grupos de puertos soportados

| Grupo | Puertos |
|-------|---------|
| `top` | 21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 8080 |
| `web` | 80, 443, 8080, 8443 |
| `remote` | 22, 23, 3389, 5900 |
| `db` | 3306, 5432, 1433, 27017, 6379 |
| `mail` | 25, 110, 143, 465, 587, 993, 995 |
| `custom` | Cualquier puerto especificado por el usuario |

---

## 🤖 Modelos LLM recomendados

El agente soporta cualquier modelo compatible con Ollama. Los recomendados para ciberseguridad son:

- `Titus-CybersecurityLLM-v1.0-Q4_K_M` — Especializado en ciberseguridad
- `llama3.1:latest` — Propósito general, excelente razonamiento
- `qwen2.5-coder:7b` — Orientado a código y análisis técnico
- `qwen2.5:7b` — Equilibrio rendimiento/tamaño
- `dolphin-llama3:latest` — Sin restricciones, ideal para pentest

---

## ⚠️ Aviso Legal

> **Este software es solo para uso educativo y en entornos de prueba autorizados.**
> El escaneo de redes sin autorización explícita del propietario es **ilegal** en la mayoría de jurisdicciones.
> El autor no se responsabiliza del uso indebido de esta herramienta.

---

## 📄 Dependencias

```
python-nmap>=0.7.1
ollama>=0.2.0
```

---

## 👤 Autor

Desarrollado como parte del programa de formación **Hacking con IA — 8dot8**
Sesión 8 — Tarea práctica

---

## 📜 Licencia

MIT License — Libre para uso educativo y personal.
