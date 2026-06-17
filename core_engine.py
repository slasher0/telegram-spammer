import asyncio
import random
import os
import socks
from telethon import TelegramClient, errors as tel_errors, functions, types
from telethon.sessions import StringSession
from datetime import datetime, timedelta
from proxy_manager import ProxyManager

class ChaosEngine:
    @staticmethod
    def obfuscate(text):
        invisible_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
        emojis = ["💀", "🧨", "⚡", "💢", "💥", "🎯"]
        replacements = {'а': 'a', 'о': 'o', 'е': 'e', 'р': 'p', 'с': 'c', 'х': 'x'}
        t_list = list(text)
        for i, c in enumerate(t_list):
            if c.lower() in replacements and random.random() > 0.4:
                t_list[i] = replacements[c.lower()].upper() if c.isupper() else replacements[c.lower()]
        suffix = "".join(random.choices(invisible_chars, k=3)) + random.choice(emojis) + " #" + str(random.randint(1000, 9999))
        return "".join(t_list) + suffix

class SessionManager:
    DEFAULT_API_ID = 14369082
    DEFAULT_API_HASH = "b221b4f79223104634a800ecd4a9c3e5"

    @staticmethod
    def get_session_obj(name, sessions_dir="sessions"):
        string_path = os.path.join(sessions_dir, f"{name}.string")
        if os.path.exists(string_path):
            with open(string_path, "r", encoding="utf-8") as f:
                return StringSession(f.read().strip())
        return os.path.join(sessions_dir, name)

    @staticmethod
    async def check_single_account(name, sessions_dir, proxy_mgr, auto_delete, check_spam, progress_callback, semaphore):
        async with semaphore:
            session_obj = SessionManager.get_session_obj(name, sessions_dir)

            async def attempt_connect(p_cfg):
                client = TelegramClient(session_obj, SessionManager.DEFAULT_API_ID, SessionManager.DEFAULT_API_HASH, 
                                        proxy=p_cfg, connection_retries=0, timeout=10)
                try:
                    await asyncio.wait_for(client.connect(), 15)
                    if await client.is_user_authorized():
                        me = await client.get_me()
                        status_text = "ALIVE"
                        if check_spam:
                            try:
                                async with client.conversation("@SpamBot", timeout=12) as conv:
                                    await conv.send_message("/start")
                                    response = await conv.get_response()
                                    if any(p in response.text.lower() for p in ["no restrictions", "нет никаких ограничений", "свободен"]): 
                                        status_text = "ALIVE (CLEAN)"
                                    else: 
                                        status_text = "SPAMBLOCK"
                            except: status_text = "ALIVE (CHECK FAILED)"
                        return {"success": True, "status": status_text, "user": f"@{me.username or me.id}", "client": client}
                    else:
                        await client.disconnect()
                        return {"success": True, "status": "DEAD", "error": "Unauthorized/Banned"}
                except Exception as e:
                    try: await client.disconnect()
                    except: pass
                    return {"success": False, "error": str(e)}

            assigned_proxy = proxy_mgr.get_proxy_for_account(name)
            if assigned_proxy:
                p_cfg = (socks.SOCKS5, assigned_proxy['hostname'], assigned_proxy['port'], True, assigned_proxy.get('username'), assigned_proxy.get('password'))
                res = await attempt_connect(p_cfg)
            else:
                res = {"success": False, "error": "No proxy assigned"}

            if not res.get("success", False) or res.get("status") == "ERROR":
                for _ in range(3):
                    if not proxy_mgr.proxies: break
                    alt_p_str = random.choice(proxy_mgr.proxies)
                    alt_proxy = proxy_mgr.parse_proxy_string(alt_p_str)
                    if alt_proxy:
                        alt_p_cfg = (socks.SOCKS5, alt_proxy['hostname'], alt_proxy['port'], True, alt_proxy.get('username'), alt_proxy.get('password'))
                        res = await attempt_connect(alt_p_cfg)
                        if res.get("success", False): break

            if res.get("success", False):
                final_res = {"name": name, "status": res["status"], "user": res.get("user", "")}
                if res["status"] == "DEAD" and auto_delete:
                    for ext in [".session", ".string"]:
                        p = os.path.join(sessions_dir, f"{name}{ext}")
                        if os.path.exists(p): os.remove(p)
            else:
                final_res = {"name": name, "status": "ERROR", "error": res.get("error", "All proxies failed")}

            if progress_callback: progress_callback(final_res)
            if "client" in res: await res["client"].disconnect()
            return final_res

    @staticmethod
    async def check_health(sessions_dir, proxy_mgr, auto_delete=False, progress_callback=None, check_spam=False):
        if not os.path.exists(sessions_dir): return []
        files = os.listdir(sessions_dir)
        names = set(f.replace(".session", "").replace(".string", "") for f in files if f.endswith((".session", ".string")))
        semaphore = asyncio.Semaphore(15)
        tasks = [SessionManager.check_single_account(n, sessions_dir, proxy_mgr, auto_delete, check_spam, progress_callback, semaphore) for n in sorted(list(names))]
        return await asyncio.gather(*tasks)

