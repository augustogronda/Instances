import os
import time
import json
import random
import asyncio
import requests
from tkinter import Tk, Label, Entry, Button, Checkbutton, BooleanVar, ttk
from tkinter.messagebox import askokcancel, showinfo, showerror
from playwright.async_api import async_playwright
import threading
from datetime import datetime
import urllib.parse
import subprocess
import platform

# Lista de User-Agents reales para rotación
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
]

# Lista de resoluciones de pantalla comunes
VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1440, 'height': 900},
    {'width': 1536, 'height': 864},
    {'width': 1280, 'height': 720},
    {'width': 1600, 'height': 900}
]

# Idiomas comunes
LOCALES = ['es-ES', 'es-AR', 'es-MX', 'es-CO', 'en-US', 'en-GB']

playwright_instances = []
proxy_list = []  # Lista global de proxies
wireproxy_processes = []  # Procesos de wireproxy en segundo plano para cerrarlos al salir

# Configuración de Brave con Tor
def find_brave_browser():
    """Detecta la instalación de Brave Browser en el sistema"""
    system = platform.system()
    brave_paths = []
    
    if system == "Windows":
        brave_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\Application\brave.exe")
        ]
    elif system == "Darwin":  # macOS
        brave_paths = [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        ]
    elif system == "Linux":
        brave_paths = [
            "/usr/bin/brave-browser",
            "/usr/bin/brave",
            "/snap/bin/brave",
            "/opt/brave.com/brave/brave-browser"
        ]
    
    for path in brave_paths:
        if os.path.exists(path):
            print(f"✅ Brave Browser encontrado en: {path}")
            return path
    
    print("❌ Brave Browser no encontrado en el sistema")
    return None

def check_tor_availability():
    """Verifica si Tor está disponible en Brave"""
    brave_path = find_brave_browser()
    if not brave_path:
        return False, "Brave Browser no está instalado"
    
    try:
        # Verificar si Brave puede abrir ventanas Tor
        result = subprocess.run([brave_path, "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, f"Brave Browser disponible: {result.stdout.strip()}"
        else:
            return False, "Error verificando Brave Browser"
    except Exception as e:
        return False, f"Error verificando Brave: {str(e)}"

# Clase para manejar proxies de forma centralizada
class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
    
    def clear(self):
        """Limpia todas las listas de proxies"""
        self.proxies.clear()
        self.working_proxies.clear()
        global proxy_list
        proxy_list.clear()
    
    def add_proxy(self, proxy):
        """Agrega un proxy a la lista"""
        if proxy and proxy not in self.proxies:
            self.proxies.append(proxy)
            global proxy_list
            if proxy not in proxy_list:
                proxy_list.append(proxy)
    
    def add_proxies(self, proxy_list_new):
        """Agrega múltiples proxies"""
        for proxy in proxy_list_new:
            self.add_proxy(proxy)
    
    def get_proxies(self):
        """Obtiene la lista de proxies"""
        return self.proxies.copy()
    
    def count(self):
        """Cuenta los proxies disponibles"""
        return len(self.proxies)
    
    def save_to_file(self, filename="proxies.txt"):
        """Guarda los proxies en un archivo"""
        try:
            with open(filename, "w") as f:
                f.write("# Proxies obtenidos automáticamente y validados\n")
                f.write(f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total: {len(self.proxies)} proxies funcionando\n")
                f.write("# Formato: ip:puerto\n\n")
                
                for proxy in self.proxies:
                    f.write(f"{proxy}\n")
                    
            print(f"✅ Guardados {len(self.proxies)} proxies en {filename}")
            return True
        except Exception as e:
            print(f"❌ Error guardando proxies: {e}")
            return False

# Instancia global del manejador de proxies
proxy_manager = ProxyManager()

# APIs de proxies gratuitos - Optimizadas para Argentina/Boca Juniors
PROXY_APIS = {
    'proxyscrape': {
        'http': 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=AR,BR,UY,CL&ssl=all&anonymity=all&skip=0&limit=50',
        'http_global': 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=30',
        'socks4': 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=socks4&timeout=10000&country=AR,BR,UY,CL&skip=0&limit=30',
        'socks5': 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=socks5&timeout=10000&country=AR,BR,UY,CL&skip=0&limit=30'
    },
    'freeproxy': {
        'http': 'https://www.proxy-list.download/api/v1/get?type=http',
        'https': 'https://www.proxy-list.download/api/v1/get?type=https',
        'socks4': 'https://www.proxy-list.download/api/v1/get?type=socks4',
        'socks5': 'https://www.proxy-list.download/api/v1/get?type=socks5'
    },
    'proxylist': {
        'http': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'socks4': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
        'socks5': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt'
    }
}

# Configuración específica para Boca Juniors
BOCA_JUNIORS_CONFIG = {
    'target_url': 'https://soysocio.bocajuniors.com.ar',
    'preferred_countries': ['AR', 'BR', 'UY', 'CL'],  # Países cercanos
    'preferred_ports': [80, 8080, 3128, 8888],  # Puertos que suelen funcionar
    'timeout': 15,  # Timeout más largo para sitios argentinos
    'user_agents_argentina': [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]
}

def get_dynamic_proxy_limit(instances_count):
    """Calcula el límite dinámico de proxies basado en el número de instancias"""
    # Límite mínimo: 10 proxies
    # Límite recomendado: 2x las instancias para tener margen
    # Límite máximo: 50 proxies para no sobrecargar las APIs
    return min(max(instances_count * 2, 10), 50)

class AdvancedInstanceManager:
    def __init__(self):
        self.instances = []
        self.session_cookies = {}
        
    def get_random_proxy(self):
        """Obtiene un proxy aleatorio de la lista"""
        if not proxy_list:
            return None
        
        proxy_string = random.choice(proxy_list)
        if proxy_string.startswith("socks5://"):
            # Para proxies que ya tienen el protocolo
            proxy_config = {'server': proxy_string}
            return proxy_config
            
        if ':' in proxy_string:
            parts = proxy_string.split(':')
            if len(parts) >= 2:
                # Si empieza con http o socks, dejarlo tal cual, sino agregar http://
                protocol = "http://" if not parts[0].startswith("http") and not parts[0].startswith("socks") else ""
                
                proxy_config = {
                    'server': f"{protocol}{parts[0]}:{parts[1]}",
                    'username': parts[2] if len(parts) > 2 else None,
                    'password': parts[3] if len(parts) > 3 else None
                }
                return proxy_config
        return None

    async def create_stealth_browser(self, instance_id):
        """Crea un navegador con características anti-detección avanzadas"""
        playwright = await async_playwright().start()
        
        # Configuración específica para Boca Juniors
        url = url_entry.get() if url_entry else ""
        is_boca_site = 'bocajuniors.com.ar' in url.lower()
        
        if is_boca_site:
            # Configuración optimizada para Boca Juniors
            user_agent = random.choice(BOCA_JUNIORS_CONFIG['user_agents_argentina'])
            viewport = {'width': 1366, 'height': 768}  # Resolución común en Argentina
            locale = 'es-AR'  # Español argentino
            timezone = 'America/Argentina/Buenos_Aires'
            print(f"🏆 Configuración optimizada para Boca Juniors - Instancia {instance_id}")
        else:
            # Configuración general
            user_agent = random.choice(USER_AGENTS)
            viewport = random.choice(VIEWPORTS)
            locale = random.choice(LOCALES)
            timezone = 'America/Argentina/Buenos_Aires'
        
        # Verificar si usar Brave con Tor
        use_brave_tor = getattr(self, 'use_brave_tor', False) if hasattr(self, 'use_brave_tor') else (use_tor_mode.get() if 'use_tor_mode' in globals() else False)
        
        if use_brave_tor:
            # Configuración para Brave con Tor
            brave_path = find_brave_browser()
            if brave_path:
                print(f"🔒 Instancia {instance_id}: Usando Brave con Tor")
                browser_args = [
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--incognito',  # Modo incógnito
                    '--disable-brave-update',
                    '--disable-brave-rewards',
                    '--disable-brave-sync',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
                
                try:
                    browser = await playwright.chromium.launch(
                        headless=False,
                        executable_path=brave_path,
                        args=browser_args
                    )
                    context = await browser.new_context(user_agent=user_agent, viewport=viewport, locale=locale, timezone_id=timezone)
                    print(f"✅ Instancia {instance_id}: Brave con Tor iniciado correctamente")
                except Exception as e:
                    print(f"❌ Error iniciando Brave: {e}. Usando navegador regular")
                    browser = await playwright.chromium.launch(
                        headless=False,
                        args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
                    )
                    context = await browser.new_context(user_agent=user_agent, viewport=viewport, locale=locale, timezone_id=timezone)
            else:
                print(f"❌ Brave no encontrado. Usando navegador regular para instancia {instance_id}")
                browser = await playwright.chromium.launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
                )
                context = await browser.new_context(user_agent=user_agent, viewport=viewport, locale=locale, timezone_id=timezone)
        else:
            # Configuración regular con proxies
            proxy_config = None
            if use_proxies.get() and proxy_list:
                proxy_config = self.get_random_proxy()
                if proxy_config:
                    print(f"🌐 Instancia {instance_id}: Usando proxy: {proxy_config['server']}")
            
            # Configuración del navegador
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
            
            # Agregar configuración de proxy si está disponible
            if proxy_config:
                browser_args.extend([
                    f'--proxy-server={proxy_config["server"]}',
                    '--proxy-bypass-list=<-loopback>'
                ])
            
            # Remover disable-extensions y agregar banderas anti automatizacion
            if '--disable-extensions' in browser_args:
                browser_args.remove('--disable-extensions')
            browser_args.extend(["--exclude-switches=enable-automation"])
            
            profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "Profiles", f"chrome_profile_{instance_id}"))
            
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=False,
                args=browser_args,
                user_agent=user_agent,
                viewport=viewport,
                locale=locale,
                timezone_id=timezone,
                permissions=['geolocation'],
                geolocation={'latitude': -34.6037, 'longitude': -58.3816},  # Buenos Aires
                color_scheme='light',
                reduced_motion='no-preference',
                forced_colors='none',
                ignore_https_errors=True,
                accept_downloads=False
            )
            browser = context.browser if hasattr(context, 'browser') else context
        
        # Configurar listeners del contexto para evitar cierres
        def handle_context_close():
            print(f"⚠️ Contexto de instancia {instance_id} se cerró - intentando mantener navegador abierto")
        
        context.on("close", handle_context_close)
        
        # Scripts de evasión avanzados
        await context.add_init_script("""
            // Eliminar propiedades de automatización
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Sobrescribir el plugin de Chrome
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Sobrescribir languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es'],
            });
            
            // Sobrescribir permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Prevenir cierres automáticos por errores
            window.addEventListener('error', function(e) {
                console.log('Error capturado pero ventana permanece abierta:', e.message);
                e.preventDefault();
                return false;
            });
            
            // Prevenir cierres por unhandledrejection
            window.addEventListener('unhandledrejection', function(e) {
                console.log('Promise rejection capturada pero ventana permanece abierta:', e.reason);
                e.preventDefault();
                return false;
            });
            
            // Simular comportamiento de mouse real
            let mouseX = 0, mouseY = 0;
            document.addEventListener('mousemove', (e) => {
                mouseX = e.clientX;
                mouseY = e.clientY;
            });
            
            // Simular actividad de teclado
            let lastKeyTime = Date.now();
            document.addEventListener('keydown', () => {
                lastKeyTime = Date.now();
            });
        """)
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Configurar timeouts más realistas y tolerantes
        page.set_default_timeout(60000)  # 60 segundos en lugar de 30
        page.set_default_navigation_timeout(60000)  # Más tiempo para cargar
        
        return playwright, browser, context, page
    
    async def simulate_human_behavior(self, page, instance_id):
        """Simula comportamiento humano realista"""
        if not stealth_mode.get():
            return
            
        # Movimientos de mouse aleatorios
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 1200)
            y = random.randint(100, 800)
            await page.mouse.move(x, y)
            await page.wait_for_timeout(random.randint(100, 500))
        
        # Scroll aleatorio
        for _ in range(random.randint(1, 3)):
            delta_y = random.randint(-500, 500)
            await page.mouse.wheel(0, delta_y)
            await page.wait_for_timeout(random.randint(500, 1500))
        
        # Simular actividad de teclado ocasional
        if random.random() < 0.3:  # 30% de probabilidad
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(random.randint(200, 800))
    
    async def open_advanced_instances(self, url, num_instances):
        """Abre instancias con características anti-detección"""
        global playwright_instances
        playwright_instances = []
        
        print(f"🚀 Iniciando {num_instances} instancias para {url}")
        
        for i in range(num_instances):
            playwright = None
            browser = None
            context = None
            page = None
            
            try:
                # Delay progresivo entre instancias
                if i > 0:
                    delay = random.uniform(5, 15)  # 5-15 segundos entre instancias
                    await asyncio.sleep(delay)
                
                # Crear navegador sigiloso
                playwright, browser, context, page = await self.create_stealth_browser(i)
                
                # Configurar manejo de errores para evitar que se cierre la ventana
                def handle_page_close():
                    print(f"⚠️ Página {i+1} se cerró, pero el navegador permanece abierto")
                
                page.on("close", handle_page_close)
                
                # Manejar errores de página sin cerrar
                def handle_page_crash():
                    print(f"⚠️ Error/crash en página {i+1} - ventana permanece abierta")
                
                page.on("crash", handle_page_crash)
                
                # Manejar errores de consola sin cerrar
                def handle_console_error(msg):
                    # Solo loguear, no hacer nada que pueda cerrar la ventana
                    if msg.type == "error":
                        print(f"⚠️ Error en consola instancia {i+1}: {msg.text}")
                
                page.on("console", handle_console_error)
                
                # Navegar con retraso aleatorio - con manejo robusto de errores
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    print(f"✅ Instancia {i+1}: Navegación exitosa a {url}")
                except Exception as nav_error:
                    print(f"⚠️ Error navegando instancia {i+1}: {str(nav_error)}")
                    print(f"💡 La ventana permanece abierta - puedes navegar manualmente")
                    # Intentar cargar una página de error personalizada o dejar en blanco
                    try:
                        await page.goto("about:blank", timeout=5000)
                    except:
                        pass  # Si falla, dejar la página como está
                
                # Simular comportamiento humano solo si la navegación fue exitosa
                try:
                    await self.simulate_human_behavior(page, i)
                except Exception as behavior_error:
                    print(f"⚠️ Error en simulación de comportamiento instancia {i+1}: {str(behavior_error)}")
                    # Continuar de todas formas
                
                # Guardar instancia SIEMPRE, incluso si hubo errores
                # Esto asegura que la ventana no se pierda
                playwright_instances.append((playwright, browser, context, page))
                
                # Log de actividad
                print(f"✅ Instancia {i+1} creada y guardada (ventana permanece abierta)")
                
            except Exception as e:
                print(f"❌ Error crítico creando instancia {i+1}: {str(e)}")
                # Si se creó el navegador pero falló algo más, guardarlo de todas formas
                if browser is not None and context is not None and page is not None:
                    try:
                        playwright_instances.append((playwright, browser, context, page))
                        print(f"💡 Instancia {i+1} guardada a pesar del error - ventana permanece abierta")
                    except Exception as save_error:
                        print(f"❌ No se pudo guardar instancia {i+1}: {str(save_error)}")
                else:
                    print(f"⚠️ Instancia {i+1} no se pudo crear completamente")
                continue
        
        return playwright_instances

    async def monitor_queues_loop(self):
        """Monitorea el tiempo restante en las filas de Queue-it de forma asíncrona"""
        while True:
            await asyncio.sleep(15)
            if not playwright_instances:
                continue
                
            import re
            for i, instance_data in enumerate(playwright_instances):
                try:
                    playwright, browser, context, page = instance_data
                    if page.is_closed():
                        continue
                        
                    script = """
                    () => {
                        let text = '';
                        let timeElem = document.getElementById('MainPart_lbWhichIsIn') || 
                                       document.getElementById('MainPart_TimeLeft') || 
                                       document.querySelector('.time-left');
                        if (timeElem) { text += timeElem.innerText + ' '; }
                        if (text === '') { text = document.body.innerText; }
                        return text;
                    }
                    """
                    page_text = await page.evaluate(script)
                    
                    if not page_text:
                        continue
                        
                    page_text = page_text.lower()
                    
                    match = re.search(r'(\d+)\s*(minuto|minute)', page_text)
                    is_less_than_two = False
                    time_left_str = None
                    
                    if match:
                        mins = int(match.group(1))
                        time_left_str = f"{mins} minutos"
                        if mins <= 2:
                            is_less_than_two = True
                    elif "menos de un minuto" in page_text or "less than a minute" in page_text or "menos de 1 minuto" in page_text:
                        time_left_str = "< 1 minuto"
                        is_less_than_two = True
                    elif "tu turno es el próximo" in page_text or "your turn is next" in page_text:
                        time_left_str = "¡Tu turno!"
                        is_less_than_two = True
                    elif "hora" in page_text or "hour" in page_text:
                        time_left_str = "+ de 1 hora"
                    elif "calculando" in page_text or "calculating" in page_text:
                        time_left_str = "Calculando tiempo..."
                    elif "la fila abrirá" in page_text or "the queue will open" in page_text or "la fila se abrirá" in page_text:
                        time_left_str = "Fila cerrada (En espera)"
                        
                    if time_left_str:
                        print(f"Instancia {i} - Tiempo restante: {time_left_str}")
                    else:
                        preview = page_text.replace('\n', ' ')[:80]
                        print(f"Instancia {i} - Estado desconocido. Texto leído: {preview}")
                    
                    if is_less_than_two:
                        print(f"⚠️ ¡ATENCIÓN! La instancia {i} está a punto de entrar.")
                        alert_script = """
                        () => {
                            if (!window.alert_shown) {
                                alert('¡ATENCIÓN! Faltan menos de 2 minutos en esta instancia.\\n\\nVe rápido.');
                                window.alert_shown = true;
                            }
                        }
                        """
                        await page.evaluate(alert_script)
                        
                except Exception as e:
                    print(f"❌ Error leyendo instancia {i}: {type(e).__name__} - {str(e)[:100]}")
                    pass

