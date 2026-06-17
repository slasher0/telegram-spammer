import os
import asyncio
from telethon.sessions import StringSession
from telegram_session_encoder import TelegramSessionEncoder

class AccountImporter:
    DEFAULT_API_ID = 14369082
    DEFAULT_API_HASH = "b221b4f79223104634a800ecd4a9c3e5"

    @staticmethod
    async def import_from_raw_key_async(name, auth_key_hex, dc_id, sessions_dir="sessions"):
        try:
            if not os.path.exists(sessions_dir): 
                os.makedirs(sessions_dir)

            auth_key = bytes.fromhex(auth_key_hex)
            encoder = TelegramSessionEncoder(auth_key, dc_id)
            string_session_str = encoder.to_string()

            string_path = os.path.join(sessions_dir, f"{name}.string")
            with open(string_path, "w", encoding="utf-8") as f:
                f.write(string_session_str)

            return True, f"Success: {name} saved as StringSession."
        except Exception as e:
            return False, f"Import Error: {str(e)}"

    @staticmethod
    def import_from_json(json_path, sessions_dir="sessions"):
        try:
            import json, shutil
            base_name = os.path.basename(json_path).replace(".json", "")
            src_session = json_path.replace(".json", ".session")
            if os.path.exists(src_session):
                if not os.path.exists(sessions_dir): os.makedirs(sessions_dir)
                shutil.copy2(src_session, os.path.join(sessions_dir, f"{base_name}.session"))
                return True, f"Imported {base_name}"
            return False, "File missing."
        except Exception as e: return False, str(e)

    @staticmethod
    async def import_tdata_async(tdata_path, name, sessions_dir="sessions"):
        try:
            from opentele.td import TDesktop
            if not os.path.exists(sessions_dir): os.makedirs(sessions_dir)
            td = TDesktop(tdata_path)
            dest_path = os.path.join(sessions_dir, f"{name}.session")
            await td.ToTelethon(dest_path, flag=AccountImporter.DEFAULT_API_ID)
            return True, f"TData {name} converted."
        except Exception as e: return False, str(e)
