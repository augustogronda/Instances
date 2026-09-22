# -*- coding: utf-8 -*-
import os
import re
import json
import time
import queue
import threading
import datetime
import tkinter as tk
from tkinter.messagebox import askokcancel, showinfo, showerror
import undetected_chromedriver as uc

# ═══════════════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════════════
BG_DARK      = "#0D1117"
BG_CARD      = "#161B22"
BG_HEADER    = "#0D1117"
BG_URGENT    = "#1F1500"
BG_ENTER     = "#0D1F12"
BG_ERROR     = "#1F0D0D"
BG_OPEN      = "#0D1520"

ACCENT       = "#F0B323"
TEXT_PRIMARY = "#E6EDF3"
TEXT_MUTED   = "#8B949E"
GREEN        = "#3FB950"
YELLOW       = "#D29922"
RED          = "#F85149"
BLUE         = "#58A6FF"
BORDER       = "#21262D"

FONT         = "Segoe UI"

# ═══════════════════════════════════════════════════════════════════
#  PATHS (siempre relativo al script, no al CWD)          FIX #5
# ═══════════════════════════════════════════════════════════════════
_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "config.json")

# ═══════════════════════════════════════════════════════════════════
#  GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════
chrome_instances: list  = []
instance_data:    dict  = {}   # idx -> {time_left, status, urgent, error}
dashboard_win           = None
_monitor_after_id       = None  # para cancelar el bucle anterior  FIX #2
_ui_queue: queue.Queue  = queue.Queue()  # thread → main thread     FIX #6

# ═══════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════
def save_config(data: dict):
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        showerror("Error", f"Error guardando config: {e}")

def load_config() -> dict | None:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        showerror("Error", f"Error cargando config: {e}")
    return None

# ═══════════════════════════════════════════════════════════════════
#  UI QUEUE — comunicación thread → tkinter                FIX #6
# ═══════════════════════════════════════════════════════════════════
def _poll_ui_queue():
    """Drena la cola de mensajes del thread secundario cada 200 ms."""
    try:
        while True:
            msg = _ui_queue.get_nowait()
            action = msg.get("action")
            if action == "refresh_card" and dashboard_win:
                dashboard_win.refresh_card(msg["idx"])
            elif action == "refresh_all" and dashboard_win:
                dashboard_win.refresh_all(
                    msg["data"], msg["errors"], msg["urgent"]
                )
            elif action == "open_done":
                close_btn.config(state="normal")
                root.after(10000, monitor_queues)
            elif action == "open_error":
                showerror("Error al abrir instancias", msg["error"])
    except queue.Empty:
        pass
    root.after(200, _poll_ui_queue)

# ═══════════════════════════════════════════════════════════════════
#  CHROME — apertura en hilo secundario                    FIX #1
# ═══════════════════════════════════════════════════════════════════
def _open_chrome_thread(url: str, num_instances: int, use_kiosk: bool = False):
    """Corre en un Thread para no bloquear la UI."""
    global chrome_instances

    chrome_instances = []

    for i in range(num_instances):
        try:
            options = uc.ChromeOptions()

            # Perfil persistente por instancia (guarda sesiones y cookies)
            profile_path = os.path.join(_SCRIPT_DIR, "Profiles", f"chrome_profile_{i}")
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--log-level=3")
            
            if use_kiosk:
                options.add_argument("--kiosk")
            else:
                options.add_argument("--start-maximized")

            driver = uc.Chrome(options=options, use_subprocess=True)
            driver.get(url)
            chrome_instances.append(driver)

            instance_data[i] = {
                "time_left": "Cargando...",
                "status": "opening",
                "urgent": False,
                "error": False,
            }
            _ui_queue.put({"action": "refresh_card", "idx": i})

        except Exception as e:
            instance_data[i] = {
                "time_left": "Error",
                "status": "error",
                "urgent": False,
                "error": True,
            }
            _ui_queue.put({"action": "refresh_card", "idx": i})
            print(f"❌ Error abriendo instancia {i}: {e}")

        time.sleep(5)  # pausa entre instancias para no saturar

    # Señalizar que terminó (habilita botón y arranca monitor)
    _ui_queue.put({"action": "open_done"})

