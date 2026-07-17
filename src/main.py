#!/usr/bin/env python3
import logging
import sys
import threading
import paho.mqtt.client as mqtt


from .config import (
    MQTT_BROKER, MQTT_PORT, MQTT_USE_TLS,
    MQTT_USER, MQTT_PASSWORD, LOG_LEVEL, HEALTH_SERVER_PORT
)
from .mqtt_handler import on_connect, on_disconnect, on_message, publish_health
from .health_server import start_health_server

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("KeeneticMQTT")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    if MQTT_USE_TLS:
        client.tls_set()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        logger.error(f"Не удалось подключиться к MQTT: {e}")
        sys.exit(1)

    # Запускаем HTTP-сервер для healthcheck
    health_thread = threading.Thread(
        target=start_health_server,
        args=(client, HEALTH_SERVER_PORT),
        daemon=True
    )
    health_thread.start()

    # Запускаем периодический healthcheck в MQTT
    health_mqtt_thread = threading.Thread(
        target=publish_health,
        args=(client,),
        daemon=True
    )
    health_mqtt_thread.start()

    client.loop_forever()

if __name__ == "__main__":
    main()