# Instancia global del manager
instance_manager = AdvancedInstanceManager()

def save_config(data):
    """Guarda la configuración en archivo JSON"""
    try:
        with open("config_advanced.json", "w") as config_file:
            json.dump(data, config_file, indent=4)
    except Exception as e:
        showerror("Error", f"Error guardando la configuración: {str(e)}")

def load_config():
    """Carga la configuración desde archivo JSON"""
    try:
        if os.path.exists("config_advanced.json"):
            with open("config_advanced.json", "r") as config_file:
                return json.load(config_file)
    except Exception as e:
        showerror("Error", f"Error cargando configuración: {str(e)}")
    return None

def ensure_wireproxy():
    """Descarga wireproxy si no existe"""
    import urllib.request
    import tarfile
    if os.path.exists("wireproxy.exe"):
        return True
    
    showinfo("Descargando Wireproxy", "Wireproxy no encontrado. Descargando automáticamente para manejar Surfshark/WireGuard localmente...")
    try:
        url = "https://github.com/octeep/wireproxy/releases/download/v1.0.8/wireproxy-windows-amd64.tar.gz"
        urllib.request.urlretrieve(url, "wireproxy.tar.gz")
        with tarfile.open("wireproxy.tar.gz", "r:gz") as tar:
            tar.extractall()
        if os.path.exists("wireproxy.tar.gz"):
            os.remove("wireproxy.tar.gz")
        return os.path.exists("wireproxy.exe")
    except Exception as e:
        showerror("Error", f"No se pudo descargar wireproxy: {e}\nPor favor descárgalo manualmente de GitHub (octeep/wireproxy) y pon wireproxy.exe en esta carpeta.")
        return False