# ═══════════════════════════════════════════════════════════════════
#  MONITOR — lectura del estado de cada instancia
# ═══════════════════════════════════════════════════════════════════
_QUEUE_SCRIPT = """
let text = '';
let timeElem = document.getElementById('MainPart_lbWhichIsIn') ||
               document.getElementById('MainPart_TimeLeft')    ||
               document.querySelector('.time-left');
if (timeElem) { text += timeElem.innerText + ' '; }
if (text === '') { text = document.body.innerText; }
return text;
"""

def _parse_page(page_text: str) -> dict:
    """Analiza el texto de la página y devuelve un dict de estado."""
    t = page_text.lower()

    # 1. Comprobar PRIMERO si el turno ya comenzó o es el próximo
    # (Evita que "Tenés 10 minutos para realizar la transacción" se confunda con 10 min de espera en fila)
    turn_entry_keywords = (
        "tu turno comenzó", "tu turno comenzo",
        "tu turno es el proximo", "tu turno es el próximo",
        "your turn is next",
        "ya podés ingresar", "ya podes ingresar",
        "ingresar a boca socios",
        "realizar la transacción", "realizar la transaccion",
    )
    if any(k in t for k in turn_entry_keywords):
        return {"time_left": "¡ENTRAR YA!", "status": "enter", "urgent": True, "error": False}

    if any(k in t for k in ("menos de un minuto", "less than a minute", "menos de 1 minuto")):
        return {"time_left": "< 1 min", "status": "urgent", "urgent": True, "error": False}

    # 2. Minutos exactos de espera en la fila
    match = re.search(r'(\d+)\s*(minuto|minute)', t)
    if match:
        mins = int(match.group(1))
        urgent = mins <= 2
        return {
            "time_left": f"{mins} min",
            "status": "urgent" if urgent else "queue",
            "urgent": urgent,
            "error": False,
        }

    # 3. Otros estados
    if re.search(r'\b(hora|hour)s?\b', t):
        return {"time_left": "+1 hora", "status": "waiting", "urgent": False, "error": False}

    if re.search(r'\b(calculando|calculating)\b', t):
        return {"time_left": "Calculando...", "status": "calculating", "urgent": False, "error": False}

    if any(k in t for k in ("la fila abrir", "the queue will open", "la fila se abrir")):
        return {"time_left": "Fila cerrada", "status": "closed", "urgent": False, "error": False}

    return {"time_left": "N/O", "status": "unknown", "urgent": False, "error": False}


def focus_chrome_instance(idx: int):
    """Trae al frente y enfoca la ventana de la instancia Chrome correspondiente."""
    if 0 <= idx < len(chrome_instances):
        try:
            driver = chrome_instances[idx]
            driver.switch_to.window(driver.current_window_handle)
            driver.minimize_window()
            driver.maximize_window()
            print(f"📌 Instancia #{idx+1} traída al frente.")
        except Exception as e:
            print(f"❌ Error al enfocar instancia {idx+1}: {e}")


def monitor_queues():
    global _monitor_after_id

    if not chrome_instances:
        return

    errors       = 0
    urgent_count = 0

    for i, driver in enumerate(chrome_instances):
        try:
            page_text = driver.execute_script(_QUEUE_SCRIPT)
            if not page_text:
                instance_data[i] = {"time_left": "Sin datos", "status": "unknown",
                                    "urgent": False, "error": False}
                continue

            data = _parse_page(page_text)
            instance_data[i] = data

            if data["urgent"]:
                urgent_count += 1

        except Exception as e:
            errors += 1
            instance_data[i] = {"time_left": "Error", "status": "error",
                                 "urgent": False, "error": True}
            print(f"❌ Error instancia {i}: {type(e).__name__} — {str(e)[:80]}")

    if dashboard_win and dashboard_win.winfo_exists():
        dashboard_win.refresh_all(instance_data, errors, urgent_count)

    # Actualización cada 5 segundos (5000 ms)
    _monitor_after_id = root.after(5000, monitor_queues)


