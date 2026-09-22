
import os
import time
import json
import random
import asyncio
from tkinter import Tk, Label, Entry, Button
from tkinter.messagebox import askokcancel, showinfo, showerror
from playwright.async_api import async_playwright

playwright_instances = []

async def open_playwright_instances(url, num_instances):
    global playwright_instances
    playwright_instances = []
    if num_instances > 3:
        showinfo("Recomendación", "Para evitar bloqueos del firewall, no abras más de 3 instancias a la vez.")
    for i in range(num_instances):
        p = await async_playwright().start()
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale='es-ES'
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        page = await context.new_page()
        await page.goto(url)
        # Simula comportamiento humano
        await page.mouse.move(random.randint(100, 400), random.randint(100, 400))
        await page.keyboard.type("Hola mundo")
        await page.wait_for_timeout(random.randint(2000, 5000))
        await page.mouse.wheel(0, random.randint(100, 500))
        playwright_instances.append((p, browser, context, page))
        await asyncio.sleep(random.uniform(3, 7))
    return playwright_instances

def save_config(data):
    try:
        with open("config_playwright.json", "w") as config_file:
            json.dump(data, config_file, indent=4)
    except Exception as e:
        showerror("Error", f"Error saving the configuration: {str(e)}")

def load_config():
    try:
        if os.path.exists("config_playwright.json"):
            with open("config_playwright.json", "r") as config_file:
                return json.load(config_file)
    except Exception as e:
        showerror("Error", f"Error loading configuration: {str(e)}")
    return None

def execute_script():
    global playwright_instances
    url = url_entry.get()
    try:
        instances = int(instances_entry.get())
    except ValueError:
        showerror("Error", "Please enter a valid instance number.")
        return
    confirm = askokcancel(
        "Confirm Run",
        f"This will open {instances} instances of Chromium with the URL:\n{url}\n¿Do you want to continue?"
    )
    if not confirm:
        return
    save_config({"url": url, "instances": instances})
    async def run_async():
        try:
            await open_playwright_instances(url, instances)
            showinfo("Success!", f"{instances} Instances of Chromium opened")
            close_button.config(state="normal")
        except Exception as e:
            showerror("Error", f"An error occurred: {str(e)}")
    asyncio.run(run_async())

def close_windows():
    global playwright_instances
    async def close_all():
        for p, browser, context, page in playwright_instances:
            await browser.close()
            await p.stop()
        showinfo("Cerrado", "All Chromium instances are closed")
    asyncio.run(close_all())

root = Tk()
root.title("Instances Playwright")

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
Label(root, text="Insert URL with 'https://' for example https://www.google.com.ar/").grid(row=1, column=1, padx=10, pady=5)

Label(root, text="number of instances:").grid(row=2, column=0, padx=10, pady=5)
Label(root, text="Each instance is a separate browser window with approximately 100 MB of RAM per instance.").grid(row=3, column=1, padx=10, pady=5)

instances_entry = Entry(root, width=10)
instances_entry.insert(0, instances_entry_value)
instances_entry.grid(row=2, column=1, padx=10, pady=5)

Button(root, text="Run", command=execute_script).grid(row=6, column=0, columnspan=2, pady=10)

close_button = Button(root, text="Close Windows", command=close_windows, state="disabled")
close_button.grid(row=7, column=0, columnspan=2, pady=10)

root.mainloop() 