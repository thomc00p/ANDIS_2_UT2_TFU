# Trabajo Final de Unidad 2 (UT2) - Tácticas de Arquitectura

Este proyecto implementa y valida experimentalmente la **Combinación de Tácticas 2** (Disponibilidad y Seguridad) para un sistema distribuido resiliente y defensivo, bajo los lineamientos del TFU de Arquitectura de Software.

---

## 1. Mapeo de Atributos de Calidad (QRs) y Tácticas

| Atributo de Calidad | Táctica Arquitectónica | Componente / Implementación | Métrica de Éxito |
| :--- | :--- | :--- | :--- |
| **Disponibilidad** (Tolerancia a fallas transitorias) | **Replicación** (*Mantener múltiples copias de cómputo*) | 3 instancias de la API (`web_replica_1`, `2`, `3`) orquestadas por NGINX Load Balancer con Round-Robin. | Alta disponibilidad y redundancia de cómputo. |
| **Disponibilidad** (Tolerancia a fallas transitorias) | **Re-intentos** (*Retry con espera*) | Cliente de carga (`client_test.py`) con 3 intentos ante desconexión o reconfiguración del balanceador. | **0% de error percibido** por el cliente final (100% de éxito en carga concurrente). |
| **Seguridad** (Resistencia a amenazas externas) | **Autenticar Actores** | Verificación estricta mediante Bearer Token en FastAPI (`HTTPBearer`, token `TFU-UT2-SECRET-KEY`). | Rechazo inmediato con **HTTP 401** ante solicitudes no autenticadas. |
| **Seguridad** (Resistencia a amenazas externas) | **Validar la Entrada** | Esquema estricto en Pydantic (`PayloadModel` con `item_id > 0` y `name >= 3 chars`). | Rechazo en el borde con **HTTP 422** ante datos malformados. |

---

## 2. Estructura del Proyecto

```
ut2-tacticas-arquitectura/
├── app/
│   ├── main.py              # API FastAPI con autenticación y validación de entrada
│   ├── requirements.txt     # Dependencias de Python (fastapi, uvicorn, pydantic)
│   └── Dockerfile           # Imagen Docker basada en python:3.12-slim
├── nginx.conf               # Configuración de NGINX como reverse proxy y balanceador
├── docker-compose.yml       # Orquestación de 3 réplicas API y balanceador NGINX
├── client_test.py           # Cliente con ThreadPoolExecutor y re-intentos
├── demo_script.sh           # Script bash para pruebas automatizadas (Linux / macOS / Git Bash)
├── demo_script.ps1          # Script PowerShell para pruebas automatizadas en Windows
└── README.md                # Este documento de referencia y guía de presentación
```

---

## 3. Instrucciones de Ejecución

### Prerrequisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y en ejecución.
- Python 3.9+ instalado en la máquina anfitriona (para correr el script de prueba del cliente).

### Paso 1: Levantar los Servicios
Desde la raíz del proyecto (`ut2-tacticas-arquitectura/`):
```bash
docker compose up -d --build
```
Esto creará e iniciará 4 contenedores:
- `web_replica_1`, `web_replica_2`, `web_replica_3` (escuchando internamente en el puerto 8000).
- `nginx_lb` (escuchando en el puerto `80` local).

Verificar estado:
```bash
docker compose ps
```

---

## 4. Pruebas y Validación Empírica

### A. Pruebas de Seguridad

1. **Acceso sin Token (Autenticar Actores):**
   ```bash
   curl -i -X POST http://localhost/process
   ```
   *Respuesta esperada:* `HTTP/1.1 401 Unauthorized` (`{"detail":"Not authenticated"}` o `{"detail":"Identidad no verificada"}`).

2. **Envío de Payload Malformado (Validar Entrada):**
   ```bash
   curl -i -X POST http://localhost/process \
     -H "Authorization: Bearer TFU-UT2-SECRET-KEY" \
     -H "Content-Type: application/json" \
     -d '{"item_id": -5, "name": "A"}'
   ```
   *Respuesta esperada:* `HTTP/1.1 422 Unprocessable Entity` (Pydantic rechaza los campos antes de entrar a la lógica de negocio).

3. **Solicitud Válida:**
   ```bash
   curl -i -X POST http://localhost/process \
     -H "Authorization: Bearer TFU-UT2-SECRET-KEY" \
     -H "Content-Type: application/json" \
     -d '{"item_id": 101, "name": "ResilienceTest"}'
   ```
   *Respuesta esperada:* `HTTP/1.1 200 OK` retornando el contenedor (`processed_by`) que procesó la solicitud.

---

### B. Prueba de Disponibilidad y Resiliencia en Vivo

Ejecutar la prueba de concurrencia y detención de nodo:

#### En Windows PowerShell:
```powershell
.\demo_script.ps1
```

#### En Bash / Git Bash / Linux:
```bash
chmod +x demo_script.sh
./demo_script.sh
```

#### Ejecución Manual del Test de Carga:
```bash
python client_test.py
```
*(Mientras corre, ejecuta en otra terminal `docker stop web_replica_1` para simular la caída del nodo).*