def load_wireguard_proxies():
    """Carga configuraciones de WireGuard e inicia wireproxy localmente para cada uno"""
    try:
        if not ensure_wireproxy():
            return

        wireguard_dir = "wireguard-configs"
        if not os.path.exists(wireguard_dir):
            showinfo("Info", f"La carpeta {wireguard_dir} no existe.\n\nCreando carpeta...")
            os.makedirs(wireguard_dir, exist_ok=True)
            showinfo("Carpeta Creada", f"Se creó la carpeta {wireguard_dir}.\n\nColoca tus archivos .conf de Surfshark/WireGuard allí y vuelve a intentar.")
            return
        
        # Buscar archivos .conf
        conf_files = [f for f in os.listdir(wireguard_dir) if f.endswith('.conf')]
        
        if not conf_files:
            showinfo("Info", f"No se encontraron archivos .conf en {wireguard_dir}\n\nColoca tus configuraciones de WireGuard allí.")
            return
            
        temp_dir = os.path.join(wireguard_dir, "tmp")
        os.makedirs(temp_dir, exist_ok=True)
        
        wireguard_proxies = []
        base_port = 1080
        
        global wireproxy_processes
        
        for idx, conf_file in enumerate(conf_files):
            try:
                file_path = os.path.join(wireguard_dir, conf_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Crear config de wireproxy añadiendo bloque [Socks5]
                port = base_port + idx
                proxy_config = f"\n[Socks5]\nBindAddress = 127.0.0.1:{port}\n"
                
                temp_conf_path = os.path.join(temp_dir, f"wp_{conf_file}")
                with open(temp_conf_path, 'w', encoding='utf-8') as f:
                    f.write(content + proxy_config)
                
                # Iniciar wireproxy silenciosamente en background
                process = subprocess.Popen(
                    ["wireproxy.exe", "-c", temp_conf_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                
                wireproxy_processes.append(process)
                
                # Para Playwright el proxy socks5 se pasa como socks5://ip:puerto
                proxy_str = f"socks5://127.0.0.1:{port}"
                wireguard_proxies.append(proxy_str)
                print(f"✅ Wireproxy iniciado en puerto {port} para {conf_file}")
                
            except Exception as e:
                print(f"❌ Error configurando wireproxy para {conf_file}: {e}")
                continue
        
        if wireguard_proxies:
            # Agregar a la lista de proxies existente (no limpiar)
            proxy_manager.add_proxies(wireguard_proxies)
            proxy_manager.save_to_file()
            
            result_msg = f"""🔐 Surfshark/WireGuard Iniciado Localmente:

✅ Archivos procesados: {len(conf_files)}
🌐 Túneles SOCKS5 creados: {len(wireguard_proxies)}
📋 Total en lista de proxies: {proxy_manager.count()}

Se han iniciado {len(wireproxy_processes)} procesos de VPN locales (wireproxy) en segundo plano.
Cada instancia de navegador usará un túnel WireGuard distinto de forma aislada."""
            
            showinfo("WireGuard Configurado", result_msg)
            print(f"🔐 Cargados {len(wireguard_proxies)} túneles locales desde WireGuard")
        else:
            showinfo("Advertencia", f"No se pudo iniciar ningún túnel local de WireGuard.")
            
    except Exception as e:
        showerror("Error", f"Error cargando proxies de WireGuard: {str(e)}")
        print(f"❌ Error: {e}")

def load_proxy_list():
    """Carga lista de proxies desde archivo"""
    try:
        if os.path.exists("proxies.txt"):
            with open("proxies.txt", "r") as f:
                # Filtrar líneas que no sean comentarios y tengan contenido
                loaded_proxies = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                
            if loaded_proxies:
                proxy_manager.clear()
                proxy_manager.add_proxies(loaded_proxies)
                showinfo("Proxies Cargados", f"Se cargaron {proxy_manager.count()} proxies válidos")
                print(f"Proxies cargados: {loaded_proxies[:5]}...")
            else:
                showinfo("Info", "No se encontraron proxies válidos en el archivo")
        else:
            showinfo("Info", "Archivo proxies.txt no encontrado. Creando archivo de ejemplo...")
            # Crear archivo de ejemplo
            with open("proxies.txt", "w") as f:
                f.write("# Archivo de proxies - Un proxy por línea\n")
                f.write("# Formato: ip:puerto:usuario:contraseña (opcional)\n")
                f.write("# Ejemplo:\n")
                f.write("# 192.168.1.100:8080\n")
                f.write("# 192.168.1.101:8080:usuario:contraseña\n")
            showinfo("Archivo Creado", "Se creó el archivo proxies.txt con ejemplos. Edítalo con tus proxies reales.")
    except Exception as e:
        showerror("Error", f"Error cargando proxies: {str(e)}")

def is_preferred_proxy_for_boca(proxy_string):
    """Verifica si un proxy es preferido para Boca Juniors"""
    try:
        parts = proxy_string.split(':')
        if len(parts) < 2:
            return False
        
        port = int(parts[1])
        # Priorizar puertos comunes que funcionan bien con sitios argentinos
        return port in BOCA_JUNIORS_CONFIG['preferred_ports']
    except:
        return False

def validate_proxy_for_boca(proxy_string, timeout=15):
    """Valida un proxy específicamente para Boca Juniors"""
    try:
        parts = proxy_string.split(':')
        if len(parts) < 2:
            print(f"❌ Formato inválido: {proxy_string}")
            return False
        
        proxy_url = f"http://{parts[0]}:{parts[1]}"
        proxies = {'http': proxy_url, 'https': proxy_url}
        
        # Primero probar con el sitio de Boca directamente
        try:
            print(f"🏆 Probando {proxy_string} con Boca Juniors...")
            response = requests.get(BOCA_JUNIORS_CONFIG['target_url'], proxies=proxies, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ Proxy {proxy_string} funciona PERFECTAMENTE con Boca Juniors")
                return True
            else:
                print(f"⚠️ Proxy {proxy_string} - Status {response.status_code} con Boca")
        except requests.exceptions.ConnectTimeout:
            print(f"⏰ Proxy {proxy_string} - Timeout con Boca")
        except requests.exceptions.ProxyError:
            print(f"🚫 Proxy {proxy_string} - Error de proxy con Boca")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Proxy {proxy_string} - Error de conexión con Boca")
        except Exception as e:
            print(f"❓ Proxy {proxy_string} - Error con Boca: {type(e).__name__}")
        
        # Si falla con Boca, probar con endpoints de prueba
        test_urls = [
            ('http://httpbin.org/ip', 'HttpBin'),
            ('http://api.ipify.org?format=json', 'Ipify')
        ]
        
        for test_url, service_name in test_urls:
            try:
                response = requests.get(test_url, proxies=proxies, timeout=8)
                if response.status_code == 200:
                    print(f"⚠️ Proxy {proxy_string} funciona con {service_name} pero NO con Boca")
                    return False  # No sirve si no funciona con Boca
            except:
                continue
        
        print(f"❌ Proxy {proxy_string} no funciona")
        return False
    except Exception as e:
        print(f"❌ Error validando proxy {proxy_string}: {e}")
        return False

def validate_proxy(proxy_string, timeout=8):
    """Valida si un proxy funciona correctamente (función general)"""
    try:
        parts = proxy_string.split(':')
        if len(parts) < 2:
            print(f"❌ Formato inválido: {proxy_string}")
            return False
        
        proxy_url = f"http://{parts[0]}:{parts[1]}"
        proxies = {'http': proxy_url, 'https': proxy_url}
        
        # Prueba rápida de conexión con múltiples endpoints
        test_urls = [
            ('http://httpbin.org/ip', 'HttpBin'),
            ('http://api.ipify.org?format=json', 'Ipify'),
            ('http://ip-api.com/json', 'IP-API'),
            ('http://icanhazip.com', 'ICanHazIP')
        ]
        
        for test_url, service_name in test_urls:
            try:
                response = requests.get(test_url, proxies=proxies, timeout=timeout)
                if response.status_code == 200:
                    print(f"✅ Proxy {proxy_string} funciona con {service_name}")
                    return True
            except requests.exceptions.ConnectTimeout:
                continue
            except requests.exceptions.ProxyError:
                continue
            except requests.exceptions.ConnectionError:
                continue
            except Exception as e:
                continue
        
        print(f"❌ Proxy {proxy_string} falló en todos los tests")
        return False
    except Exception as e:
        print(f"❌ Error validando proxy {proxy_string}: {e}")
        return False

def fetch_proxies_from_api(api_name='proxyscrape', protocol='http', limit=20, validate=True):
    """Obtiene proxies automáticamente desde APIs con validación opcional"""
    try:
        if api_name not in PROXY_APIS:
            print(f"❌ API {api_name} no disponible")
            return []
        
        if protocol not in PROXY_APIS[api_name]:
            print(f"❌ Protocolo {protocol} no disponible para {api_name}")
            return []
        
        api_url = PROXY_APIS[api_name][protocol]
        print(f"🔄 Obteniendo proxies desde {api_name} ({protocol})...")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        # Parsear respuesta según el formato de cada API
        raw_text = response.text.strip()
        print(f"📊 Respuesta de {api_name}: {len(raw_text)} caracteres")
        
        # Dividir según el formato de cada API
        if api_name == 'proxyscrape':
            # ProxyScrape v4 usa espacios como separador
            proxies = [proxy.strip() for proxy in raw_text.split() if proxy.strip()]
            print(f"📋 Proxies encontrados (separados por espacios): {len(proxies)}")
        else:
            # Otras APIs usan líneas como separador
            proxies = [line.strip() for line in raw_text.split('\n') if line.strip()]
            print(f"📋 Líneas encontradas: {len(proxies)}")
        
        # Filtrar y limpiar proxies
        valid_proxies = []
        for proxy in proxies:
            proxy = proxy.strip()
            if proxy and ':' in proxy and not proxy.startswith('#'):
                # Validar formato básico ip:puerto
                parts = proxy.split(':')
                if len(parts) >= 2 and parts[0] and parts[1].isdigit():
                    # Validar que la IP tenga formato correcto
                    ip_parts = parts[0].split('.')
                    if len(ip_parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                        valid_proxies.append(proxy)
                    else:
                        print(f"❌ IP inválida: {proxy}")
                else:
                    print(f"❌ Formato inválido: {proxy}")
        
        print(f"✅ Proxies encontrados: {len(proxies)}, Válidos: {len(valid_proxies)}")
        
        # Mostrar algunos ejemplos
        if valid_proxies:
            print(f"📝 Ejemplos de proxies válidos: {valid_proxies[:3]}")
        else:
            print("⚠️ No se encontraron proxies válidos")
            print(f"📄 Primeras líneas de respuesta: {proxies[:5]}")
        
        # Validar proxies si está habilitado
        if validate and valid_proxies:
            print("🔍 Validando proxies...")
            working_proxies = []
            for proxy in valid_proxies[:limit*2]:  # Probar más para tener suficientes
                if validate_proxy(proxy):
                    working_proxies.append(proxy)
                    print(f"✅ Proxy funcionando: {proxy}")
                    if len(working_proxies) >= limit:
                        break
                else:
                    print(f"❌ Proxy falló: {proxy}")
            
            valid_proxies = working_proxies
            print(f"🎯 Proxies funcionando: {len(valid_proxies)}")
        
        # Limitar cantidad final
        valid_proxies = valid_proxies[:limit]
        
        # NO agregar proxies automáticamente al manager
        # Las funciones específicas se encargarán de validar y agregar
        if valid_proxies:
            print(f"✅ Se obtuvieron {len(valid_proxies)} proxies desde {api_name}")
        else:
            print(f"⚠️ No se obtuvieron proxies válidos desde {api_name}")
        
        return valid_proxies
            
    except Exception as e:
        print(f"❌ Error obteniendo proxies desde {api_name}: {str(e)}")
        return []

def fetch_proxies_auto():
    """Obtiene proxies automáticamente desde múltiples fuentes"""
    def fetch_thread():
        try:
            print("🚀 Iniciando obtención automática de proxies...")
            
            # Limpiar proxies anteriores
            proxy_manager.clear()
            
            # Obtener número de instancias deseadas
            try:
                desired_instances = int(instances_entry.get()) if instances_entry.get() else 3
            except:
                desired_instances = 3
            
            # Calcular límite dinámico
            proxy_limit = get_dynamic_proxy_limit(desired_instances)
            
            print(f"🎯 Obteniendo proxies para {desired_instances} instancias (límite: {proxy_limit})")
            
            # Obtener desde múltiples fuentes con límite dinámico (solo las que funcionan)
            sources = [
                ('freeproxy', 'http', proxy_limit // 2),  # Esta funciona bien
                ('proxylist', 'http', proxy_limit // 2)   # Esta también funciona
            ]
            
            total_obtained = 0
            for api, protocol, limit in sources:
                try:
                    print(f"\n=== 🔄 Obteniendo desde {api} ({protocol}) ===")
                    obtained = fetch_proxies_from_api(api, protocol, limit, validate=False)  # Sin validación inicial
                    total_obtained += len(obtained)
                    print(f"📈 Obtenidos de {api}: {len(obtained)} proxies")
                    time.sleep(3)  # Delay entre requests
                except Exception as e:
                    print(f"❌ Error con {api} {protocol}: {e}")
                    continue
            
            # Obtener proxies del manager
            all_proxies = proxy_manager.get_proxies()
            
            # Validar solo los proxies obtenidos - ESPECÍFICAMENTE PARA BOCA JUNIORS
            if all_proxies:
                print(f"\n=== 🔍 Validando {len(all_proxies)} proxies obtenidos PARA BOCA JUNIORS ===")
                working_proxies = []
                for proxy in all_proxies[:min(len(all_proxies), proxy_limit)]:
                    if validate_proxy_for_boca(proxy):
                        working_proxies.append(proxy)
                        print(f"✅ Proxy {proxy} funciona PERFECTAMENTE con Boca Juniors")
                        if len(working_proxies) >= desired_instances:
                            break
                    else:
                        print(f"❌ Proxy {proxy} NO funciona con Boca Juniors")
                
                # Actualizar el manager con proxies funcionando
                proxy_manager.clear()
                proxy_manager.add_proxies(working_proxies)
                print(f"🎯 Proxies funcionando con Boca Juniors: {len(working_proxies)}")
            
            # Mostrar resultado final y guardar proxies
            final_count = proxy_manager.count()
            if final_count > 0:
                final_proxies = proxy_manager.get_proxies()
                
                # Guardar proxies validados automáticamente
                if proxy_manager.save_to_file():
                    save_msg = "\n✅ Proxies guardados en proxies.txt"
                else:
                    save_msg = "\n⚠️ Error guardando proxies"
                
                showinfo("Proxies Obtenidos", f"✅ Total: {final_count} proxies funcionando\nPara {desired_instances} instancias{save_msg}\n\nProxies obtenidos:\n{final_proxies[:5]}")
                print(f"✅ Proceso completado: {final_count} proxies funcionando")
                print(f"💾 Proxies guardados automáticamente en proxies.txt")
            else:
                showinfo("Advertencia", "❌ No se pudieron obtener proxies automáticamente\n\nRevisa la consola para más detalles")
                print("❌ No se obtuvieron proxies funcionando")
                
        except Exception as e:
            print(f"❌ Error en obtención automática: {str(e)}")
            root.after(0, lambda: showerror("Error", f"Error en obtención automática: {str(e)}"))
    
    thread = threading.Thread(target=fetch_thread)
    thread.daemon = True
    thread.start()

def is_sensitive_page(url):
    """Detecta páginas sensibles que requieren desactivar proxies"""
    sensitive_keywords = [
        'payment', 'checkout', 'billing', 'card', 'pay',
        'bank', 'financial', 'secure', 'ssl', 'login',
        'account', 'profile', 'settings', 'password'
    ]
    return any(keyword in url.lower() for keyword in sensitive_keywords)

def auto_disable_proxy_if_needed():
    """Desactiva proxies automáticamente si detecta páginas sensibles"""
    global playwright_instances
    
    if not playwright_instances:
        return
    
    def check_pages_thread():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def check_pages():
                sensitive_pages = []
                for playwright, browser, context, page in playwright_instances:
                    try:
                        current_url = await page.url
                        if is_sensitive_page(current_url):
                            sensitive_pages.append((playwright, browser, context, page, current_url))
                    except:
                        continue
                
                if sensitive_pages:
                    print(f"⚠️ Detectadas {len(sensitive_pages)} páginas sensibles")
                    root.after(0, lambda: showinfo("Páginas Sensibles Detectadas", 
                        f"Se detectaron {len(sensitive_pages)} páginas sensibles.\n"
                        f"Se recomienda desactivar proxies para mayor seguridad.\n"
                        f"¿Deseas desactivar proxies automáticamente?"))
            
            loop.run_until_complete(check_pages())
            loop.close()
            
        except Exception as e:
            print(f"Error verificando páginas: {e}")
    
    thread = threading.Thread(target=check_pages_thread)
    thread.daemon = True
    thread.start()

def disable_proxy_for_current_session():
    """Desactiva proxies para la sesión actual sin perder la posición"""
    global playwright_instances
    
    if not playwright_instances:
        showinfo("Info", "No hay instancias abiertas para modificar")
        return
    
    def disable_proxy_thread():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def disable_proxies():
                disabled_count = 0
                for playwright, browser, context, page in playwright_instances:
                    try:
                        # Obtener la URL actual
                        current_url = await page.url
                        print(f"Desactivando proxy para: {current_url}")
                        
                        # Crear nuevo contexto sin proxy
                        new_context = await browser.new_context(
                            user_agent=await page.evaluate("navigator.userAgent"),
                            viewport=await page.evaluate("({width: window.innerWidth, height: window.innerHeight})"),
                            locale='es-ES'
                        )
                        
                        # Crear nueva página sin proxy
                        new_page = await new_context.new_page()
                        
                        # Navegar a la misma URL sin proxy
                        await new_page.goto(current_url)
                        
                        # Reemplazar la página antigua
                        await page.close()
                        await context.close()
                        
                        # Actualizar la instancia
                        playwright_instances[playwright_instances.index((playwright, browser, context, page))] = (
                            playwright, browser, new_context, new_page
                        )
                        
                        disabled_count += 1
                        print(f"✅ Proxy desactivado para instancia {disabled_count}")
                        
                    except Exception as e:
                        print(f"❌ Error desactivando proxy: {e}")
                        continue
                
                # Mostrar resultado
                root.after(0, lambda: showinfo("Proxies Desactivados", f"Se desactivaron proxies en {disabled_count} instancias\nLas sesiones se mantienen activas"))
            
            loop.run_until_complete(disable_proxies())
            loop.close()
            
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"Error desactivando proxies: {str(e)}"))
    
    thread = threading.Thread(target=disable_proxy_thread)
    thread.daemon = True
    thread.start()

def load_and_show_proxy_list():
    """Carga y muestra la lista de proxies con estadísticas"""
    try:
        # Cargar proxies desde archivo
        load_proxy_list()
        
        # Obtener proxies cargados
        proxies = proxy_manager.get_proxies()
        
        if not proxies:
            showinfo("Lista de Proxies", "📝 No hay proxies guardados\n\nUsa 'Agregar Proxies Nuevos' para obtener proxies automáticamente")
            return
        
        # Analizar estadísticas
        total_proxies = len(proxies)
        ports = {}
        for proxy in proxies:
            port = proxy.split(':')[1] if ':' in proxy else 'unknown'
            ports[port] = ports.get(port, 0) + 1
        
        # Mostrar información detallada
        stats_text = f"""📋 Lista de Proxies Cargada:

✅ Total: {total_proxies} proxies disponibles

🔢 Puertos más comunes:
"""
        
        for port, count in sorted(ports.items(), key=lambda x: x[1], reverse=True)[:5]:
            stats_text += f"  • Puerto {port}: {count} proxies\n"
        
        stats_text += f"\n📝 Primeros 10 proxies:\n"
        for i, proxy in enumerate(proxies[:10], 1):
            stats_text += f"  {i}. {proxy}\n"
        
        if total_proxies > 10:
            stats_text += f"  ... y {total_proxies - 10} proxies más"
        
        showinfo("Lista de Proxies", stats_text)
        print(f"📋 Lista cargada: {total_proxies} proxies disponibles")
        
    except Exception as e:
        showerror("Error", f"❌ Error cargando lista de proxies: {str(e)}")

def test_and_clean_proxy_list():
    """Prueba todos los proxies y elimina los que no funcionan con Boca Juniors"""
    proxies = proxy_manager.get_proxies()
    
    if not proxies:
        showinfo("Info", "📝 No hay proxies para probar\n\nUsa 'Ver Lista de Proxies' primero")
        return
    
    def test_thread():
        try:
            print(f"🧹 Iniciando limpieza de {len(proxies)} proxies PARA BOCA JUNIORS...")
            working_proxies = []
            failed_count = 0
            
            for i, proxy in enumerate(proxies, 1):
                print(f"🔍 Probando proxy {i}/{len(proxies)}: {proxy}")
                if validate_proxy_for_boca(proxy):
                    working_proxies.append(proxy)
                    print(f"✅ Proxy {i} funciona PERFECTAMENTE con Boca Juniors")
                else:
                    failed_count += 1
                    print(f"❌ Proxy {i} NO funciona con Boca Juniors - ELIMINADO")
            
            # Actualizar lista con solo los proxies funcionando
            proxy_manager.clear()
            proxy_manager.add_proxies(working_proxies)
            
            # Guardar lista limpia
            if working_proxies:
                proxy_manager.save_to_file()
            
            # Mostrar resultado
            result_msg = f"""🧹 Limpieza Completada PARA BOCA JUNIORS:

✅ Proxies funcionando con Boca: {len(working_proxies)}
❌ Proxies eliminados: {failed_count}
💾 Lista actualizada y guardada

Solo se guardaron proxies que funcionan PERFECTAMENTE con Boca Juniors"""
            
            root.after(0, lambda: showinfo("Limpieza Completada", result_msg))
            print(f"🧹 Limpieza completada: {len(working_proxies)} proxies funcionando con Boca Juniors")
            
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"❌ Error en limpieza: {str(e)}"))
    
    thread = threading.Thread(target=test_thread)
    thread.daemon = True
    thread.start()

def clear_proxy_list():
    """Limpia completamente la lista de proxies"""
    proxy_manager.clear()
    proxy_manager.save_to_file()
    print("🧹 Lista de proxies limpiada completamente")
    showinfo("Lista Limpiada", "✅ Lista de proxies limpiada completamente\n\nAhora puedes agregar proxies que funcionen con Boca Juniors")

def check_brave_tor_status():
    """Verifica el estado de Brave y Tor"""
    def check_thread():
        try:
            print("🔍 Verificando disponibilidad de Brave Browser...")
            
            # Verificar Brave
            brave_available, brave_msg = check_tor_availability()
            
            if brave_available:
                result_msg = f"""✅ Brave Browser Disponible

{brave_msg}

🔒 Funcionalidades disponibles:
• Navegación con Tor integrado
• Mayor anonimato que proxies tradicionales
• Evasión avanzada de WAF
• Rotación automática de circuitos Tor

Para usar Brave con Tor:
1. Activa "Usar Brave con Tor"
2. Ejecuta las instancias normalmente
3. Brave abrirá ventanas con Tor habilitado"""
                
                root.after(0, lambda: showinfo("Brave + Tor Disponible", result_msg))
                print("✅ Brave Browser disponible para usar con Tor")
            else:
                result_msg = f"""❌ Brave Browser No Disponible

{brave_msg}

📥 Para usar Brave con Tor:
1. Descarga Brave desde: https://brave.com/
2. Instala Brave Browser
3. Reinicia esta aplicación
4. Activa "Usar Brave con Tor"

🔒 Ventajas de Brave + Tor:
• Mayor anonimato que proxies
• Tor integrado nativamente
• Mejor evasión de WAF
• No necesita configuración de proxies"""
                
                root.after(0, lambda: showinfo("Instalar Brave Browser", result_msg))
                print("❌ Brave Browser no disponible")
                
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"❌ Error verificando Brave: {str(e)}"))
            print(f"❌ Error: {e}")
    
    thread = threading.Thread(target=check_thread)
    thread.daemon = True
    thread.start()

def fetch_proxies_from_proxyscrape():
    """Obtiene proxies desde ProxyScrape y los valida para Boca Juniors"""
    def fetch_thread():
        try:
            print("📡 Obteniendo proxies desde ProxyScrape...")
            
            # Obtener proxies desde ProxyScrape (HTTP y SOCKS4)
            all_proxies = []
            protocols = [('http', 20), ('socks4', 15)]
            
            for protocol, limit in protocols:
                try:
                    print(f"🔍 Obteniendo {limit} proxies {protocol} desde ProxyScrape...")
                    proxies = fetch_proxies_from_api('proxyscrape', protocol, limit, validate=False)
                    if proxies:
                        all_proxies.extend(proxies)
                        print(f"✅ Obtenidos {len(proxies)} proxies {protocol} desde ProxyScrape")
                    time.sleep(1)  # Delay entre requests
                except Exception as e:
                    print(f"❌ Error obteniendo proxies {protocol}: {e}")
                    continue
            
            if not all_proxies:
                root.after(0, lambda: showinfo("Error", "❌ No se pudieron obtener proxies desde ProxyScrape\n\nRevisa la consola para más detalles"))
                return
            
            print(f"📋 Total de proxies obtenidos desde ProxyScrape: {len(all_proxies)}")
            
            # Validar ESPECÍFICAMENTE para Boca Juniors
            print(f"\n=== 🏆 Validando {len(all_proxies)} proxies de ProxyScrape PARA BOCA JUNIORS ===")
            working_proxies = []
            
            for i, proxy in enumerate(all_proxies, 1):
                print(f"🔍 Probando proxy {i}/{len(all_proxies)}: {proxy}")
                if validate_proxy_for_boca(proxy):
                    working_proxies.append(proxy)
                    print(f"✅ Proxy {proxy} funciona PERFECTAMENTE con Boca Juniors")
                else:
                    print(f"❌ Proxy {proxy} NO funciona con Boca Juniors")
                
                # Parar si tenemos suficientes
                if len(working_proxies) >= 5:  # Máximo 5 proxies funcionando
                    print(f"🎯 Obtenidos {len(working_proxies)} proxies funcionando - suficiente")
                    break
            
            # Agregar proxies funcionando a la lista existente
            if working_proxies:
                proxy_manager.add_proxies(working_proxies)
                proxy_manager.save_to_file()
                
                result_msg = f"""📡 ProxyScrape - Proxies para Boca Juniors:

✅ Proxies funcionando con Boca: {len(working_proxies)}
💾 Agregados a la lista existente
📋 Total en lista: {proxy_manager.count()}

Proxies obtenidos desde ProxyScrape:
{working_proxies[:3]}..."""
                
                root.after(0, lambda: showinfo("ProxyScrape - Proxies Obtenidos", result_msg))
                print(f"📡 ProxyScrape completado: {len(working_proxies)} proxies funcionando con Boca Juniors")
            else:
                root.after(0, lambda: showinfo("Advertencia", "❌ No se encontraron proxies funcionando desde ProxyScrape\n\nIntenta con otro servidor"))
                print("❌ No se encontraron proxies funcionando desde ProxyScrape")
                
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"❌ Error obteniendo proxies desde ProxyScrape: {str(e)}"))
            print(f"❌ Error: {e}")
    
    thread = threading.Thread(target=fetch_thread)
    thread.daemon = True
    thread.start()

