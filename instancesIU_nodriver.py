import os
import json
import re
import asyncio
import threading
from tkinter import Tk, Label, Entry, Button
from tkinter.messagebox import askokcancel, showinfo, showerror

try:
    import nodriver as uc
except ImportError:
    print("❌ Falta la librería 'nodriver'. Por favor instalala ejecutando en la consola:")
    print("pip install nodriver")
    import sys
    sys.exit(1)

nodriver_instances = []

async def monitor_queues_loop():
    """Monitorea el tiempo restante usando Nodriver"""
    while True:
        await asyncio.sleep(15)
        if not nodriver_instances:
            continue
            
        for i, browser_data in enumerate(nodriver_instances):
            try:
                browser, page = browser_data
                
                script = """
                    let text = '';
                    let timeElem = document.getElementById('MainPart_lbWhichIsIn') || 
                                   document.getElementById('MainPart_TimeLeft') || 
                                   document.querySelector('.time-left');
                    if (timeElem) { text += timeElem.innerText + ' '; }
                    if (text === '') { text = document.body.innerText; }
                    text;
                """
                page_text = await page.evaluate(script)
                
                if not page_text:
                    continue
                    
                page_text = str(page_text).lower()
                
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
                        if (!window.alert_shown) {
                            alert('¡ATENCIÓN! Faltan menos de 2 minutos en esta instancia.\\n\\nVe rápido.');
                            window.alert_shown = true;
                        }
                    """
                    await page.evaluate(alert_script)
                    
            except Exception as e:
                # Ignoramos errores si la página cerró o hubo un problema temporal
                pass

async def open_nodriver_instances(url, num_instances):
    global nodriver_instances
    nodriver_instances = []
    
    print(f"🚀 Iniciando {num_instances} instancias con Nodriver (Indetectable)...")
    
    for i in range(num_instances):
        try:
            profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "Profiles", f"chrome_profile_{i}"))
            
            # Argumentos básicos, nodriver se encarga del resto de la magia antidetect
            browser_args = [
                "--window-size=1100,800",
                "--log-level=3",
            ]
            
            # Start browser
            browser = await uc.start(
                user_data_dir=profile_path,
                headless=False,
                browser_args=browser_args
            )
            
            # Navigate
            page = await browser.get(url)
            
            nodriver_instances.append((browser, page))
            print(f"✅ Instancia {i} iniciada correctamente.")
            
            # Pequeña pausa entre aperturas para no saturar la PC ni levantar sospechas
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Error iniciando instancia {i}: {e}")

def save_config(data):
    try:
        with open("config_nodriver.json", "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass

def load_config():
    if os.path.exists("config_nodriver.json"):
        with open("config_nodriver.json", "r") as f:
            return json.load(f)
    return None

def execute_script():
    url = url_entry.get()
    try:
        instances = int(instances_entry.get())
    except ValueError:
        showerror("Error", "Ingresa un número válido de instancias.")
        return

    confirm = askokcancel("Confirmar", f"¿Abrir {instances} instancias indetectables con Nodriver?\n\nDestino: {url}")
    if not confirm:
        return
        
    save_config({"url": url, "instances": instances})
    close_button.config(state="normal")
    
    def run_async():
        # Crear un nuevo event loop para el hilo en segundo plano
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Abrir instancias
        loop.run_until_complete(open_nodriver_instances(url, instances))
        print("✅ Proceso de apertura finalizado. Monitoreo de filas activado.")
        
        # Mantener vivo el loop asíncrono para el monitoreo
        loop.create_task(monitor_queues_loop())
        loop.run_forever()
        
    # Ejecutar en segundo plano para no congelar la interfaz Tkinter
    threading.Thread(target=run_async, daemon=True).start()

def close_windows():
    # Cerrar todas las instancias abiertas de Nodriver
    for browser, _ in nodriver_instances:
        try:
            browser.stop()
        except:
            pass
    nodriver_instances.clear()
    print("Todas las ventanas han sido cerradas.")

# === Interfaz de Usuario ===
root = Tk()
root.title("Instances - Nodriver (Stealth Mode)")
root.geometry("500x300")

config = load_config()
url_val = config.get("url", "") if config else ""
inst_val = config.get("instances", "3") if config else "3"

Label(root, text="URL Destino (Queue-it / Boca):", font=("Arial", 10, "bold")).pack(pady=(10,0))
url_entry = Entry(root, width=50)
url_entry.insert(0, url_val)
url_entry.pack(pady=5)

Label(root, text="Número de instancias:", font=("Arial", 10, "bold")).pack(pady=(10,0))
instances_entry = Entry(root, width=15, justify="center")
instances_entry.insert(0, inst_val)
instances_entry.pack(pady=5)

Button(root, text="🚀 Ejecutar Instancias (Nodriver)", command=execute_script, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), pady=5).pack(pady=15)

close_button = Button(root, text="Cerrar Ventanas", command=close_windows, state="disabled", bg="#f44336", fg="white", font=("Arial", 10))
close_button.pack(pady=5)

root.mainloop()
