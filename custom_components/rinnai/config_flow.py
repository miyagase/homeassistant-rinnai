from __future__ import annotations

import asyncio
import logging
import socket
import ssl as _ssl

import aiohttp
import voluptuous as vol
from homeassistant import config_entries

from .const import API_BASE, API_HEADERS, CONF_ACCESS_TOKEN, CONF_CONTROLLER_ID, CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

UDP_PORT = 64471
UDP_DISCOVER_PAYLOAD = bytes([0xAA, 0x00])
UDP_TIMEOUT = 60.0


async def _udp_broadcast_and_discover() -> str | None:
    """UDPブロードキャストを送信してデバイスIPを自動検出する。
    デバイスはOKボタンが押されると0x41を返す。
    """
    loop = asyncio.get_event_loop()

    def _blocking_discover():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(UDP_TIMEOUT)
        try:
            _LOGGER.info("[Rinnai] UDP broadcast → 255.255.255.255:%d payload=%s", UDP_PORT, UDP_DISCOVER_PAYLOAD.hex())
            sock.sendto(UDP_DISCOVER_PAYLOAD, ("255.255.255.255", UDP_PORT))
            response, addr = sock.recvfrom(16)
            _LOGGER.info("[Rinnai] UDP response: %s from %s", response.hex(), addr[0])
            if len(response) >= 2 and response[1] in (0x41, 0x42):
                _LOGGER.info("[Rinnai] Device found at %s (response[1]=0x%02x)", addr[0], response[1])
                return addr[0]
            _LOGGER.warning("[Rinnai] Unexpected UDP response: %s from %s", response.hex(), addr[0])
        except socket.timeout:
            _LOGGER.warning("[Rinnai] UDP discovery timed out after %s seconds", UDP_TIMEOUT)
            return None
        except Exception as err:
            _LOGGER.exception("[Rinnai] UDP discovery error: %s", err)
            return None
        finally:
            sock.close()
        return None

    return await loop.run_in_executor(None, _blocking_discover)



def _raw_post_app_auth(device_ip: str) -> dict | None:
    """生ソケットでPOSTし、非標準HTTPレスポンスを自前パース。
    デバイスはclientid/app-keyをurllib3が解析できない形式で返すため。
    """
    ssl_ctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = _ssl.CERT_NONE

    request = (
        "POST /app_auth2/app_auth.html HTTP/1.0\r\n"
        f"Host: {device_ip}\r\n"
        "app-key: FFFF\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )

    with socket.create_connection((device_ip, 443), timeout=3) as raw_sock:
        with ssl_ctx.wrap_socket(raw_sock) as s:
            s.sendall(request.encode())
            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)

    raw = b"".join(chunks).decode("utf-8", errors="replace")

    auth_code = None
    mqtt_code = None
    for line in raw.splitlines():
        low = line.lower().strip()
        if low.startswith("clientid"):
            val = line.split(":", 1)[-1].strip()
            # APIにはコロン区切りの最後の部分のみ渡す (例: d:rinnai:RJ:01:RJ:XXXXX → XXXXX)
            auth_code = val.split(":")[-1] if ":" in val else val
        elif low.startswith("app-key") and "ffff" not in low:
            val = line.split(":", 1)[-1].strip()
            mqtt_code = val

    if auth_code and mqtt_code:
        _LOGGER.debug("[Rinnai] app_auth credentials received")
        return {"auth_code": auth_code, "mqtt_code": mqtt_code}
    return None


async def _fetch_app_auth(device_ip: str, max_wait: int = 60) -> dict | None:
    """POST /app_auth2/app_auth.html → authCode と mqttCode を取得。"""
    loop = asyncio.get_event_loop()
    start = loop.time()

    while loop.time() - start <= max_wait:
        elapsed = int(loop.time() - start)
        _LOGGER.warning("[Rinnai] POST https://%s/app_auth2/app_auth.html (elapsed=%ds)", device_ip, elapsed)
        try:
            result = await loop.run_in_executor(None, _raw_post_app_auth, device_ip)
            if result:
                return result
        except Exception as err:
            _LOGGER.warning("[Rinnai] app_auth attempt failed: %s", type(err).__name__)

        await asyncio.sleep(1)

    _LOGGER.warning("[Rinnai] app_auth timed out after %ds", max_wait)
    return None


async def _create_guest_user(auth_code: str) -> dict | None:
    url = f"{API_BASE}/api/v2/users/create_guest_user"
    _LOGGER.info("[Rinnai] POST %s", url)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"code": auth_code}, headers=API_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            _LOGGER.info("[Rinnai] create_guest_user status: %s", resp.status)
            if resp.status != 200:
                _LOGGER.error("[Rinnai] create_guest_user failed: %s %s", resp.status, await resp.text())
                return None
            return await resp.json()


async def _register_controller(auth_code: str, mqtt_code: str, access_token: str) -> dict | None:
    url = f"{API_BASE}/api/v2/controllers/register"
    _LOGGER.info("[Rinnai] POST %s", url)
    headers = {**API_HEADERS, "Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"code": auth_code, "mqttCode": mqtt_code, "isMonitoring": True}, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            _LOGGER.info("[Rinnai] register_controller status: %s", resp.status)
            if resp.status != 200:
                _LOGGER.error("[Rinnai] register_controller failed: %s %s", resp.status, await resp.text())
                return None
            data = await resp.json()
            _LOGGER.info("[Rinnai] controllerId: %s", data.get("controllerId"))
            return data


class RinnaiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            _LOGGER.info("[Rinnai] Starting UDP discovery")
            device_ip = await _udp_broadcast_and_discover()
            if not device_ip:
                errors["base"] = "pairing_timeout"
                return self.async_show_form(step_id="user", data_schema=_schema(), errors=errors)

            _LOGGER.info("[Rinnai] Pairing with device at %s", device_ip)
            try:
                auth_info = await _fetch_app_auth(device_ip)
                if not auth_info:
                    errors["base"] = "auth_failed"
                    return self.async_show_form(step_id="user", data_schema=_schema(), errors=errors)

                user_data = await _create_guest_user(auth_info["auth_code"])
                if not user_data:
                    errors["base"] = "cannot_connect"
                    return self.async_show_form(step_id="user", data_schema=_schema(), errors=errors)

                ctrl_data = await _register_controller(auth_info["auth_code"], auth_info["mqtt_code"], user_data["accessToken"])
                if not ctrl_data:
                    errors["base"] = "cannot_connect"
                    return self.async_show_form(step_id="user", data_schema=_schema(), errors=errors)

            except Exception as err:
                _LOGGER.exception("[Rinnai] Pairing error: %s", err)
                errors["base"] = "unknown"
                return self.async_show_form(step_id="user", data_schema=_schema(), errors=errors)

            await self.async_set_unique_id(ctrl_data["controllerId"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="乾太くん",
                data={
                    CONF_CONTROLLER_ID: ctrl_data["controllerId"],
                    CONF_ACCESS_TOKEN: user_data["accessToken"],
                    CONF_REFRESH_TOKEN: user_data["refreshToken"],
                },
            )

        return self.async_show_form(step_id="user", data_schema=_schema(), errors=errors)


def _schema():
    return vol.Schema({})