# ═══════════════════════════════════════════════════════════════════
#  STATUS MAPS
# ═══════════════════════════════════════════════════════════════════
STATUS_FG = {
    "opening":     BLUE,
    "queue":       TEXT_PRIMARY,
    "urgent":      ACCENT,
    "enter":       GREEN,
    "waiting":     TEXT_MUTED,
    "calculating": BLUE,
    "closed":      TEXT_MUTED,
    "unknown":     TEXT_MUTED,
    "error":       RED,
}
STATUS_BG = {
    "opening":     BG_OPEN,
    "queue":       BG_CARD,
    "urgent":      BG_URGENT,
    "enter":       BG_ENTER,
    "waiting":     BG_CARD,
    "calculating": BG_OPEN,
    "closed":      BG_CARD,
    "unknown":     BG_CARD,
    "error":       BG_ERROR,
}
STATUS_BADGE = {
    # (texto, bg_badge, fg_badge)  — FIX #8: patrón consistente: bg coloreado, fg oscuro
    "opening":     ("Abriendo",    BLUE,       BG_DARK),
    "queue":       ("En fila",     BLUE,       BG_DARK),
    "urgent":      ("URGENTE",     ACCENT,     BG_DARK),
    "enter":       ("ENTRAR YA",   GREEN,      BG_DARK),
    "waiting":     ("Esperando",   TEXT_MUTED, BG_DARK),
    "calculating": ("Calculando",  BLUE,       BG_DARK),
    "closed":      ("Cerrada",     TEXT_MUTED, BG_DARK),
    "unknown":     ("N/O",         TEXT_MUTED, BG_DARK),
    "error":       ("Error",       RED,        BG_DARK),
}
STATUS_DOT = {
    "opening":     BLUE,
    "queue":       BLUE,
    "urgent":      ACCENT,
    "enter":       GREEN,
    "waiting":     TEXT_MUTED,
    "calculating": BLUE,
    "closed":      TEXT_MUTED,
    "unknown":     TEXT_MUTED,
    "error":       RED,
}

# ═══════════════════════════════════════════════════════════════════
#  DASHBOARD WINDOW
# ═══════════════════════════════════════════════════════════════════
COLS = 3   # tarjetas por fila

