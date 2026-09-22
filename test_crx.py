from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

chrome_options = Options()
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

extension_path = os.path.abspath(r"C:\Users\augus\repos\instancesgit\Instances\vpn_extension.crx")
chrome_options.add_extension(extension_path)

# use an empty profile
chrome_options.add_argument(f"user-data-dir={os.path.abspath('Profiles/test_profile')}")

driver = webdriver.Chrome(options=chrome_options)
driver.get("chrome://extensions")
time.sleep(5)
driver.save_screenshot("test_crx_screenshot.png")
driver.quit()