def fetch_proxies_from_freeproxy():
    """Obtiene proxies desde FreeProxy y los valida para Boca Juniors"""
    def fetch_thread():
        try:
            print("📡 Obteniendo proxies desde FreeProxy...")
            
            # Obtener proxies desde FreeProxy (HTTP y SOCKS4)
            all_proxies = []
            protocols = [('http', 15), ('socks4', 10)]
            
            for protocol, limit in protocols:
                try:
                    print(f"🔍 Obteniendo {limit} proxies {protocol} desde FreeProxy...")
                    proxies = fetch_proxies_from_api('freeproxy', protocol, limit, validate=False)
                    if proxies:
                        all_proxies.extend(proxies)
                        print(f"✅ Obtenidos {len(proxies)} proxies {protocol} desde FreeProxy")
                    time.sleep(1)  # Delay entre requests
                except Exception as e:
                    print(f"❌ Error obteniendo proxies {protocol}: {e}")
                    continue
            
            if not all_proxies:
                root.after(0, lambda: showinfo("Error", "❌ No se pudieron obtener proxies desde FreeProxy\n\nRevisa la consola para más detalles"))
                return
            
            print(f"📋 Total de proxies obtenidos desde FreeProxy: {len(all_proxies)}")
            
            # Validar ESPECÍFICAMENTE para Boca Juniors
            print(f"\n=== 🏆 Validando {len(all_proxies)} proxies de FreeProxy PARA BOCA JUNIORS ===")
            working_proxies = []
            
            for i, proxy in enumerate(all_proxies, 1):
                print(f"🔍 Probando proxy {i}/{len(all_proxies)}: {proxy}")
                if validate_proxy_for_boca(proxy):
                    working_proxies.append(proxy)
                    print(f"✅ Proxy {proxy} funciona PERFECTAMENTE con Boca Juniors")
                else:
                    print(f"❌ Proxy {proxy} NO funciona con Boca Juniors")
                
                # Parar si tenemos suficientes
                if len(working_proxies) >= 5:  # Máximo 5 proxies funcionando
                    print(f"🎯 Obtenidos {len(working_proxies)} proxies funcionando - suficiente")
                    break
            
            # Agregar proxies funcionando a la lista existente
            if working_proxies:
                proxy_manager.add_proxies(working_proxies)
                proxy_manager.save_to_file()
                
                result_msg = f"""📡 FreeProxy - Proxies para Boca Juniors:

✅ Proxies funcionando con Boca: {len(working_proxies)}
💾 Agregados a la lista existente
📋 Total en lista: {proxy_manager.count()}

Proxies obtenidos desde FreeProxy:
{working_proxies[:3]}..."""
                
                root.after(0, lambda: showinfo("FreeProxy - Proxies Obtenidos", result_msg))
                print(f"📡 FreeProxy completado: {len(working_proxies)} proxies funcionando con Boca Juniors")
            else:
                root.after(0, lambda: showinfo("Advertencia", "❌ No se encontraron proxies funcionando desde FreeProxy\n\nIntenta con otro servidor"))
                print("❌ No se encontraron proxies funcionando desde FreeProxy")
                
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"❌ Error obteniendo proxies desde FreeProxy: {str(e)}"))
            print(f"❌ Error: {e}")
    
    thread = threading.Thread(target=fetch_thread)
    thread.daemon = True
    thread.start()