class Dashboard(tk.Toplevel):

    def __init__(self, parent: tk.Tk, num_instances: int, url: str):
        super().__init__(parent)
        self.num_instances = num_instances
        self.url           = url
        self.card_widgets: dict[int, dict] = {}
        self._canvas_ref   = None  # para unbind en destroy  FIX #7

        self.title("Monitor de Fila")
        self.configure(bg=BG_DARK)
        self.geometry("1000x680")
        self.minsize(700, 500)

        self._build_header()
        self._build_stats_bar()
        self._build_cards_area()
        self._build_footer()

        # FIX #7: desregistrar bind_all al destruir la ventana
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Inicializar tarjetas en "abriendo"
        for i in range(num_instances):
            instance_data[i] = {"time_left": "...", "status": "opening",
                                 "urgent": False, "error": False}
        self.refresh_all(instance_data, 0, 0)

    def _on_close(self):
        """Limpieza al cerrar el dashboard."""
        if self._canvas_ref:
            try:
                self._canvas_ref.unbind_all("<MouseWheel>")
            except Exception:
                pass
        self.destroy()

    # ─── HEADER ────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_HEADER)
        hdr.pack(fill="x")

        inner = tk.Frame(hdr, bg=BG_HEADER, pady=14)
        inner.pack(fill="x", padx=24)

        tk.Label(
            inner, text="▣  MONITOR DE FILA",
            font=(FONT, 17, "bold"),
            bg=BG_HEADER, fg=ACCENT,
        ).pack(side="left")

        tk.Label(
            inner, text="Sistema de monitoreo en tiempo real",
            font=(FONT, 10),
            bg=BG_HEADER, fg=TEXT_MUTED,
        ).pack(side="right")

        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

    # ─── STATS BAR ─────────────────────────────────────────────────
    def _build_stats_bar(self):
        bar = tk.Frame(self, bg=BG_DARK, pady=10)
        bar.pack(fill="x", padx=20)

        self.lbl_tokens  = self._stat_pill(bar, "TOKENS",      str(self.num_instances), BLUE)
        self.lbl_queue   = self._stat_pill(bar, "EN FILA",     "—",                     TEXT_PRIMARY)
        self.lbl_urgent  = self._stat_pill(bar, "URGENTES",    "—",                     ACCENT)
        self.lbl_errors  = self._stat_pill(bar, "ERRORES",     "—",                     RED)
        self.lbl_updated = self._stat_pill(bar, "ACTUALIZADO", "--:--:--",               TEXT_MUTED)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20)

    def _stat_pill(self, parent, label, value, color):
        box = tk.Frame(parent, bg=BG_CARD, padx=18, pady=8)
        box.pack(side="left", padx=6, pady=2)
        tk.Label(box, text=label, font=(FONT, 7, "bold"),
                 bg=BG_CARD, fg=TEXT_MUTED).pack()
        val = tk.Label(box, text=value, font=(FONT, 20, "bold"),
                       bg=BG_CARD, fg=color)
        val.pack()
        return val

    # ─── CARDS AREA ────────────────────────────────────────────────
    def _build_cards_area(self):
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=16, pady=10)

        canvas = tk.Canvas(outer, bg=BG_DARK, highlightthickness=0)
        vsb    = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._canvas_ref = canvas  # guardar ref para unbind  FIX #7

        self.cards_frame = tk.Frame(canvas, bg=BG_DARK)
        self._cwin = canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")

        self.cards_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(self._cwin, width=e.width)
        )

        # FIX #7: bind_all reemplazado por bind en el canvas + focus
        canvas.bind("<Enter>", lambda e: canvas.focus_set())
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._build_cards()

    def _build_cards(self):
        for i in range(self.num_instances):
            row = i // COLS
            col = i % COLS
            self.cards_frame.grid_columnconfigure(col, weight=1)
            self._make_card(i, row, col)

    def _make_card(self, i: int, row: int, col: int):
        card = tk.Frame(self.cards_frame, bg=BG_CARD, padx=16, pady=14)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        # ── Fila superior: número + badge ──
        top = tk.Frame(card, bg=BG_CARD)
        top.pack(fill="x")

        num_lbl = tk.Label(top, text=f"#{i+1:02d}",
                           font=(FONT, 11, "bold"), bg=BG_CARD, fg=TEXT_MUTED)
        num_lbl.pack(side="left")

        badge = tk.Label(top, text="  Abriendo  ",
                         font=(FONT, 7, "bold"), bg=BLUE, fg=BG_DARK,
                         padx=4, pady=2)
        badge.pack(side="right")

        # ── Tiempo (número grande) ──
        time_lbl = tk.Label(card, text="...",
                            font=(FONT, 26, "bold"), bg=BG_CARD, fg=TEXT_PRIMARY)
        time_lbl.pack(pady=(10, 0))

        sub_lbl = tk.Label(card, text="minutos",
                           font=(FONT, 8), bg=BG_CARD, fg=TEXT_MUTED)
        sub_lbl.pack()

        # ── Separador ──
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=8)

        # ── Indicador inferior ──
        bot = tk.Frame(card, bg=BG_CARD)
        bot.pack(fill="x")

        dot = tk.Label(bot, text="●", font=(FONT, 10), bg=BG_CARD, fg=BLUE)
        dot.pack(side="left")

        dot_txt = tk.Label(bot, text=f"instancia {i+1}",
                           font=(FONT, 8), bg=BG_CARD, fg=TEXT_MUTED)
        dot_txt.pack(side="left", padx=4)

        widgets_list = (card, top, num_lbl, badge, time_lbl, sub_lbl, bot, dot, dot_txt)
        for w in widgets_list:
            w.config(cursor="hand2")
            w.bind("<Button-1>", lambda e, idx=i: focus_chrome_instance(idx))

        self.card_widgets[i] = {
            "card":     card,
            "top":      top,
            "num":      num_lbl,
            "badge":    badge,
            "time_lbl": time_lbl,
            "sub_lbl":  sub_lbl,
            "bot":      bot,
            "dot":      dot,
            "dot_txt":  dot_txt,
        }

    # ─── FOOTER ────────────────────────────────────────────────────
    def _build_footer(self):
        ft = tk.Frame(self, bg="#0A0D11", pady=6)
        ft.pack(fill="x", side="bottom")
        tk.Label(
            ft,
            text="Actualización cada 5 s  •  Haz click en una tarjeta para enfocar la ventana  •  undetected-chromedriver",
            font=(FONT, 8), bg="#0A0D11", fg=TEXT_MUTED,
        ).pack()

    # ─── REFRESH (un card) ─────────────────────────────────────────
    def refresh_card(self, i: int):
        if not self.winfo_exists():
            return
        data = instance_data.get(i, {})
        w    = self.card_widgets.get(i)
        if not w:
            return

        status  = data.get("status", "unknown")
        tl      = data.get("time_left", "N/O")
        urgent  = data.get("urgent", False)

        fg              = STATUS_FG.get(status, TEXT_MUTED)
        bg              = STATUS_BG.get(status, BG_CARD)
        btxt, bbg, bfg  = STATUS_BADGE.get(status, ("N/O", TEXT_MUTED, BG_DARK))
        dot_col         = STATUS_DOT.get(status, TEXT_MUTED)

        # Actualizar fondo de todos los sub-widgets de la tarjeta
        for widget in (w["card"], w["top"], w["bot"], w["num"],
                       w["time_lbl"], w["sub_lbl"], w["dot"], w["dot_txt"]):
            try:
                widget.config(bg=bg)
            except Exception:
                pass

        w["time_lbl"].config(text=tl, fg=fg)
        badge_text = f"  {'⚡ ' if urgent else ''}{btxt}  "
        w["badge"].config(text=badge_text, bg=bbg, fg=bfg)
        w["dot"].config(fg=dot_col)

    # ─── REFRESH (todos) ───────────────────────────────────────────
    def refresh_all(self, data: dict, errors: int, urgent_count: int):
        if not self.winfo_exists():
            return
        now      = datetime.datetime.now().strftime("%H:%M:%S")
        in_queue = sum(1 for d in data.values()
                       if d.get("status") in ("queue", "waiting", "urgent", "enter", "opening"))

        self.lbl_queue.config(text=str(in_queue))
        self.lbl_urgent.config(text=str(urgent_count))
        self.lbl_errors.config(text=str(errors))
        self.lbl_updated.config(text=now)

        for i in data:
            self.refresh_card(i)


