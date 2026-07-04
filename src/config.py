import os

# Keenetic API
ROUTER_IP = os.getenv("ROUTER_IP", "192.168.1.1")
ROUTER_PORT = int(os.getenv("ROUTER_PORT", 80))
ROUTER_USE_HTTPS = os.getenv("ROUTER_USE_HTTPS", "false").lower() == "true"
ROUTER_USER = os.getenv("ROUTER_USER", "admin")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD", "")
ROUTER_INTERFACE = os.getenv("ROUTER_INTERFACE", "")

# MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.1.140")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC_COMMAND = os.getenv("MQTT_TOPIC_COMMAND", "keenetic-gateway/command")
MQTT_TOPIC_RESPONSE = os.getenv("MQTT_TOPIC_RESPONSE", "keenetic-gateway/response")
MQTT_TOPIC_HEALTH = os.getenv("MQTT_TOPIC_HEALTH", "keenetic-gateway/health")

SECRET_KEY = os.getenv("SECRET_KEY", None)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
HEALTH_INTERVAL = int(os.getenv("HEALTH_INTERVAL", 60))
HEALTH_SERVER_PORT = int(os.getenv("HEALTH_SERVER_PORT", 8080))