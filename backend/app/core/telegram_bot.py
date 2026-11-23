import os
import json
import logging
import asyncio
from typing import Optional
import aiohttp
from datetime import datetime

logger = logging.getLogger("nextlevelcheat.telegram_bot")


class TelegramSecurityBot:
    def __init__(self):
        self.bot_token: Optional[str] = None
        self.owner_chat_id: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def init_credentials(self, token: str, chat_id: str):
        self.bot_token = token.strip() if token else None
        self.owner_chat_id = chat_id.strip() if chat_id else None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        return self._session

    async def send_security_alert(self, title: str, details: str, severity: str = "HIGH", ip_address: str = "Unknown"):
        """
        Sends clear-text instant security alerts for DDoS, Brute Force, Admin Logins, and Attacks.
        """
        if not self.bot_token or not self.owner_chat_id:
            return False

        icon = "🚨" if severity in ("HIGH", "CRITICAL") else "⚠️"
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        message = (
            f"{icon} <b>SECURITY ALERT: {title.upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>Severity:</b> {severity}\n"
            f"<b>Time:</b> <code>{timestamp}</code>\n"
            f"<b>Origin IP:</b> <code>{ip_address}</code>\n\n"
            f"<b>Details:</b>\n{details}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ <i>बी - TOOL Anti-Intrusion Shield</i>"
        )

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.owner_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            session = await self.get_session()
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    logger.error(f"Telegram alert failed: {data.get('description')}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Error sending Telegram security alert: {e}")
            return False

    async def send_database_backup(self, file_path: str, caption: str = "📦 Automated Weekly Database Backup"):
        """
        Exports and sends actual SQLite / SQL dump file directly to Owner Chat ID.
        """
        if not self.bot_token or not self.owner_chat_id:
            return False, "Bot token or owner chat ID not configured"

        if not os.path.exists(file_path):
            logger.error(f"Backup file not found at: {file_path}")
            return False, "Backup file not found on disk"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        try:
            session = await self.get_session()
            with open(file_path, "rb") as doc_file:
                data = aiohttp.FormData()
                data.add_field("chat_id", self.owner_chat_id)
                data.add_field("caption", caption)
                data.add_field("parse_mode", "HTML")
                data.add_field("document", doc_file.read(), filename=os.path.basename(file_path))

                async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    result = await resp.json()
                    if not result.get("ok"):
                        err_desc = result.get("description", "Unknown Telegram error")
                        logger.error(f"Failed to send database backup to Telegram: {err_desc}")
                        return False, err_desc
                    return True, "Delivered successfully"
        except Exception as e:
            logger.error(f"Failed to send database backup to Telegram: {e}")
            return False, str(e)


telegram_security_bot = TelegramSecurityBot()