# ═══════════════════════════════════════════════════════════════════
#  CONTROL WINDOW — acciones
# ═══════════════════════════════════════════════════════════════════
def execute_script():
    global chrome_instances, dashboard_win, _monitor_after_id

    url = url_entry.get().strip()
    if not url:
        showerror("Error", "Ingresá una URL.")
        return

    try:
        instances = int(instances_entry.get())
        if instances < 1:
            raise ValueError
    except ValueError:
        showerror("Error", "Número de instancias inválido.")
        return

    use_kiosk = kiosk_var.get()
    mode_desc = "Modo Kiosk (pantalla completa sin controles)" if use_kiosk else "Ventana normal maximizada (minimizable, redimensionable)"

    confirm = askokcancel(
        "Confirmar",
        f"Se abrirán {instances} instancias en modo {mode_desc}:\n{url}\n\n¿Continuar?"
    )
    if not confirm:
        return

    # FIX #3: cerrar instancias previas antes de abrir nuevas
    if chrome_instances:
        for driver in chrome_instances:
            try:
                driver.quit()
            except Exception:
                pass
        chrome_instances = []

    # FIX #2: cancelar el bucle de monitor anterior
    if _monitor_after_id is not None:
        try:
            root.after_cancel(_monitor_after_id)
        except Exception:
            pass
        _monitor_after_id = None

    save_config({"url": url, "instances": instances, "kiosk": use_kiosk})

    # Abrir dashboard antes de lanzar Chrome
    if dashboard_win and dashboard_win.winfo_exists():
        dashboard_win.destroy()
    dashboard_win = Dashboard(root, instances, url)

    close_btn.config(state="disabled")  # se rehabilita cuando termina el thread

    # FIX #1: abrir Chrome en thread secundario para no bloquear la UI
    t = threading.Thread(
        target=_open_chrome_thread,
        args=(url, instances, use_kiosk),
        daemon=True
    )
    t.start()


def close_windows():
    global chrome_instances, _monitor_after_id

    # Cancelar monitor
    if _monitor_after_id is not None:
        try:
            root.after_cancel(_monitor_after_id)
        except Exception:
            pass
        _monitor_after_id = None

    for driver in chrome_instances:
        try:
            driver.quit()
        except Exception:
            pass
    chrome_instances = []
    close_btn.config(state="disabled")
    showinfo("Cerrado", "Todas las instancias fueron cerradas.")


