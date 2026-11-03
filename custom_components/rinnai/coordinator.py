from __future__ import annotations

import asyncio
import base64
import json
import logging
from datetime import datetime, timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE,
    API_HEADERS,
    CONF_ACCESS_TOKEN,
    CONF_CONTROLLER_ID,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    TOKEN_REFRESH_THRESHOLD_HOURS,
    UPDATE_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


class RinnaiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self._entry = entry
        self._access_token: str = entry.data[CONF_ACCESS_TOKEN]
        self._refresh_token: str = entry.data[CONF_REFRESH_TOKEN]
        self._controller_id: str = entry.data[CONF_CONTROLLER_ID]

    def _token_expires_within(self, hours: float) -> bool:
        try:
            payload_b64 = self._access_token.split(".")[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(base64.b64decode(payload_b64))
            remaining = payload["exp"] - datetime.now().timestamp()
            return remaining < hours * 3600
        except Exception:
            return True

    async def _refresh_access_token(self) -> bool:
        url = f"{API_BASE}/api/v2/users/refresh_token"
        headers = {**API_HEADERS, "Authorization": f"Bearer {self._access_token}"}
        body = {"refreshToken": self._refresh_token}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.error("Token refresh failed: %s %s", resp.status, text)
                    return False
                data = await resp.json()

        new_token = data.get("accessToken") or data.get("access_token") or data.get("token")
        new_refresh = data.get("refreshToken") or data.get("refresh_token")

        if not new_token:
            _LOGGER.error("No accessToken in refresh response: %s", data)
            return False

        self._access_token = new_token
        if new_refresh:
            self._refresh_token = new_refresh

        new_data = {**self._entry.data, CONF_ACCESS_TOKEN: self._access_token, CONF_REFRESH_TOKEN: self._refresh_token}
        self.hass.config_entries.async_update_entry(self._entry, data=new_data)
        _LOGGER.debug("Token refreshed successfully")
        return True

    async def _fetch_status(self) -> dict:
        url = f"{API_BASE}/api/v2/controllers/{self._controller_id}/kantakun"
        headers = {**API_HEADERS, "Authorization": f"Bearer {self._access_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 401:
                    return None
                resp.raise_for_status()
                return await resp.json()

    async def _async_update_data(self) -> dict:
        if self._token_expires_within(TOKEN_REFRESH_THRESHOLD_HOURS):
            _LOGGER.debug("Token expiring soon, refreshing...")
            await self._refresh_access_token()

        try:
            data = await self._fetch_status()
        except Exception as err:
            raise UpdateFailed(f"API error: {err}") from err

        if data is None:
            _LOGGER.warning("Got 401, attempting token refresh and retry")
            refreshed = await self._refresh_access_token()
            if not refreshed:
                raise UpdateFailed("Token refresh failed after 401")
            try:
                data = await self._fetch_status()
            except Exception as err:
                raise UpdateFailed(f"API error after token refresh: {err}") from err
            if data is None:
                raise UpdateFailed("401 persists after token refresh")

        return data
