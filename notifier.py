import os
import json
import urllib.request
import logging

# Simple env loader to avoid external dependencies
def load_env(env_path=".env"):
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
        except Exception as e:
            print(f"Erro ao carregar o arquivo .env: {e}")

class Notifier:
    def __init__(self):
        load_env()
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Setup logging config
        logger = logging.getLogger()
        if not logger.handlers:
            logging.basicConfig(
                filename="dados_aberto_cpnj.log",
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s"
            )

    def log_and_notify(self, message, level=logging.INFO):
        # Print to console
        print(message)
        
        # Log to file
        if level == logging.INFO:
            logging.info(message)
        elif level == logging.WARNING:
            logging.warning(message)
        elif level == logging.ERROR:
            logging.error(message)

        # Send Telegram alert if configured
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(message)

        # Send Discord alert if configured
        if self.discord_webhook:
            self._send_discord(message)

    def _send_discord(self, message):
        data = {"content": message}
        req = urllib.request.Request(
            self.discord_webhook,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Notifier-Agent"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                pass
        except Exception as e:
            logging.error(f"Erro ao enviar alerta para Discord: {e}")

    def _send_telegram(self, message):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {"chat_id": self.telegram_chat_id, "text": message}
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Notifier-Agent"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                pass
        except Exception as e:
            logging.error(f"Erro ao enviar alerta para Telegram: {e}")
