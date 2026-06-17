import customtkinter as ctk
import asyncio
import threading
import os
import random
import webbrowser
from tkinter import filedialog, messagebox

try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from core_engine import AttackEngine, ReportEngine, SessionManager
from proxy_manager import ProxyManager
from account_importer import AccountImporter

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("megatgspammer2281337")
        self.geometry("1350x950")

        self.proxy_mgr = ProxyManager()
        self.engine = None
        self.report_engine = None
        self.photo_path = None
        self.last_results = {}

        self.bg_loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_bg_loop, daemon=True, name="BackgroundLoop").start()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.github_btn = ctk.CTkButton(self, text="GitHub: slasher0", command=lambda: webbrowser.open("https://github.com/slasher0"), fg_color="#333333", hover_color="#555555")
        self.github_btn.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        self.tab_attack = self.tabview.add("Attack Panel")
        self.tab_report = self.tabview.add("Report Panel")
        self.tab_proxies = self.tabview.add("Proxy Manager")
        self.tab_accounts = self.tabview.add("Account Warehouse")
        self.tab_logs = self.tabview.add("Global Logs")

        self.setup_attack_tab()
        self.setup_report_tab()
        self.setup_proxy_tab()
        self.setup_accounts_tab()
        self.setup_logs_tab()

        self.update_stats()
        self.bind_all("<Control-v>", self.paste_event)
        self.bind_all("<Control-c>", self.copy_event)
        self.bind_all("<Control-a>", self.select_all_event)

    def start_bg_loop(self):
        asyncio.set_event_loop(self.bg_loop)
        self.bg_loop.run_forever()

    def get_loaded_account_names(self):
        if not os.path.exists("sessions"): os.makedirs("sessions")
        files = os.listdir("sessions")
        names = set()
        for f in files:
            if f.endswith((".session", ".string")):
                names.add(f.replace(".session", "").replace(".string", ""))
        return sorted(list(names))

    def get_auto_name(self):
        names = self.get_loaded_account_names()
        nums = [int(n) for n in names if n.isdigit()]
        if not nums: return "1"
        return str(max(nums) + 1)

    def setup_attack_tab(self):
        self.tab_attack.grid_columnconfigure(0, weight=0); self.tab_attack.grid_columnconfigure(1, weight=1)
        sf = ctk.CTkFrame(self.tab_attack, width=280); sf.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(sf, text="SPAM", font=ctk.CTkFont(weight="bold", size=16)).pack(pady=10)
        self.target_entry = ctk.CTkEntry(sf, placeholder_text="Target @username"); self.target_entry.pack(padx=10, pady=5, fill="x")
        self.acc_gap = self.create_setting(sf, "Entry Gap (sec):", "30")
        self.acc_cd = self.create_setting(sf, "Msg Cooldown (min):", "10")
        self.limit = self.create_setting(sf, "Limit per Acc:", "5")
        self.duration = self.create_setting(sf, "Duration (hours):", "2")
        ctk.CTkButton(sf, text="START", fg_color="green", command=self.start_attack).pack(padx=10, pady=15, fill="x")
        ctk.CTkButton(sf, text="HYPER MODE", fg_color="purple", font=ctk.CTkFont(weight="bold"), command=self.start_massive_raid).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(sf, text="STOP", fg_color="red", command=self.stop_attack).pack(padx=10, pady=5, fill="x")
        self.risk_var = ctk.BooleanVar(value=False); ctk.CTkCheckBox(sf, text="Accept IP Ban Risk", variable=self.risk_var, font=ctk.CTkFont(size=10)).pack(padx=10, pady=15)

        mf = ctk.CTkFrame(self.tab_attack); mf.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(mf, text="MESSAGE & MEDIA BUILDER", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.photo_btn = ctk.CTkButton(mf, text="SELECT PHOTO / FOLDER", fg_color="gray", command=self.select_photo); self.photo_btn.pack(padx=10, pady=5, fill="x")
        self.msg_text = ctk.CTkTextbox(mf, height=400); self.msg_text.pack(padx=10, pady=10, fill="both", expand=True)
        self.msg_text.insert("0.0", "Sample Attack Message.")
        self.stats_label = ctk.CTkLabel(mf, text="Stats: Delivered: 0 | Active Units: 0", font=ctk.CTkFont(size=14, weight="bold")); self.stats_label.pack(pady=10)

    def create_setting(self, parent, label_text, default_val):
        ctk.CTkLabel(parent, text=label_text, anchor="w").pack(padx=10, pady=(5, 0), fill="x")
        e = ctk.CTkEntry(parent); e.insert(0, default_val); e.pack(padx=10, pady=(0, 5), fill="x"); return e

    def setup_report_tab(self):
        f = ctk.CTkFrame(self.tab_report); f.pack(padx=20, pady=20, fill="both", expand=True)
        ctk.CTkLabel(f, text="MASS REPORT VECTOR", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=15)
        self.report_target = ctk.CTkEntry(f, placeholder_text="Target @username", width=400); self.report_target.pack(pady=10)
        self.report_reason = ctk.CTkComboBox(f, values=["Spam", "Violence", "Other"], width=400); self.report_reason.pack(pady=10)
        self.report_gap = ctk.CTkEntry(f, width=150); self.report_gap.insert(0, "5"); self.report_gap.pack(pady=5)
        ctk.CTkButton(f, text="INITIATE MASS REPORT", fg_color="orange", height=40, font=ctk.CTkFont(weight="bold"), command=self.start_report).pack(pady=30)
        self.report_stats = ctk.CTkLabel(f, text="Reports Sent: 0", font=ctk.CTkFont(size=14)); self.report_stats.pack()

    def setup_proxy_tab(self):
        self.tab_proxies.grid_columnconfigure(0, weight=1); self.tab_proxies.grid_columnconfigure(1, weight=1)
        lf = ctk.CTkFrame(self.tab_proxies); lf.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(lf, text="GLOBAL PROXY POOL", font=ctk.CTkFont(weight="bold", size=14)).pack(pady=5)
        self.proxy_input = ctk.CTkTextbox(lf, height=500); self.proxy_input.pack(padx=10, pady=10, fill="both", expand=True)

        btn_f = ctk.CTkFrame(lf); btn_f.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_f, text="SAVE", fg_color="green", width=60, command=self.save_proxies_only).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="TEST & CLEAN", fg_color="orange", width=100, command=self.start_proxy_test).pack(side="left", padx=2)

        scrape_f = ctk.CTkFrame(lf); scrape_f.pack(fill="x", padx=10, pady=5)
        self.scrape_limit_slider = ctk.CTkSlider(scrape_f, from_=10, to=500, number_of_steps=49, width=150)
        self.scrape_limit_slider.set(100); self.scrape_limit_slider.pack(side="left", padx=5)
        self.scrape_label = ctk.CTkLabel(scrape_f, text="100", font=ctk.CTkFont(size=10)); self.scrape_label.pack(side="left", padx=2)
        self.scrape_limit_slider.configure(command=lambda v: self.scrape_label.configure(text=str(int(v))))
        ctk.CTkButton(scrape_f, text="SCRAPE NEW", fg_color="blue", width=100, command=self.scrape_proxies_action).pack(side="right", padx=5)

        rf = ctk.CTkFrame(self.tab_proxies); rf.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(rf, text="GROUP BINDING & AUTO-DISTRIBUTION", font=ctk.CTkFont(weight="bold", size=14)).pack(pady=5)

        dist_f = ctk.CTkFrame(rf); dist_f.pack(padx=10, pady=10, fill="x")
        ctk.CTkButton(dist_f, text="distribute proxies", fg_color="purple", height=40, font=ctk.CTkFont(weight="bold"), command=self.auto_distribute_proxies).pack(pady=5, fill="x", padx=10)
        ctk.CTkButton(dist_f, text="REDISTRIBUTE FAILED", fg_color="#A52A2A", height=35, command=self.redistribute_errors).pack(pady=5, fill="x", padx=10)

        range_f = ctk.CTkFrame(rf); range_f.pack(padx=10, pady=10, fill="x")
        self.bind_range = ctk.CTkEntry(range_f, placeholder_text="Range (1-50)"); self.bind_range.pack(padx=10, pady=5, fill="x")
        self.range_proxy = ctk.CTkEntry(range_f, placeholder_text="host:port:user:pass"); self.range_proxy.pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(range_f, text="BIND RANGE", fg_color="blue", command=self.bind_industrial_range).pack(pady=15, fill="x", padx=10)

        self.mapping_list = ctk.CTkTextbox(rf, height=250); self.mapping_list.pack(padx=10, pady=10, fill="both", expand=True)
        ctk.CTkButton(rf, text="CLEAR MAPPINGS", fg_color="red", command=self.clear_bindings).pack(pady=5)
        self.refresh_mapping_ui()

    def setup_accounts_tab(self):
        f = self.tab_accounts; ctk.CTkLabel(f, text="ACCOUNT WAREHOUSE", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        inf = ctk.CTkFrame(f); inf.pack(padx=20, pady=10, fill="x")
        ctk.CTkButton(inf, text="Import JSON+Session", command=self.import_json).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(inf, text="Import TData Folder", command=self.import_tdata).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(inf, text="Direct HEX Key Import", fg_color="green", command=self.import_direct).pack(side="left", padx=5, pady=5)
        self.acc_list = ctk.CTkTextbox(f, height=450); self.acc_list.pack(padx=20, pady=10, fill="both", expand=True)
        self.acc_status_label = ctk.CTkLabel(f, text="Ready", font=ctk.CTkFont(size=14, weight="bold")); self.acc_status_label.pack(pady=10)
        bf = ctk.CTkFrame(f); bf.pack(padx=20, pady=10, fill="x")
        ctk.CTkButton(bf, text="REFRESH", width=120, command=self.force_refresh_list).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="HEALTH", width=120, command=lambda: self.check_sessions_ui(False, False)).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="SPAMBOT", width=150, fg_color="orange", command=lambda: self.check_sessions_ui(False, True)).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="CLEAN", width=100, fg_color="red", command=lambda: self.check_sessions_ui(True, False)).pack(side="left", padx=10)

    def setup_logs_tab(self):
        self.global_logs = ctk.CTkTextbox(self.tab_logs, state="disabled", font=ctk.CTkFont(family="Consolas")); self.global_logs.pack(padx=20, pady=20, fill="both", expand=True)

    def log(self, msg):
        self.global_logs.configure(state="normal"); self.global_logs.insert("end", f"{msg}\n"); self.global_logs.see("end"); self.global_logs.configure(state="disabled")

    def auto_distribute_proxies(self):
        accounts = self.get_loaded_account_names(); proxies_text = self.proxy_input.get("0.0", "end").strip()
        if not proxies_text or not accounts: return
        proxies = [p.strip() for p in proxies_text.split("\n") if p.strip()]
        for i, acc_name in enumerate(accounts): self.proxy_mgr.mappings[acc_name] = proxies[i % len(proxies)]
        self.proxy_mgr.save_mappings(); self.refresh_mapping_ui(); self.log("Auto-distribution complete.")

    def redistribute_errors(self):
        proxies_text = self.proxy_input.get("0.0", "end").strip()
        if not proxies_text: return
        proxies = [p.strip() for p in proxies_text.split("\n") if p.strip()]
        count = 0
        for name, status in self.last_results.items():
            if status == "ERROR":
                self.proxy_mgr.mappings[name] = random.choice(proxies)
                count += 1
        self.proxy_mgr.save_mappings(); self.refresh_mapping_ui(); self.log(f"Redistributed {count} failed accounts.")

    def scrape_proxies_action(self):
        limit = int(self.scrape_limit_slider.get()); scraped = self.proxy_mgr.scrape_free_proxies(limit=limit)
        self.proxy_input.insert("end", "\n" + "\n".join(scraped)); self.log(f"Added {len(scraped)} proxies.")

    def select_photo(self):
        choice = messagebox.askquestion("Media", "Select FOLDER?"); p = filedialog.askdirectory() if choice == 'yes' else filedialog.askopenfilename()
        if p: self.photo_path = p; self.photo_btn.configure(text=f"SET: {os.path.basename(p)}", fg_color="blue")

    def save_proxies_only(self):
        with open("proxies.txt", "w") as f: f.write(self.proxy_input.get("0.0", "end").strip())
        self.proxy_mgr.load_proxies(); self.log("Pool updated.")

    def clear_proxies(self):
        self.proxy_input.delete("0.0", "end"); self.proxy_mgr.proxies = []; self.log("Pool cleared.")

    def start_proxy_test(self):
        self.log("Testing..."); asyncio.run_coroutine_threadsafe(self.do_proxy_test(), self.bg_loop)

    async def do_proxy_test(self):
        text = self.proxy_input.get("0.0", "end").strip().split("\n"); working = []
        for line in text:
            p = self.proxy_mgr.parse_proxy_string(line)
            if p and await self.proxy_mgr.test_single_proxy(p): working.append(line); self.after(0, lambda l=line: self.log(f"[OK] {l}"))
        self.after(0, lambda: self.proxy_input.delete("0.0", "end")); self.after(0, lambda w=working: self.proxy_input.insert("0.0", "\n".join(w))); self.after(0, self.save_proxies_only)

    def bind_industrial_range(self):
        r_str = self.bind_range.get().strip(); prox = self.range_proxy.get().strip()
        if r_str and prox:
            try:
                if "-" in r_str:
                    s, e = map(int, r_str.split("-")); 
                    for i in range(s, e + 1): self.proxy_mgr.mappings[str(i)] = prox
                else: self.proxy_mgr.mappings[r_str] = prox
                self.proxy_mgr.save_mappings(); self.refresh_mapping_ui()
            except: pass

    def clear_bindings(self):
        self.proxy_mgr.mappings = {}; self.proxy_mgr.save_mappings(); self.refresh_mapping_ui()

    def refresh_mapping_ui(self):
        self.mapping_list.delete("0.0", "end")
        for acc, prox in self.proxy_mgr.mappings.items(): self.mapping_list.insert("end", f"{acc} -> {prox}\n")

    def update_stats(self):
        if self.engine: self.stats_label.configure(text=f"Stats: Delivered: {self.engine.stats['delivered']} | Active: {self.engine.stats['active_accounts']}")
        if self.report_engine: self.report_stats.configure(text=f"Reports Sent: {self.report_engine.stats['reported']}")
        self.after(1000, self.update_stats)

    def start_attack(self):
        if not self.risk_var.get(): return
        t = self.target_entry.get(); m = self.msg_text.get("0.0", "end").strip()
        if t and m:
            self.engine = AttackEngine(t, m, proxy_mgr=self.proxy_mgr, log_callback=self.log, photo_path=self.photo_path)
            asyncio.run_coroutine_threadsafe(self.engine.start_attack(int(self.acc_gap.get()), int(self.limit.get()), int(self.acc_cd.get()), float(self.duration.get())), self.bg_loop)

    def start_massive_raid(self):
        if not self.risk_var.get(): return
        t = self.target_entry.get(); m = self.msg_text.get("0.0", "end").strip()
        if t and m:
            self.engine = AttackEngine(t, m, proxy_mgr=self.proxy_mgr, log_callback=self.log, photo_path=self.photo_path)
            asyncio.run_coroutine_threadsafe(self.engine.start_massive_spam(), self.bg_loop)

    def stop_attack(self):
        if self.engine: self.engine.stop()

    def start_report(self):
        t = self.report_target.get()
        if t:
            self.report_engine = ReportEngine(t, proxy_mgr=self.proxy_mgr, log_callback=self.log)
            asyncio.run_coroutine_threadsafe(self.report_engine.start_mass_report("Spam", int(self.report_gap.get())), self.bg_loop)

    def force_refresh_list(self):
        names = self.get_loaded_account_names(); self.acc_list.delete("0.0", "end")
        for n in names: self.acc_list.insert("end", f"[READY] {n}\n")

    def check_sessions_ui(self, auto_del, check_spam):
        self.acc_list.delete("0.0", "end"); asyncio.run_coroutine_threadsafe(self.do_health_check(auto_del, check_spam), self.bg_loop)

    async def do_health_check(self, auto_del, check_spam):
        self.last_results = {}
        def on_progress(res): 
            self.last_results[res['name']] = res['status']
            info = res.get('user', res.get('error', ''))
            self.after(0, lambda: self.acc_list.insert("end", f"[{res['status']}] {res['name']} - {info}\n"))
        results = await SessionManager.check_health("sessions", self.proxy_mgr, auto_delete=auto_del, progress_callback=on_progress, check_spam=check_spam)
        alive = sum(1 for r in results if "ALIVE" in r['status'])
        self.after(0, lambda: self.acc_status_label.configure(text=f"WAREHOUSE: {alive} UNITS"))

    def import_direct(self):
        bw = ctk.CTkToplevel(self); bw.title("HEX Import"); bw.geometry("600x500"); bw.attributes("-topmost", True)
        it = ctk.CTkTextbox(bw, height=350); it.pack(padx=20, pady=10, fill="both", expand=True)
        def process_bulk():
            lines = it.get("0.0", "end").strip().split("\n"); cur = int(self.get_auto_name())
            for line in lines:
                if ":" in line:
                    p = line.strip().split(":"); asyncio.run_coroutine_threadsafe(AccountImporter.import_from_raw_key_async(str(cur), p[0], int(p[1])), self.bg_loop); cur += 1
            bw.destroy(); self.after(1000, self.force_refresh_list)
        ctk.CTkButton(bw, text="START IMPORT", command=process_bulk).pack(pady=20)

    def import_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path: AccountImporter.import_from_json(path); self.force_refresh_list()

    def import_tdata(self):
        path = filedialog.askdirectory()
        if path: asyncio.run_coroutine_threadsafe(self.do_tdata_import(path, self.get_auto_name()), self.bg_loop)

    async def do_tdata_import(self, path, name):
        await AccountImporter.import_tdata_async(path, name); self.after(0, self.force_refresh_list)

    def paste_event(self, event): pass
    def copy_event(self, event): pass
    def select_all_event(self, event):
        w = self.focus_get()
        if isinstance(w, ctk.CTkEntry): w.select_range(0, 'end'); w.icursor('end')
        elif isinstance(w, ctk.CTkTextbox): w.tag_add("sel", "1.0", "end")
        return "break"

if __name__ == "__main__":
    app = App(); app.mainloop()
