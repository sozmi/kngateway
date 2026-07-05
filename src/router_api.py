import requests
from requests.auth import HTTPDigestAuth
import logging

from .config import (
    ROUTER_IP, ROUTER_PORT, ROUTER_USE_HTTPS,
    ROUTER_USER, ROUTER_PASSWORD, ROUTER_INTERFACE
)

logger = logging.getLogger("KeeneticMQTT")

def keenetic_request(method, endpoint, data=None):
    """Отправляет запрос к API Keenetic с Digest-аутентификацией"""
    protocol = "https" if ROUTER_USE_HTTPS else "http"
    url = f"{protocol}://{ROUTER_IP}:{ROUTER_PORT}/rci/{endpoint}"
    auth = HTTPDigestAuth(ROUTER_USER, ROUTER_PASSWORD)
    headers = {"Content-Type": "application/json"}
    try:
        if method.upper() == "GET":
            response = requests.get(url, auth=auth, headers=headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, auth=auth, headers=headers, json=data, timeout=10)
        else:
            return None, "Unsupported method"
        if response.status_code in (200, 201, 204):
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return None, str(e)

def block_mac(mac):
    """Добавляет MAC в чёрный список"""
    data = {"address": mac}
    result, error = keenetic_request("POST", f"interface/{ROUTER_INTERFACE}/mac/access-list/address", data)
    if error:
        return False, error
    result, error = keenetic_request("POST", "system/configuration/save", {})
    if error:
        return False, f"Не удалось сохранить конфигурацию: {error}"
    return True, "MAC добавлен в чёрный список"

def unblock_mac(mac):
    """Удаляет MAC из чёрного списка"""
    data = {"no": True, "address": mac}
    result, error = keenetic_request("POST", f"interface/{ROUTER_INTERFACE}/mac/access-list/address", data)
    if error:
        return False, error
    result, error = keenetic_request("POST", "system/configuration/save", {})
    if error:
        return False, f"Не удалось сохранить конфигурацию: {error}"
    return True, "MAC удалён из чёрного списка"

def get_blacklist():
    """Получить текущий чёрный список (для диагностики)"""
    result, error = keenetic_request("GET", f"interface/{ROUTER_INTERFACE}")
    if error:
        return None, error
    mac_list = result.get("interface", {}).get("mac-access-list", {}).get("address", [])
    return mac_list, None

def check_router_api():
    """Проверяет доступность API роутера"""
    protocol = "https" if ROUTER_USE_HTTPS else "http"
    url = f"{protocol}://{ROUTER_IP}:{ROUTER_PORT}/rci/interface/{ROUTER_INTERFACE}"
    auth = HTTPDigestAuth(ROUTER_USER, ROUTER_PASSWORD)
    try:
        response = requests.get(url, auth=auth, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "interface" in data:
                return True, "OK"
            else:
                return False, "Invalid response format"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, str(e)