# ═══════════════════════════════════════════════════════════════════
#  MAIN — ventana de control (dark theme)
# ═══════════════════════════════════════════════════════════════════
root = tk.Tk()
root.title("Instances — Panel de Control")
root.configure(bg=BG_DARK)
root.resizable(False, False)

# ── Header ──────────────────────────────────────────────────────────
hdr_f = tk.Frame(root, bg=BG_HEADER, pady=12)
hdr_f.pack(fill="x")
tk.Label(hdr_f, text="▣  INSTANCES",
         font=(FONT, 14, "bold"), bg=BG_HEADER, fg=ACCENT).pack(side="left", padx=16)
tk.Label(hdr_f, text="Panel de Control",
         font=(FONT, 9), bg=BG_HEADER, fg=TEXT_MUTED).pack(side="right", padx=16)
tk.Frame(root, bg=ACCENT, height=2).pack(fill="x")

# ── Formulario ──────────────────────────────────────────────────────
form = tk.Frame(root, bg=BG_DARK, padx=24, pady=20)
form.pack(fill="x")

def _lbl(parent, text, row, col, **kw):
    tk.Label(parent, text=text, font=(FONT, 9), bg=BG_DARK,
             fg=TEXT_MUTED, **kw).grid(row=row, column=col,
                                        sticky="w", pady=4, padx=(0, 8))

def _entry(parent, row, col, width=42, default=""):
    e = tk.Entry(parent, width=width,
                 font=(FONT, 10), bg=BG_CARD, fg=TEXT_PRIMARY,
                 insertbackground=TEXT_PRIMARY, relief="flat",
                 highlightthickness=1, highlightcolor=ACCENT,
                 highlightbackground=BORDER)
    e.insert(0, default)
    e.grid(row=row, column=col, pady=4, padx=4, ipady=5, sticky="ew")
    return e

config = load_config()
_url_default = config.get("url", "")            if config else ""
_n_default   = str(config.get("instances", "")) if config else ""

_lbl(form, "URL", 0, 0)
url_entry = _entry(form, 0, 1, default=_url_default)

_lbl(form, "Instancias", 1, 0)
instances_entry = _entry(form, 1, 1, width=8, default=_n_default)

tk.Label(form, text="Cada instancia ~100 MB RAM  •  5 s de pausa entre aperturas",
         font=(FONT, 7), bg=BG_DARK, fg=TEXT_MUTED).grid(
         row=2, column=0, columnspan=2, sticky="w", pady=(0, 6))

_kiosk_default = bool(config.get("kiosk", False)) if config else False

kiosk_var = tk.BooleanVar(value=_kiosk_default)
kiosk_cb  = tk.Checkbutton(form, text="Modo Kiosk (pantalla completa sin controles de ventana ni click derecho)",
                           variable=kiosk_var, font=(FONT, 8), bg=BG_DARK, fg=TEXT_MUTED,
                           selectcolor=BG_CARD, activebackground=BG_DARK, activeforeground=TEXT_PRIMARY)
kiosk_cb.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

# ── Botones ─────────────────────────────────────────────────────────
btn_f = tk.Frame(root, bg=BG_DARK, pady=14)
btn_f.pack()

def _btn(parent, text, cmd, bg, fg=BG_DARK, state="normal"):
    b = tk.Button(parent, text=text, command=cmd,
                  font=(FONT, 10, "bold"), bg=bg, fg=fg,
                  activebackground=fg, activeforeground=bg,
                  relief="flat", padx=20, pady=8, cursor="hand2",
                  state=state, bd=0)
    b.pack(side="left", padx=8)
    return b

_btn(btn_f, "▶  Iniciar", execute_script, ACCENT)
close_btn = _btn(btn_f, "✕  Cerrar todo", close_windows, RED, state="disabled")

# ── Footer ──────────────────────────────────────────────────────────
tk.Frame(root, bg=BORDER, height=1).pack(fill="x")
tk.Label(root, text="undetected-chromedriver 3.5.5",
         font=(FONT, 7), bg=BG_DARK, fg=TEXT_MUTED, pady=6).pack()

# Arrancar el poller de la UI queue
root.after(200, _poll_ui_queue)

root.mainloop()
