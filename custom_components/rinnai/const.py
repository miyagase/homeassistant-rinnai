DOMAIN = "rinnai"

API_BASE = "https://rinnaiapp.rinnai.co.jp"
API_HEADERS = {
    "os-type": "Android",
    "app-version": "1.5.0",
    "app-type": "Rinnai",
    "user-agent": "okhttp/5.3.2",
    "Content-Type": "application/json",
}

CONF_CONTROLLER_ID = "controller_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"

UPDATE_INTERVAL_SECONDS = 60
TOKEN_REFRESH_THRESHOLD_HOURS = 2
