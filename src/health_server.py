import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

from .router_api import check_router_api
from .mqtt_handler import check_mqtt_connection

logger = logging.getLogger("KeeneticMQTT")

class HealthHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов для healthcheck"""

    client = None  # будет установлен из main

    def log_message(self, format, *args):
        pass  # отключаем логирование http-сервера

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Проверяем состояние
            mqtt_ok, mqtt_msg = check_mqtt_connection(self.client)
            router_ok, router_msg = check_router_api()

            errors = []
            if not mqtt_ok:
                errors.append(f"MQTT: {mqtt_msg}")
            if not router_ok:
                errors.append(f"Router: {router_msg}")

            status = {
                "status": "ok" if not errors else "error",
                "timestamp": int(time.time()),
                "components": {
                    "mqtt": "ok" if mqtt_ok else "error",
                    "router": "ok" if router_ok else "error"
                }
            }
            if errors:
                status["message"] = ", ".join(errors)

            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server(client, port=8080):
    """Запускает HTTP-сервер для healthcheck в отдельном потоке"""
    HealthHandler.client = client
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Healthcheck HTTP сервер запущен на порту {port}")
    server.serve_forever()