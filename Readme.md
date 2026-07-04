# Keenetic MQTT Gateway

Шлюз для управления MAC-адресами на роутере Keenetic через MQTT.  
Позволяет удалённо блокировать и разблокировать Wi-Fi клиентов, что удобно для автоматического «переподключения» зависших камер.

## 🚀 Быстрый старт

1. Клонируйте репозиторий
   ```bash
   git clone https://github.com/sozmi/kngateway.git
   cd kngateway
  
2. Создайте файл .env из шаблона
   ```bash
   cp .env.example .env
   nano .env   # заполните своими данными

3. Запустите контейнер
   ```bash
   docker compose up -d

## Переменные окружения (.env)
| Переменная | Описание | Пример |
|------------|----------|--------|
| `ROUTER_IP` | IP-адрес роутера Keenetic | `192.168.1.1` |
| `ROUTER_PORT` | Порт для HTTP API (обычно 80) | `80` |
| `ROUTER_USE_HTTPS` | Использовать HTTPS? | `false` |
| `ROUTER_USER` | Пользователь роутера с правами на API | `admin` |
| `ROUTER_PASSWORD` | Пароль пользователя | `your_password` |
| `ROUTER_INTERFACE` | Интерфейс (сегмент) для управления MAC | `Bridge2` |
| `MQTT_BROKER` | IP-адрес MQTT-брокера | `192.168.1.140` |
| `MQTT_PORT` | Порт MQTT | `1883` |
| `MQTT_USE_TLS` | Использовать TLS для MQTT? | `false` |
| `MQTT_USER` | Пользователь MQTT (если требуется) | `gateway` |
| `MQTT_PASSWORD` | Пароль MQTT | `mqtt_pass` |
| `MQTT_TOPIC_COMMAND` | Топик для команд | `keenetic-gateway/command` |
| `MQTT_TOPIC_RESPONSE` | Топик для ответов | `keenetic-gateway/response` |
| `MQTT_TOPIC_HEALTH` | Топик для статуса (опционально) | `keenetic-gateway/health` |
| `SECRET_KEY` | Секретный ключ для защиты команд | `your_strong_secret` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `HEALTH_INTERVAL` | Интервал проверок (сек) | `60` |
| `HEALTH_SERVER_PORT` | Порт HTTP-сервера для healthcheck | `8080` |

Важно: Убедитесь, что пользователь на роутере имеет теги manager и http-proxy для доступа к API.

## 🧪Healthcheck
Шлюз предоставляет HTTP-эндпоинт для проверки состояния:

text
http://localhost:8080/health
Возвращает JSON со статусом ok или error, а также информацией о компонентах (mqtt, router).

json
{
  "status": "ok",
  "timestamp": 1719323456,
  "components": {
    "mqtt": "ok",
    "router": "ok"
  }
}
Docker-контейнер использует этот эндпоинт для healthcheck (интервал 30 секунд, 3 попытки).

## 🤖 Использование в Home Assistant
```yaml
reboot_camera:
  alias: "Переподключить камеру по MAC"
  mode: single
  fields:
    mac:
      description: "MAC-адрес камеры (формат XX:XX:XX:XX:XX:XX)"
      example: "0c:ef:15:26:19:dc"
      required: true
  sequence:
    - action: mqtt.publish
      data:
        topic: keenetic-gateway/command
        payload: >
          {"mac": "{{ mac }}", "action": "block", "key": "keenetic_secret_key"}
    - delay:
        seconds: 10
    - action: mqtt.publish
      data:
        topic: keenetic-gateway/command
        payload: >
          {"mac": "{{ mac }}", "action": "unblock", "key": "keenetic_secret_key"}

```yaml
alias: "Переподключить камеру при потере FPS"
trigger:
  - platform: state
    entity_id: sensor.kit_cam1_camera_fps
    to: "0"
    for:
      minutes: 2
action:
  - service: script.reboot_camera
    data:
      mac: "0c:ef:15:26:19:dc"
mode: single
