import random
import os
import json
import asyncio
import socks
import urllib.request

class ProxyManager:
    def __init__(self, proxy_file="proxies.txt", mapping_file="proxy_mappings.json"):
        self.proxy_file = proxy_file
        self.mapping_file = mapping_file
        self.proxies = []
        self.mappings = {} 
        self.load_proxies()
        self.load_mappings()

    def parse_proxy_string(self, p_str):
        p_str = p_str.strip().replace("socks5://", "").replace("http://", "")
        try:
            if "@" in p_str:
                auth, addr = p_str.split("@")
                user, pw = auth.split(":")
                host, port = addr.split(":")
            else:
                parts = p_str.split(":")
                if len(parts) == 2:
                    host, port, user, pw = parts[0], parts[1], None, None
                elif len(parts) == 4:
                    host, port, user, pw = parts[0], parts[1], parts[2], parts[3]
                else:
                    return None
            return {
                "scheme": "socks5",
                "hostname": host,
                "port": int(port),
                "username": user,
                "password": pw
            }
        except:
            return None

    async def test_single_proxy(self, p_dict, timeout=5):
        try:
            host = "149.154.167.50" 
            port = 443
            loop = asyncio.get_event_loop()
            def _check():
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, p_dict['hostname'], p_dict['port'], True, p_dict.get('username'), p_dict.get('password'))
                s.settimeout(timeout)
                s.connect((host, port))
                s.close()
                return True
            await loop.run_in_executor(None, _check)
            return True
        except:
            return False

    def load_proxies(self):
        if os.path.exists(self.proxy_file):
            with open(self.proxy_file, "r") as f:
                lines = f.readlines()
                self.proxies = [line.strip() for line in lines if self.parse_proxy_string(line)]
        else:
            self.proxies = []

    def load_mappings(self):
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, "r") as f:
                    self.mappings = json.load(f)
            except:
                self.mappings = {}

    def save_mappings(self):
        with open(self.mapping_file, "w") as f:
            json.dump(self.mappings, f)

    def get_proxy_for_account(self, account_name):
        proxy_str = self.mappings.get(account_name)
        if not proxy_str and self.proxies:
            proxy_str = random.choice(self.proxies)
        if not proxy_str:
            return None
        return self.parse_proxy_string(proxy_str)

    def scrape_free_proxies(self, limit=100):
        urls = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=socks5",
            "https://www.proxyscan.io/download?type=socks5"
        ]
        scraped = []
        for url in urls:
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    content = response.read().decode('utf-8')
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ":" in line:
                            scraped.append(line)
            except:
                continue

        scraped = list(set(scraped))
        random.shuffle(scraped)
        return scraped[:limit]
