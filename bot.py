from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from http.cookies import SimpleCookie
from base64 import b64encode
from base58 import b58encode, b58decode
from nacl.signing import SigningKey
from datetime import datetime, timezone
from colorama import *
import asyncio, random, json, sys, re, os

class dTelecom:
    def __init__(self) -> None:
        self.BASE_API = "https://rewards.dtelecom.org"
        
        self.IDS = {
            "website": "67b55527-30aa-4e73-befc-548d55843c1d",
            "organization": "e2ede0f6-6cf7-4e27-9690-b688a36241fe",
            "checkin_rules": "32bcfb22-ae2c-481b-9516-6c9632d135f7",
        }
        
        self.REF_CODE = "MSIW9MDV" # U can change it with yours.

        self.USE_PROXY = False
        self.ROTATE_PROXY = False
        
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.accounts = {}
        
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/117.0.0.0"
        ]

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}dTelecom {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        filename = "accounts.txt"
        try:
            with open(filename, 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            return accounts
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}Failed To Load Accounts: {e}{Style.RESET_ALL}")
            return None

    def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"
    
    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def display_proxy(self, proxy_url=None):
        if not proxy_url: return "No Proxy"

        proxy_url = re.sub(r"^(http|https|socks4|socks5)://", "", proxy_url)

        if "@" in proxy_url:
            proxy_url = proxy_url.split("@", 1)[1]

        return proxy_url
    
    def extract_cookies(self, address, response):
        existing = self.accounts[address].get("cookies", {})
        
        jar = SimpleCookie()
        
        for k, v in existing.items():
            jar[k] = v
        
        for h in response.headers.getall("Set-Cookie", []):
            jar.load(h)
        
        self.accounts[address]["cookies"] = {
            k: m.value for k, m in jar.items()
        }

        return self.accounts[address]["cookies"]
    
    def initialize_headers(self, address: str):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Origin": "https://rewards.dtelecom.org",
            "Pragma": "no-cache",
            "Referer": "https://rewards.dtelecom.org/reward",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": self.accounts[address]["user_agent"]
        }

        return headers.copy()
    
    def generate_signing_key(self, private_key: str):
        try:
            decode_account = b58decode(private_key)
            signing_key = SigningKey(decode_account[:32])
            return signing_key
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Failed to Generate Signing Key {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    def generate_address(self, signing_key: bytes):
        try:
            verify_key = signing_key.verify_key
            address = b58encode(verify_key.encode()).decode()
            return address
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Failed to Generate Sol Address {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    def generate_payload(self, signing_key: bytes, address: str, csrf_token: str):
        try:
            dt_now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
            issued_at = dt_now.replace("+00:00", "Z")

            raw_message = json.dumps({
                "header":{
                    "t":"sip99"
                },
                "payload":{
                    "domain": "rewards.dtelecom.org",
                    "address": address,
                    "statement": "Sign in to the app. Powered by Snag Solutions.",
                    "uri": "https://rewards.dtelecom.org",
                    "version": "1",
                    "chainId": 900001,
                    "nonce": csrf_token,
                    "issuedAt": issued_at,
                    "chainType": "sol"
                }
            }, separators=(',', ':'))

            message = (
                "rewards.dtelecom.org wants you to sign in with your Solana account:\n"
                f"{address}\n\n"
                "Sign in to the app. Powered by Snag Solutions.\n\n"
                "URI: https://rewards.dtelecom.org\n"
                "Version: 1\n"
                "Chain ID: 900001\n"
                f"Nonce: {csrf_token}\n"
                f"Issued At: {issued_at}"
            )

            message_bytes = message.encode("utf-8")
            signed = signing_key.sign(message_bytes)
            signature = b64encode(signed.signature).decode()

            payload = { 
                "message": raw_message,
                "accessToken": signature,
                "signature": signature,
                "walletConnectorName": "MetaMask",
                "walletAddress": address,
                "redirect": "false",
                "callbackUrl": "/protected",
                "chainType": "sol",
                "walletProvider": "undefined",
                "csrfToken": csrf_token,
                "json": "true"
            }

            return payload
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")

    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "With" if proxy_choice == 1 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    self.USE_PROXY = True if proxy_choice == 1 else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        if self.USE_PROXY:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()
                if rotate_proxy in ["y", "n"]:
                    self.ROTATE_PROXY = True if rotate_proxy == "y" else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")
    
    async def ensure_ok(self, response):
        if response.status >= 400:
            error_text = await response.text()
            raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def check_connection(self, proxy_url=None):
        url = "https://api.ipify.org?format=json"

        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url=url, proxy=proxy, proxy_auth=proxy_auth) as response:
                    await self.ensure_ok(response)
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def auth_csrf(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/auth/csrf"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                cookies = self.accounts[address].get("cookies", {})
                headers = self.initialize_headers(address)

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(
                        url=url, headers=headers, cookies=cookies, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        self.extract_cookies(address, response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Csrf Token {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_credentials(self, signing_key: bytes, address: str, csrf_token: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/auth/callback/credentials"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                cookies = self.accounts[address].get("cookies", {})
                headers = self.initialize_headers(address)
                headers["Content-Type"] = "application/json"
                headers["X-Requested-With"] = "XMLHttpRequest"
                payload = self.generate_payload(signing_key, address, csrf_token)

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, json=payload, cookies=cookies, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        self.extract_cookies(address, response)
                        return True
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Session Token {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None

    async def loyality_account(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/loyalty/accounts"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                cookies = self.accounts[address].get("cookies", {})
                headers = self.initialize_headers(address)
                params = {
                    "websiteId": self.IDS["website"], 
                    "organizationId": self.IDS["organization"], 
                    "walletAddress": address
                }
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(
                        url=url, headers=headers, params=params, cookies=cookies, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Balance :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Points {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def complete_checkin(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/loyalty/rules/{self.IDS['checkin_rules']}/complete"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                cookies = self.accounts[address].get("cookies", {})
                headers = self.initialize_headers(address)
                headers["Content-Type"] = "application/json"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, cookies=cookies, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        result = await response.json()

                        if response.status == 400:
                            err_msg = result.get("message")
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                            )
                            return None
                        
                        await self.ensure_ok(response)
                        return result
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, address: str, proxy_url=None):
        while True:
            if self.USE_PROXY:
                proxy_url = self.get_next_proxy_for_account(address)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.display_proxy(proxy_url)} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy_url)
            if is_valid: return True

            if self.ROTATE_PROXY:
                proxy_url = self.rotate_proxy_for_account(address)
                await asyncio.sleep(1)
                continue

            return False
    
    async def process_user_login(self, signing_key: bytes, address: str, proxy_url=None):
        is_valid = await self.process_check_connection(address, proxy_url)
        if not is_valid: return False

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(address)

        auth_csrf = await self.auth_csrf(address, proxy_url)
        if not auth_csrf: return False

        csrf_token = auth_csrf.get("csrfToken")

        credentials = await self.auth_credentials(signing_key, address, csrf_token, proxy_url)
        if not credentials: return False

        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
            f"{Fore.GREEN + Style.BRIGHT} Login Success {Style.RESET_ALL}"
        )

        return True

    async def process_accounts(self, signing_key: bytes, address: str, proxy_url=None):
        logined = await self.process_user_login(signing_key, address, proxy_url)
        if not logined: return False

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(address)

        loyality = await self.loyality_account(address, proxy_url)
        if loyality:
            loyality_data = loyality.get("data", [])

            if loyality_data:
                amount = loyality_data[0].get("amount", 0)
            else:
                amount = 0

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {amount} Points {Style.RESET_ALL}"
            )

        checkin = await self.complete_checkin(address, proxy_url)
        if checkin:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                print(f"{Fore.RED+Style.BRIGHT}No Accounts Loaded.{Style.RESET_ALL}") 
                return

            self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if self.USE_PROXY: self.load_proxies()

                separator = "=" * 25
                for idx, private_key in enumerate(accounts, start=1):

                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {idx} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {len(accounts)} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                    )

                    signing_key = self.generate_signing_key(private_key)
                    if not signing_key: continue

                    address = self.generate_address(signing_key)
                    if not address: continue

                    if address not in self.accounts:
                        self.accounts[address] = {
                            "cookies": {"referral_code": self.REF_CODE},
                            "user_agent": random.choice(self.USER_AGENTS)
                        }

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Address :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                    )
                        
                    await self.process_accounts(signing_key, address)
                    await asyncio.sleep(random.uniform(2.0, 3.0))

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*60)
                
                delay = 24 * 60 * 60
                while delay > 0:
                    formatted_time = self.format_seconds(delay)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)
                    delay -= 1

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = dTelecom()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] dTelecom - BOT{Style.RESET_ALL}                                       "                              
        )
        sys.exit(0)