class ReportEngine:
    def __init__(self, target, sessions_dir="sessions", proxy_mgr=None, log_callback=None):
        self.target = target; self.sessions_dir = sessions_dir; self.proxy_mgr = proxy_mgr or ProxyManager(); self.log_callback = log_callback; self.is_running = False; self.stats = {"reported": 0, "failed": 0}
    def log(self, msg):
        if self.log_callback: self.log_callback(f"[REPORT] {msg}")
    async def report_once(self, name):
        proxy = self.proxy_mgr.get_proxy_for_account(name); p_cfg = None
        if proxy: p_cfg = (socks.SOCKS5, proxy['hostname'], proxy['port'], True, proxy.get('username'), proxy.get('password'))
        else: return
        session_obj = SessionManager.get_session_obj(name, self.sessions_dir)
        client = TelegramClient(session_obj, SessionManager.DEFAULT_API_ID, SessionManager.DEFAULT_API_HASH, proxy=p_cfg)
        try:
            await client.connect()
            if not await client.is_user_authorized(): return
            await client(functions.account.ReportPeerRequest(peer=self.target, reason=types.InputReportReasonSpam(), message="Spam"))
            self.stats["reported"] += 1; self.log(f"{name} reported.")
        except Exception as e:
            self.stats["failed"] += 1; self.log(f"{name} failed: {str(e)}")
        finally: await client.disconnect()
    async def start_mass_report(self, reason, gap):
        self.is_running = True; files = os.listdir(self.sessions_dir)
        names = set(f.replace(".session", "").replace(".string", "") for f in files if f.endswith((".session", ".string")))
        for n in sorted(list(names)):
            if not self.is_running: break
            await self.report_once(n); await asyncio.sleep(gap)
        self.is_running = False

class AttackEngine:
    def __init__(self, target, message_text, sessions_dir="sessions", proxy_mgr=None, log_callback=None, photo_path=None):
        self.target = target; self.message_text = message_text; self.sessions_dir = sessions_dir; self.proxy_mgr = proxy_mgr or ProxyManager(); self.log_callback = log_callback; self.photo_path = photo_path; self.is_running = False; self.stats = {"delivered": 0, "failed": 0, "active_accounts": 0}
    def log(self, msg):
        if self.log_callback: self.log_callback(f"[ATTACK] {msg}")
    def get_random_photo(self):
        if not self.photo_path: return None
        if os.path.isfile(self.photo_path): return self.photo_path
        try:
            files = [os.path.join(self.photo_path, f) for f in os.listdir(self.photo_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            return random.choice(files) if files else None
        except: return None
    async def run_account(self, name, limit, account_cd, duration_hours, start_time):
        proxy = self.proxy_mgr.get_proxy_for_account(name); p_cfg = None
        if proxy: p_cfg = (socks.SOCKS5, proxy['hostname'], proxy['port'], True, proxy.get('username'), proxy.get('password'))
        else: return
        session_obj = SessionManager.get_session_obj(name, self.sessions_dir)
        client = TelegramClient(session_obj, SessionManager.DEFAULT_API_ID, SessionManager.DEFAULT_API_HASH, proxy=p_cfg)
        try:
            await client.connect()
            if not await client.is_user_authorized(): self.log(f"Acc {name} unauthorized."); return
            self.stats["active_accounts"] += 1; sent = 0
            while self.is_running and sent < limit:
                if datetime.now() > start_time + timedelta(hours=duration_hours): break
                try:
                    photo = self.get_random_photo(); msg = ChaosEngine.obfuscate(self.message_text)
                    if photo: await client.send_file(self.target, photo, caption=msg)
                    else: await client.send_message(self.target, msg)
                    sent += 1; self.stats["delivered"] += 1; self.log(f"{name} -> Sent ({sent}/{limit})")
                except tel_errors.FloodWaitError as e: await asyncio.sleep(e.seconds)
                except: break
                await asyncio.sleep(account_cd * 60 + random.randint(1, 10))
        finally: self.stats["active_accounts"] -= 1; await client.disconnect()

    async def massive_spam_loop(self, name):
        proxy = self.proxy_mgr.get_proxy_for_account(name); p_cfg = None
        if proxy: p_cfg = (socks.SOCKS5, proxy['hostname'], proxy['port'], True, proxy.get('username'), proxy.get('password'))
        else: return
        session_obj = SessionManager.get_session_obj(name, self.sessions_dir)
        client = TelegramClient(session_obj, SessionManager.DEFAULT_API_ID, SessionManager.DEFAULT_API_HASH, proxy=p_cfg)
        try:
            await client.connect()
            if not await client.is_user_authorized(): return
            self.stats["active_accounts"] += 1
            while self.is_running:
                try:
                    photo = self.get_random_photo(); msg = ChaosEngine.obfuscate(self.message_text)
                    if photo: await client.send_file(self.target, photo, caption=msg)
                    else: await client.send_message(self.target, msg)
                    self.stats["delivered"] += 1
                except: break
                await asyncio.sleep(random.uniform(0.05, 0.15))
        finally: self.stats["active_accounts"] -= 1; await client.disconnect()

    async def start_massive_spam(self):
        self.is_running = True; self.log("!!! NUCLEAR START !!!"); files = os.listdir(self.sessions_dir)
        names = set(f.replace(".session", "").replace(".string", "") for f in files if f.endswith((".session", ".string")))
        tasks = [asyncio.create_task(self.massive_spam_loop(n)) for n in sorted(list(names))]
        await asyncio.gather(*tasks)

    async def start_attack(self, account_gap, limit_per_acc, account_cd, duration_hours):
        self.is_running = True; self.log("!!! RAID START !!!"); start_time = datetime.now(); files = os.listdir(self.sessions_dir)
        names = set(f.replace(".session", "").replace(".string", "") for f in files if f.endswith((".session", ".string")))
        tasks = []
        for n in sorted(list(names)):
            if not self.is_running: break
            tasks.append(asyncio.create_task(self.run_account(n, limit_per_acc, account_cd, duration_hours, start_time))); await asyncio.sleep(account_gap)
        await asyncio.gather(*tasks)

    def stop(self): self.is_running = False
