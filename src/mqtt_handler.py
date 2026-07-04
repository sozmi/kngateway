import json
import logging
import time
import threading
import paho.mqtt.client as mqtt

from .config import (
    MQTT_BROKER, MQTT_PORT, MQTT_USE_TLS,
    MQTT_USER, MQTT_PASSWORD,
    MQTT_TOPIC_COMMAND, MQTT_TOPIC_RESPONSE,
    MQTT_TOPIC_HEALTH, SECRET_KEY, HEALTH_INTERVAL
)
from .router_api import block_mac, unblock_mac, get_blacklist, check_router_api, keenetic_request

logger = logging.getLogger("KeeneticMQTT")

def check_mqtt_connection(client):
    """Проверяет, что MQTT-клиент подключён и может публиковать сообщения"""
    if not client.is_connected():
        return False, "MQTT client not connected"
    try:
        result = client.publish(MQTT_TOPIC_HEALTH, json.dumps({"status": "ping"}), qos=0, retain=False)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return True, "OK"
        return False, f"Publish failed with code {result.rc}"
    except Exception as e:
        return False, str(e)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Подключено к MQTT брокеру")
        client.subscribe(MQTT_TOPIC_COMMAND)
        logger.info(f"Подписались на топик {MQTT_TOPIC_COMMAND}")
    else:
        logger.error(f"Ошибка подключения к MQTT, код {rc}")

def on_disconnect(client, userdata, rc):
    logger.warning("Отключено от MQTT брокера")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"Получена команда: {payload}")
    except Exception as e:
        logger.error(f"Не удалось распарсить JSON: {e}")
        client.publish(MQTT_TOPIC_RESPONSE, json.dumps({"status": "error", "message": "Invalid JSON"}))
        return

    if SECRET_KEY and payload.get("key") != SECRET_KEY:
        logger.warning("Неверный секретный ключ, команда игнорирована")
        client.publish(MQTT_TOPIC_RESPONSE, json.dumps({"status": "error", "message": "Invalid secret key"}))
        return

    mac = payload.get("mac")
    action = payload.get("action")

    if not mac or not action:
        logger.warning("Отсутствует mac или action")
        client.publish(MQTT_TOPIC_RESPONSE, json.dumps({"status": "error", "message": "Missing mac or action"}))
        return

    mac = mac.strip().upper().replace("-", ":")
    if len(mac) != 17 or sum(1 for c in mac if c == ':') != 5:
        logger.warning(f"Некорректный MAC: {mac}")
        client.publish(MQTT_TOPIC_RESPONSE, json.dumps({"status": "error", "message": "Invalid MAC format"}))
        return

    if action == "block":
        success, message = block_mac(mac)
    elif action == "unblock":
        success, message = unblock_mac(mac)
    elif action == "list":
        mac_list, error = get_blacklist()
        if error:
            success, message = False, error
        else:
            success, message = True, {"blacklist": mac_list}
    elif action == "ping":
        client.publish(MQTT_TOPIC_RESPONSE, json.dumps({"status": "pong"}))
        return
    else:
        logger.warning(f"Неизвестное действие: {action}")
        client.publish(MQTT_TOPIC_RESPONSE, json.dumps({"status": "error", "message": "Unknown action"}))
        return

    response = {
        "mac": mac,
        "action": action,
        "status": "success" if success else "error",
        "message": message
    }
    client.publish(MQTT_TOPIC_RESPONSE, json.dumps(response))
    logger.info(f"Ответ отправлен: {response}")

def publish_health(client):
    """Периодически проверяет состояние и публикует статус"""
    while True:
        time.sleep(HEALTH_INTERVAL)

        mqtt_ok, mqtt_msg = check_mqtt_connection(client)
        router_ok, router_msg = check_router_api()

        errors = []
        if not mqtt_ok:
            errors.append(f"MQTT: {mqtt_msg}")
        if not router_ok:
            errors.append(f"Router: {router_msg}")

        status = {
            "timestamp": int(time.time()),
            "components": {
                "mqtt": "ok" if mqtt_ok else "error",
                "router": "ok" if router_ok else "error"
            }
        }

        if errors:
            status["status"] = "error"
            status["message"] = ", ".join(errors)
            logger.warning(f"Healthcheck error: {status['message']}")
        else:
            status["status"] = "ok"
            logger.debug("Healthcheck: всё работает")

        try:
            client.publish(MQTT_TOPIC_HEALTH, json.dumps(status), retain=True, qos=1)
        except Exception as e:
            logger.error(f"Ошибка публикации healthcheck: {e}")