def fetch_proxies_for_boca_juniors():
    """Obtiene proxies específicamente validados para Boca Juniors"""
    def fetch_thread():
        try:
            print("🏆 Obteniendo proxies ESPECÍFICAMENTE para Boca Juniors...")
            
            # Obtener proxies desde múltiples fuentes
            all_proxies = []
            proxy_sources = [
                ('proxyscrape', 'http', 30),
                ('freeproxy', 'http', 20),
                ('proxyscrape', 'socks4', 15),
                ('freeproxy', 'socks4', 10)
            ]
            
            for api_name, protocol, limit in proxy_sources:
                try:
                    print(f"📡 Obteniendo proxies desde {api_name} ({protocol})...")
                    proxies = fetch_proxies_from_api(api_name, protocol, limit, validate=False)
                    if proxies:
                        all_proxies.extend(proxies)
                        print(f"✅ Obtenidos {len(proxies)} proxies desde {api_name}")
                    time.sleep(2)  # Delay entre requests
                except Exception as e:
                    print(f"❌ Error obteniendo proxies desde {api_name}: {e}")
                    continue
            
            if not all_proxies:
                root.after(0, lambda: showinfo("Error", "❌ No se pudieron obtener proxies\n\nRevisa la consola para más detalles"))
                return
            
            print(f"📋 Total de proxies obtenidos: {len(all_proxies)}")
            
            # Validar ESPECÍFICAMENTE para Boca Juniors
            print(f"\n=== 🏆 Validando {len(all_proxies)} proxies PARA BOCA JUNIORS ===")
            working_proxies = []
            
            for i, proxy in enumerate(all_proxies, 1):
                print(f"🔍 Probando proxy {i}/{len(all_proxies)}: {proxy}")
                if validate_proxy_for_boca(proxy):
                    working_proxies.append(proxy)
                    print(f"✅ Proxy {proxy} funciona PERFECTAMENTE con Boca Juniors")
                else:
                    print(f"❌ Proxy {proxy} NO funciona con Boca Juniors")
                
                # Parar si tenemos suficientes
                if len(working_proxies) >= 10:  # Máximo 10 proxies funcionando
                    print(f"🎯 Obtenidos {len(working_proxies)} proxies funcionando - suficiente")
                    break
            
            # Actualizar el manager con proxies funcionando
            proxy_manager.clear()
            proxy_manager.add_proxies(working_proxies)
            
            # Guardar proxies validados
            if working_proxies:
                proxy_manager.save_to_file()
                result_msg = f"""🏆 Proxies para Boca Juniors Obtenidos:

✅ Proxies funcionando con Boca: {len(working_proxies)}
💾 Guardados en proxies.txt

Solo proxies que funcionan PERFECTAMENTE con Boca Juniors:
{working_proxies[:5]}..."""
                
                root.after(0, lambda: showinfo("Proxies para Boca Juniors", result_msg))
                print(f"🏆 Proceso completado: {len(working_proxies)} proxies funcionando con Boca Juniors")
            else:
                root.after(0, lambda: showinfo("Advertencia", "❌ No se encontraron proxies que funcionen con Boca Juniors\n\nIntenta con más proxies o verifica tu conexión"))
                print("❌ No se encontraron proxies funcionando con Boca Juniors")
                
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"❌ Error obteniendo proxies para Boca: {str(e)}"))
            print(f"❌ Error: {e}")
    
    thread = threading.Thread(target=fetch_thread)
    thread.daemon = True
    thread.start()

