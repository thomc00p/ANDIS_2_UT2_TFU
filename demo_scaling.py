"""Escalado manual de una a tres APIs, con datos y token conservados.
Requiere las imágenes construidas (docker compose build).
No elimina contenedores de base ni volúmenes. Restaura tres APIs al salir.
"""
from collections import Counter
from decimal import Decimal
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("BASE_URL", "http://localhost:" + os.environ.get("PORT", "8080"))
sys.path.insert(0, str(ROOT / "tests"))
from test_api import api, operation, ADMIN

DOCKER = shutil.which("docker") or str(Path.home() / ".docker/bin/docker")


def compose(*args, single=False, capture=False):
    env = os.environ.copy()
    env["NGINX_CONF"] = str(ROOT / ("nginx.single.conf" if single else "nginx.conf"))
    return subprocess.run([DOCKER, "compose", *args], cwd=ROOT, env=env,
                          check=True, text=True, capture_output=capture).stdout


def request(method, path, body=None, token=ADMIN):
    code, data, replica = api(method, path, body, token)
    if code not in (200, 201):
        raise RuntimeError(f"{method} {path}: HTTP {code}: {data}")
    return data, replica


def verify_running(expected):
    services = set(compose("ps", "--services", "--status", "running", capture=True).split())
    apis = {service for service in services if service.startswith("web_replica_")}
    if apis != set(expected):
        raise AssertionError(f"APIs activas inesperadas: {apis}")
    print("APIs en ejecución:", ", ".join(sorted(apis)), flush=True)


def sample(path, token, expected, phase):
    counts = Counter()
    for _ in range(30):
        card, replica = request("GET", path, token=token)
        if Decimal(str(card["balance"])) != Decimal("75.00") or not replica:
            raise AssertionError("Saldo incorrecto o réplica no identificada")
        counts[replica] += 1
    if len(counts) != expected:
        raise AssertionError(f"Se esperaban {expected} réplicas, respondieron {dict(counts)}")
    print(f"{phase}: 30/30 lecturas correctas, saldo 75.00, mismo token.", flush=True)
    for replica, count in sorted(counts.items()):
        print(f"  Réplica {replica}: {count} solicitudes", flush=True)
    return set(counts)


def main():
    try:
        print("FASE 1 — Una sola réplica. Preparación con breve interrupción del proxy.", flush=True)
        compose("stop", "lb", "web_replica_2", "web_replica_3")
        compose("up", "-d", "--wait", "web_replica_1")
        # --no-deps evita que las dependencias normales del proxy arranquen las tres APIs.
        compose("up", "-d", "--no-deps", "lb", single=True)
        # El proceso del proxy puede tardar un instante en aceptar conexiones.
        from demo_resilience import wait_ready
        wait_ready()
        verify_running(["web_replica_1"])
        email = str(uuid.uuid4()) + "@scaling.test"
        user, _ = request("POST", "/users/", {"name": "Demo escalado", "email": email, "password": "Demo-12345"}, None)
        login, _ = request("POST", "/users/login", {"email": email, "password": "Demo-12345"}, None)
        token = login["access_token"]
        card, _ = request("POST", "/cards/", {"user_id": user["id"]}, token)
        path = f'/cards/{card["id"]}'
        recharge = operation(amount="75.00")
        request("PATCH", path + "/recharge", recharge)
        original = sample(path, token, 1, "Antes de escalar")

        print("FASE 2 — Incorporar dos réplicas y configurar el balanceador para tres.", flush=True)
        compose("up", "-d", "--wait", "web_replica_2", "web_replica_3")
        # Compose detecta el cambio del archivo montado y recrea solamente el proxy.
        compose("up", "-d", "--no-deps", "lb")
        wait_ready()
        verify_running(["web_replica_1", "web_replica_2", "web_replica_3"])
        expanded = sample(path, token, 3, "Después de escalar")
        if not original.issubset(expanded):
            raise AssertionError("La réplica original no participó después del escalado")
        request("PATCH", path + "/recharge", recharge)
        history, _ = request("GET", path + "/history", token=token)
        current, _ = request("GET", path, token=token)
        if len(history["history"]) != 1 or Decimal(str(current["balance"])) != 75:
            raise AssertionError("La recarga se duplicó después de escalar")
        print(f'OK: escalado 1 → 3, tarjeta {card["id"]}, token y saldo conservados; recarga sin duplicados.', flush=True)
    finally:
        print("Restaurando la configuración normal de tres réplicas...", flush=True)
        compose("up", "-d", "--wait")


if __name__ == "__main__":
    main()
