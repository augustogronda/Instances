import os
import time
import json
from tkinter import Tk, Label, Entry, Button, Checkbutton, BooleanVar
from tkinter.messagebox import askokcancel, showinfo, showerror
from tkinter.filedialog import askopenfilename
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


chromedriver_path = ""
chrome_instances = []


def select_chromedriver():
    global chromedriver_path
    
    chromedriver_path = askopenfilename(
        title="Seleccionar ChromeDriver",
        filetypes=[("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")]
    )
    
    if chromedriver_path:
        showinfo("Seleccionado", f"ChromeDriver seleccionado: {chromedriver_path}")
    else:
        showerror("Error", "No se seleccionó ningún archivo ChromeDriver.")

def open_chrome_instances(url, num_instances):
    global chromedriver_path, chrome_instances
    if not chromedriver_path:
        showerror("Error", "No se ha seleccionado ChromeDriver. Por favor, selecciona un archivo.")
        return
    
    chrome_instances = []  
    for i in range(num_instances):
        
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir=/tmp/chrome_profile_{i}")
        chrome_options.add_argument("--new-window")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        
        
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
      
        driver.get(url)
        
        chrome_instances.append(driver)
        time.sleep(1)  
    
    
    return chrome_instances


def save_config(data):
    try:
        with open("config.json", "w") as config_file:
            json.dump(data, config_file, indent=4)
    except Exception as e:
        showerror("Error", f"Error al guardar la configuración: {str(e)}")


def load_config():
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r") as config_file:
                return json.load(config_file)
    except Exception as e:
        showerror("Error", f"Error al cargar la configuración: {str(e)}")
    return None


def execute_script():
    global chrome_instances
    url = url_entry.get()
    
    try:
        instances = int(instances_entry.get())
    except ValueError:
        showerror("Error", "Por favor, ingresa un número válido de instancias.")
        return

    
    confirm = askokcancel(
        "Confirmar ejecución",
        f"Se abrirán {instances} instancias de Chrome con la URL:\n{url}\n¿Deseas continuar?"
    )

    if not confirm:
        return  
   
    save_config({"url": url, "instances": instances})

   
    try:
        chrome_instances = open_chrome_instances(url, instances)
        showinfo("Éxito", f"{instances} instancias de Chrome se han abierto.")
        
       
        close_button.config(state="normal")
        
      
        root.mainloop()
    except Exception as e:
        showerror("Error", f"Ocurrió un error: {str(e)}")


def close_windows():
    global chrome_instances
    for driver in chrome_instances:
        driver.quit()
    showinfo("Cerrado", "Las instancias de Chrome han sido cerradas.")


root = Tk()
root.title("Abrir instancias de Chrome")


config = load_config()
if config:
    url_entry_value = config.get("url", "")
    instances_entry_value = config.get("instances", "")
else:
    url_entry_value = ""
    instances_entry_value = ""




Label(root, text="URL:").grid(row=0, column=0, padx=10, pady=5)
url_entry = Entry(root, width=40)
url_entry.insert(0, url_entry_value)
url_entry.grid(row=0, column=1, padx=10, pady=5)
Label(root, text="Insertar URL con https:// como por ejemplo https://www.google.com.ar/").grid(row=1, column=1, padx=10, pady=5)

Label(root, text="Número de instancias:").grid(row=2, column=0, padx=10, pady=5)
Label(root, text="Cada instancia es una ventana de navegador distinta\nAproximadamente 100 MB de RAM por instancia.").grid(row=3, column=1, padx=10, pady=5)

instances_entry = Entry(root, width=10)
instances_entry.insert(0, instances_entry_value) 
instances_entry.grid(row=2, column=1, padx=10, pady=5)

Button(root, text="Seleccionar ChromeDriver", command=select_chromedriver).grid(row=5, column=0, columnspan=2, pady=5)

Button(root, text="Ejecutar", command=execute_script).grid(row=6, column=0, columnspan=2, pady=10)

close_button = Button(root, text="Cerrar ventanas", command=close_windows, state="disabled")
close_button.grid(row=6, column=0, columnspan=2, pady=10)

root.mainloop()