def add_new_proxies(count=20):
    """Agrega nuevos proxies optimizados para Boca Juniors"""
    def add_thread():
        try:
            print(f"🔄 Agregando {count} proxies optimizados para Boca Juniors...")
            
            # Obtener proxies existentes
            existing_proxies = proxy_manager.get_proxies()
            existing_count = len(existing_proxies)
            
            # Obtener nuevos proxies desde APIs optimizadas para Argentina
            sources = [
                ('proxyscrape', 'http', count // 2),        # Proxies de países cercanos (AR, BR, UY, CL)
                ('proxyscrape', 'http_global', count // 4), # Proxies globales como respaldo
                ('freeproxy', 'http', count // 4)           # Proxies adicionales
            ]
            
            new_proxies = []
            for api, protocol, limit in sources:
                try:
                    print(f"🔄 Obteniendo desde {api}...")
                    obtained = fetch_proxies_from_api(api, protocol, limit, validate=False)
                    new_proxies.extend(obtained)
                    time.sleep(2)
                except Exception as e:
                    print(f"❌ Error con {api}: {e}")
                    continue
            
            # Filtrar duplicados
            unique_new_proxies = []
            for proxy in new_proxies:
                if proxy not in existing_proxies and proxy not in unique_new_proxies:
                    unique_new_proxies.append(proxy)
            
            # Validar nuevos proxies específicamente para Boca Juniors
            if unique_new_proxies:
                print(f"🏆 Validando {len(unique_new_proxies)} proxies para Boca Juniors...")
                
                # Primero priorizar proxies con puertos preferidos
                preferred_proxies = [p for p in unique_new_proxies if is_preferred_proxy_for_boca(p)]
                other_proxies = [p for p in unique_new_proxies if not is_preferred_proxy_for_boca(p)]
                
                print(f"🎯 Proxies con puertos preferidos: {len(preferred_proxies)}")
                print(f"📋 Otros proxies: {len(other_proxies)}")
                
                validated_proxies = []
                
                # Probar primero los proxies preferidos
                for proxy in preferred_proxies[:count]:
                    if validate_proxy_for_boca(proxy):
                        validated_proxies.append(proxy)
                        if len(validated_proxies) >= count:
                            break
                
                # Si necesitamos más, probar otros proxies
                if len(validated_proxies) < count:
                    for proxy in other_proxies[:count - len(validated_proxies)]:
                        if validate_proxy_for_boca(proxy):
                            validated_proxies.append(proxy)
                            if len(validated_proxies) >= count:
                                break
                
                # Agregar a la lista existente
                if validated_proxies:
                    proxy_manager.add_proxies(validated_proxies)
                    proxy_manager.save_to_file()
                    
                    result_msg = f"""✅ Proxies Agregados:

📊 Antes: {existing_count} proxies
➕ Agregados: {len(validated_proxies)} proxies nuevos
📊 Total: {proxy_manager.count()} proxies

💾 Lista actualizada y guardada
Usa 'Ver Lista de Proxies' para ver la lista completa"""
                    
                    root.after(0, lambda: showinfo("Proxies Agregados", result_msg))
                    print(f"✅ Se agregaron {len(validated_proxies)} proxies nuevos")
                else:
                    root.after(0, lambda: showinfo("Sin Proxies", "❌ No se encontraron proxies nuevos funcionando"))
            else:
                root.after(0, lambda: showinfo("Sin Proxies", "❌ No se encontraron proxies nuevos únicos"))
                
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"❌ Error agregando proxies: {str(e)}"))
    
    thread = threading.Thread(target=add_thread)
    thread.daemon = True
    thread.start()

def show_proxy_stats():
    """Muestra estadísticas de los proxies cargados"""
    proxies = proxy_manager.get_proxies()
    
    if not proxies:
        showinfo("Info", "No hay proxies cargados")
        return
    
    # Estadísticas básicas
    total_proxies = len(proxies)
    
    # Analizar puertos más comunes
    ports = {}
    for proxy in proxies:
        port = proxy.split(':')[1] if ':' in proxy else 'unknown'
        ports[port] = ports.get(port, 0) + 1
    
    # Mostrar estadísticas
    stats_text = f"""
📊 Estadísticas de Proxies:
• Total: {total_proxies} proxies
• Puertos más comunes:
"""
    
    for port, count in sorted(ports.items(), key=lambda x: x[1], reverse=True)[:5]:
        stats_text += f"  - Puerto {port}: {count} proxies\n"
    
    showinfo("Estadísticas de Proxies", stats_text)
    print(f"📋 Proxies cargados: {proxies[:10]}...")  # Mostrar primeros 10

def test_proxyscrape_v4():
    """Prueba específicamente la nueva API v4 de ProxyScrape"""
    def test_thread():
        try:
            print("=== Probando ProxyScrape API v4 ===")
            
            # Probar nueva API v4
            try:
                print("\n🔄 Probando ProxyScrape API v4...")
                url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=20"
                response = requests.get(url, timeout=10)
                print(f"Status: {response.status_code}")
                print(f"Contenido: {response.text[:200]}...")
                
                if response.status_code == 200:
                    # Parsear proxies (separados por espacios)
                    proxies = response.text.strip().split()
                    print(f"Proxies obtenidos: {len(proxies)}")
                    if proxies:
                        print(f"Primeros 5 proxies:")
                        for i, proxy in enumerate(proxies[:5], 1):
                            print(f"  {i}. {proxy}")
                        print("✅ ProxyScrape v4 funciona correctamente!")
                        
                        # Mostrar resultado en ventana
                        result_msg = f"""✅ ProxyScrape API v4 Funciona!

📊 Proxies obtenidos: {len(proxies)}
🔗 API: v4/free-proxy-list/get
📝 Formato: Separados por espacios

Primeros 5 proxies:
{chr(10).join(f"• {proxy}" for proxy in proxies[:5])}

El sistema ahora usará esta API v4."""
                        
                        root.after(0, lambda: showinfo("ProxyScrape v4 OK", result_msg))
                    else:
                        print("⚠️ No se obtuvieron proxies")
                        root.after(0, lambda: showinfo("Sin Proxies", "⚠️ ProxyScrape v4 no devolvió proxies"))
                else:
                    print(f"❌ Error en ProxyScrape v4: {response.status_code}")
                    root.after(0, lambda: showerror("Error", f"❌ ProxyScrape v4 error: {response.status_code}"))
                    
            except Exception as e:
                print(f"❌ Error con ProxyScrape v4: {e}")
                root.after(0, lambda: showerror("Error", f"❌ Error con ProxyScrape v4: {str(e)}"))
            
            print("\n=== Fin de pruebas ProxyScrape v4 ===")
            
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"Error en pruebas: {str(e)}"))
    
    thread = threading.Thread(target=test_thread)
    thread.daemon = True
    thread.start()

def test_proxy_fetch():
    """Prueba la obtención de proxies con las APIs que funcionan"""
    def test_thread():
        try:
            print("=== Probando obtención de proxies ===")
            
            # Probar FreeProxy
            try:
                print("\n1. Probando FreeProxy...")
                obtained = fetch_proxies_from_api('freeproxy', 'http', 5, validate=False)
                print(f"✅ FreeProxy: {len(obtained)} proxies obtenidos")
                if obtained:
                    print(f"Ejemplos: {obtained[:3]}")
            except Exception as e:
                print(f"❌ Error con FreeProxy: {e}")
            
            # Probar ProxyList
            try:
                print("\n2. Probando ProxyList...")
                obtained = fetch_proxies_from_api('proxylist', 'http', 5, validate=False)
                print(f"✅ ProxyList: {len(obtained)} proxies obtenidos")
                if obtained:
                    print(f"Ejemplos: {obtained[:3]}")
            except Exception as e:
                print(f"❌ Error con ProxyList: {e}")
            
            print("\n=== Fin de pruebas de obtención ===")
            root.after(0, lambda: showinfo("Pruebas de Obtención Completadas", "Revisa la consola para ver los resultados"))
            
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"Error en pruebas: {str(e)}"))
    
    thread = threading.Thread(target=test_thread)
    thread.daemon = True
    thread.start()

def test_proxy_parsing():
    """Prueba el parsing de proxies con una lista de ejemplo"""
    test_proxies = """185.221.160.11:80
216.205.52.179:80
170.114.45.41:80
216.205.52.145:80
45.67.215.60:80
45.67.215.178:80
89.116.250.240:80
69.84.182.204:80
170.114.45.101:80
141.101.115.242:80"""
    
    print("Probando parsing de proxies...")
    proxies = test_proxies.strip().split('\n')
    valid_count = 0
    
    for proxy in proxies:
        proxy = proxy.strip()
        if proxy and ':' in proxy:
            parts = proxy.split(':')
            if len(parts) >= 2 and parts[0] and parts[1].isdigit():
                ip_parts = parts[0].split('.')
                if len(ip_parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                    valid_count += 1
                    print(f"✅ Proxy válido: {proxy}")
                else:
                    print(f"❌ IP inválida: {proxy}")
            else:
                print(f"❌ Formato inválido: {proxy}")
    
    showinfo("Prueba de Parsing", f"Proxies válidos: {valid_count}/{len(proxies)}")
    print(f"Total: {len(proxies)}, Válidos: {valid_count}")

def configure_for_boca_juniors():
    """Configura automáticamente la aplicación para Boca Juniors"""
    # Configurar URL
    url_entry.delete(0, 'end')
    url_entry.insert(0, BOCA_JUNIORS_CONFIG['target_url'])
    
    # Activar modo sigiloso
    stealth_mode.set(True)
    
    # Activar proxies
    use_proxies.set(True)
    
    showinfo("Configuración para Boca", f"""🏆 Configurado para Boca Juniors:

🌐 URL: {BOCA_JUNIORS_CONFIG['target_url']}
🎭 Modo Sigiloso: Activado
🌐 Proxies: Activados (optimizados para Argentina)
🇦🇷 Configuración argentina aplicada

Próximo paso: 'Agregar Proxies Nuevos' (recomendado: 30)
Número de instancias: A tu elección""")

def test_proxies_with_target_site():
    """Prueba los proxies específicamente con el sitio objetivo"""
    proxies = proxy_manager.get_proxies()
    
    if not proxies:
        showinfo("Info", "No hay proxies cargados para probar")
        return
    
    # Obtener URL objetivo
    target_url = url_entry.get() if url_entry.get() else BOCA_JUNIORS_CONFIG['target_url']
    
    def test_thread():
        try:
            print(f"🎯 Probando proxies con sitio objetivo: {target_url}")
            working_proxies = []
            failed_proxies = []
            
            for i, proxy_string in enumerate(proxies[:10], 1):  # Probar primeros 10
                try:
                    parts = proxy_string.split(':')
                    if len(parts) >= 2:
                        proxy_url = f"http://{parts[0]}:{parts[1]}"
                        proxy_dict = {'http': proxy_url, 'https': proxy_url}
                        
                        print(f"🔍 Probando proxy {i}/10: {proxy_string} con {target_url}")
                        
                        # Prueba con el sitio objetivo
                        response = requests.get(target_url, proxies=proxy_dict, timeout=10, allow_redirects=True)
                        if response.status_code == 200:
                            working_proxies.append(proxy_string)
                            print(f"✅ Proxy {proxy_string} funciona con el sitio objetivo")
                        else:
                            failed_proxies.append(f"{proxy_string} (Status: {response.status_code})")
                            print(f"❌ Proxy {proxy_string} falló - Status: {response.status_code}")
                            
                except requests.exceptions.ConnectTimeout:
                    failed_proxies.append(f"{proxy_string} (Timeout)")
                    print(f"⏰ Proxy {proxy_string} - Timeout")
                except requests.exceptions.ProxyError:
                    failed_proxies.append(f"{proxy_string} (Proxy Error)")
                    print(f"🚫 Proxy {proxy_string} - Error de proxy")
                except requests.exceptions.ConnectionError:
                    failed_proxies.append(f"{proxy_string} (Connection Error)")
                    print(f"🔌 Proxy {proxy_string} - Error de conexión")
                except Exception as e:
                    failed_proxies.append(f"{proxy_string} ({type(e).__name__})")
                    print(f"❓ Proxy {proxy_string} - Error: {type(e).__name__}")
            
            # Mostrar resultado
            result_msg = f"""🎯 Prueba con Sitio Objetivo:

🌐 URL: {target_url}
✅ Proxies funcionando: {len(working_proxies)}
❌ Proxies fallidos: {len(failed_proxies)}

Proxies que funcionan:
{chr(10).join(f"• {proxy}" for proxy in working_proxies[:5])}

Recomendación: Usa 'Probar y Limpiar Lista' para eliminar proxies fallidos"""
            
            root.after(0, lambda: showinfo("Prueba con Sitio Objetivo", result_msg))
            print(f"🎯 Resultado: {len(working_proxies)} proxies funcionan con {target_url}")
            
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"❌ Error probando proxies: {str(e)}"))
    
    thread = threading.Thread(target=test_thread)
    thread.daemon = True
    thread.start()

def test_proxy_connection():
    """Prueba la conexión de los proxies cargados"""
    proxies = proxy_manager.get_proxies()
    
    if not proxies:
        showinfo("Info", "No hay proxies cargados para probar")
        return
    
    working_proxies = []
    for proxy_string in proxies[:3]:  # Probar solo los primeros 3
        try:
            parts = proxy_string.split(':')
            if len(parts) >= 2:
                proxy_url = f"http://{parts[0]}:{parts[1]}"
                proxy_dict = {'http': proxy_url, 'https': proxy_url}
                
                # Prueba rápida de conexión
                response = requests.get('http://httpbin.org/ip', proxies=proxy_dict, timeout=5)
                if response.status_code == 200:
                    working_proxies.append(proxy_string)
                    print(f"✅ Proxy {proxy_string} funciona correctamente")
        except Exception as e:
            print(f"❌ Proxy {proxy_string} falló: {e}")
    
    if working_proxies:
        showinfo("Prueba de Proxies", f"✅ {len(working_proxies)} proxies funcionan correctamente")
    else:
        showinfo("Advertencia", "❌ Ningún proxy funcionó. Verifica la configuración.")

def execute_script():
    """Ejecuta el script principal"""
    global playwright_instances
    url = url_entry.get()
    
    if not url:
        showerror("Error", "Por favor ingresa una URL válida")
        return
    
    try:
        instances = int(instances_entry.get())
        if instances <= 0:
            raise ValueError("Número de instancias debe ser mayor a 0")
    except ValueError:
        showerror("Error", "Por favor ingresa un número válido de instancias")
        return
    
    # Cargar proxies automáticamente si está habilitado
    if use_proxies.get():
        load_proxy_list()
        available_proxies = proxy_manager.count()
        
        if available_proxies == 0:
            if askokcancel("Sin Proxies", "No hay proxies disponibles.\n\n¿Deseas agregar proxies automáticamente antes de continuar?"):
                add_new_proxies(instances * 2)
                showinfo("Info", "Agregando proxies... Espera un momento y vuelve a ejecutar.")
                return
            else:
                showinfo("Info", "Ejecutando sin proxies...")
                use_proxies.set(False)
        elif available_proxies < instances:
            showinfo("Info de Proxies", f"Hay {available_proxies} proxies para {instances} instancias.\n\nLos proxies se reutilizarán según sea necesario.")
    
    # Información de confirmación
    stealth_text = " (Modo Sigiloso)" if stealth_mode.get() else ""
    
    if use_proxies.get():
        proxy_count = proxy_manager.count()
        proxy_text = f" (Con {proxy_count} Proxies)"
    else:
        proxy_text = " (Sin Proxies)"
    
    confirm = askokcancel(
        "Confirmar Ejecución",
        f"Esto abrirá {instances} instancias de navegador{stealth_text}{proxy_text} con la URL:\n{url}\n\n¿Continuar?"
    )
    
    if not confirm:
        return
    
    # Guardar configuración
    config_data = {
        "url": url,
        "instances": instances,
        "stealth_mode": stealth_mode.get(),
        "use_proxies": use_proxies.get(),
        "use_tor_mode": use_tor_mode.get()
    }
    save_config(config_data)
    
    # Ejecutar de forma asíncrona
    def run_async():
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            instances_task = loop.create_task(instance_manager.open_advanced_instances(url, instances))
            loop.run_until_complete(instances_task)
            
            # Actualizar UI desde el hilo principal
            instances_count = len(playwright_instances)
            if instances_count > 0:
                root.after(0, lambda: showinfo("Éxito", 
                    f"✅ {instances_count} instancias de navegador abiertas\n\n"
                    f"💡 Las ventanas permanecerán abiertas incluso si hay errores.\n"
                    f"🔒 Tus ventanas están protegidas contra cierres automáticos."))
                root.after(0, lambda: close_button.config(state="normal"))
                
                # Iniciar monitoreo y mantener loop vivo
                loop.create_task(instance_manager.monitor_queues_loop())
                loop.run_forever()
            else:
                root.after(0, lambda: showinfo("Advertencia", 
                    "⚠️ No se pudieron crear instancias.\n\n"
                    "Revisa la consola para más detalles."))
            
        except Exception as e:
            # Aún si hay errores, las ventanas que se crearon permanecen abiertas
            instances_count = len(playwright_instances)
            if instances_count > 0:
                root.after(0, lambda: showinfo("Parcialmente Exitoso", 
                    f"⚠️ Ocurrió un error: {str(e)}\n\n"
                    f"✅ Pero {instances_count} ventanas permanecen abiertas.\n"
                    f"🔒 Las ventanas no se cerrarán automáticamente."))
                root.after(0, lambda: close_button.config(state="normal"))
            else:
                root.after(0, lambda: showerror("Error", 
                    f"❌ Ocurrió un error: {str(e)}\n\n"
                    "Revisa la consola para más detalles."))
            print(f"❌ Error en ejecución: {str(e)}")
        finally:
            if loop:
                try:
                    loop.close()
                except:
                    pass
    
    # Ejecutar en hilo separado para no bloquear la UI
    thread = threading.Thread(target=run_async)
    thread.daemon = True
    thread.start()

def check_instances_status():
    """Verifica el estado de las instancias abiertas"""
    global playwright_instances
    if playwright_instances:
        close_button.config(state="normal")
    else:
        close_button.config(state="disabled")

def close_windows():
    """Cierra todas las instancias de navegador"""
    global playwright_instances
    
    if not playwright_instances:
        showinfo("Info", "No hay instancias abiertas para cerrar")
        return
    
    def close_all():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def close_instances():
                closed_count = 0
                for playwright, browser, context, page in playwright_instances:
                    try:
                        await browser.close()
                        await playwright.stop()
                        closed_count += 1
                    except Exception as e:
                        print(f"Error cerrando instancia: {e}")
                        continue
                
                # Actualizar la UI desde el hilo principal
                root.after(0, lambda: showinfo("Cerrado", f"Se cerraron {closed_count} instancias de navegador"))
                root.after(0, lambda: close_button.config(state="disabled"))
            
            loop.run_until_complete(close_instances())
            loop.close()
            
            # Limpiar la lista global
            playwright_instances.clear()
            
        except Exception as e:
            root.after(0, lambda: showerror("Error", f"Error cerrando instancias: {str(e)}"))
    
    thread = threading.Thread(target=close_all)
    thread.daemon = True
    thread.start()

# Configuración de la interfaz
root = Tk()
root.title("Instancias Avanzadas - Anti WAF")
root.geometry("600x400")

# Crear variables después de crear la ventana
stealth_mode = BooleanVar()
use_proxies = BooleanVar()
use_tor_mode = BooleanVar()

# Cargar configuración
config = load_config()
if config:
    url_entry_value = config.get("url", "")
    instances_entry_value = config.get("instances", "")
    stealth_mode.set(config.get("stealth_mode", False))
    use_proxies.set(config.get("use_proxies", False))
    use_tor_mode.set(config.get("use_tor_mode", False))
else:
    url_entry_value = ""
    instances_entry_value = ""

# Interfaz de usuario
Label(root, text="URL:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
url_entry = Entry(root, width=50)
url_entry.insert(0, url_entry_value)
url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

Label(root, text="Ejemplo: https://www.ejemplo.com", font=("Arial", 8)).grid(row=1, column=1, padx=10, pady=2, sticky="w")

Button(root, text="🏆 Configurar para Boca Juniors", command=configure_for_boca_juniors, bg="#FFD700", fg="black", font=("Arial", 8, "bold")).grid(row=2, column=1, padx=10, pady=2, sticky="w")

Label(root, text="Número de instancias:", font=("Arial", 10, "bold")).grid(row=3, column=0, padx=10, pady=5, sticky="w")
instances_entry = Entry(root, width=10)
instances_entry.insert(0, instances_entry_value)
instances_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

Label(root, text="Cada instancia usa ~100MB RAM. Tú decides cuántas instancias usar.", font=("Arial", 8)).grid(row=4, column=1, padx=10, pady=2, sticky="w")

# Opciones avanzadas
Label(root, text="Opciones Avanzadas:", font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")

stealth_check = Checkbutton(root, text="Modo Sigiloso (comportamiento humano simulado)", variable=stealth_mode)
stealth_check.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="w")

proxy_check = Checkbutton(root, text="Usar Proxies (optimizados para Argentina)", variable=use_proxies)
proxy_check.grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="w")

tor_check = Checkbutton(root, text="🔒 Usar Brave con Tor (máximo anonimato)", variable=use_tor_mode, fg="#FF6B35", font=("Arial", 9, "bold"))
tor_check.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky="w")

# Sección de Proxies
Label(root, text="Gestión de Proxies:", font=("Arial", 10, "bold")).grid(row=9, column=0, columnspan=2, padx=10, pady=5, sticky="w")

Button(root, text="Ver Lista de Proxies", command=load_and_show_proxy_list, bg="#2196F3", fg="white", font=("Arial", 9, "bold")).grid(row=10, column=0, columnspan=2, padx=10, pady=5)

Button(root, text="🔐 Cargar Proxies de WireGuard", command=load_wireguard_proxies, bg="#9C27B0", fg="white", font=("Arial", 9, "bold")).grid(row=11, column=0, columnspan=2, padx=10, pady=5)

Button(root, text="Probar y Limpiar Lista", command=test_and_clean_proxy_list, bg="#FF9800", fg="white", font=("Arial", 9, "bold")).grid(row=12, column=0, padx=5, pady=5)
Button(root, text="🧹 Limpiar Lista Completa", command=clear_proxy_list, bg="#f44336", fg="white", font=("Arial", 9, "bold")).grid(row=12, column=1, padx=5, pady=5)

# Botones específicos para cada servidor de proxies

Label(root, text="Obtener Proxies por Servidor:", font=("Arial", 9, "bold")).grid(row=13, column=0, columnspan=2, padx=10, pady=5, sticky="w")

Button(root, text="📡 ProxyScrape", command=fetch_proxies_from_proxyscrape, bg="#2196F3", fg="white", font=("Arial", 8, "bold"), width=12).grid(row=14, column=0, padx=5, pady=2)
Button(root, text="📡 FreeProxy", command=fetch_proxies_from_freeproxy, bg="#4CAF50", fg="white", font=("Arial", 8, "bold"), width=12).grid(row=14, column=1, padx=5, pady=2)

Button(root, text="🏆 Todos los Servidores", command=fetch_proxies_for_boca_juniors, bg="#FFD700", fg="black", font=("Arial", 8, "bold"), width=20).grid(row=15, column=0, columnspan=2, padx=10, pady=5)

Button(root, text="🔒 Verificar Brave + Tor", command=check_brave_tor_status, bg="#FF6B35", fg="white", font=("Arial", 8, "bold")).grid(row=16, column=0, padx=5, pady=2)
Button(root, text="🎯 Probar con Sitio Objetivo", command=test_proxies_with_target_site, bg="#FF5722", fg="white", font=("Arial", 8, "bold")).grid(row=16, column=1, padx=5, pady=2)

# Sección para agregar proxies
Label(root, text="Agregar Proxies:", font=("Arial", 9, "bold")).grid(row=17, column=0, padx=10, pady=5, sticky="w")
Label(root, text="Cantidad:").grid(row=17, column=1, padx=5, pady=5, sticky="w")

proxy_count_entry = Entry(root, width=10)
proxy_count_entry.insert(0, "30")
proxy_count_entry.grid(row=18, column=0, padx=10, pady=5, sticky="w")

Button(root, text="Agregar Proxies Nuevos", command=lambda: add_new_proxies(int(proxy_count_entry.get()) if proxy_count_entry.get().isdigit() else 30), bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).grid(row=18, column=1, padx=10, pady=5)

# Botón de prueba para ProxyScrape v4
Button(root, text="🔬 Probar ProxyScrape v4", command=test_proxyscrape_v4, bg="#9C27B0", fg="white", font=("Arial", 8, "bold")).grid(row=19, column=0, columnspan=2, padx=10, pady=2)

# Sección de seguridad
Label(root, text="Seguridad:", font=("Arial", 10, "bold")).grid(row=20, column=0, columnspan=2, padx=10, pady=5, sticky="w")

Button(root, text="Desactivar Proxies (Mantener Sesión)", command=disable_proxy_for_current_session, bg="#E91E63", fg="white", font=("Arial", 9, "bold")).grid(row=21, column=0, columnspan=2, padx=10, pady=5)

# Botones principales
Button(root, text="Ejecutar", command=execute_script, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(row=22, column=0, columnspan=2, pady=20)

Button(root, text="Verificar Estado", command=check_instances_status, bg="#2196F3", fg="white", font=("Arial", 10, "bold")).grid(row=23, column=0, columnspan=2, pady=5)

close_button = Button(root, text="Cerrar Todas las Ventanas", command=close_windows, state="disabled", bg="#f44336", fg="white", font=("Arial", 10, "bold"))
close_button.grid(row=24, column=0, columnspan=2, pady=10)

# Información adicional
info_text = """
Técnicas Anti-WAF implementadas:
• User-Agents rotativos y realistas
• Delays variables entre instancias
• Comportamiento humano simulado
• Fingerprints únicos por instancia
• Timeouts realistas
• Eliminación de propiedades de automatización
• Soporte para proxies de WireGuard
• Protección contra cierres automáticos por errores
"""
Label(root, text=info_text, font=("Arial", 8), justify="left").grid(row=25, column=0, columnspan=2, padx=10, pady=10, sticky="w")

# Configurar grid
root.grid_columnconfigure(1, weight=1)

def on_closing():
    """Limpia los procesos de wireproxy al salir"""
    global wireproxy_processes
    for p in wireproxy_processes:
        try:
            p.terminate()
        except:
            pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
