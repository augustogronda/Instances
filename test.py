import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

try:
    o = Options()
    o.add_extension(r'C:\Users\augus\repos\instancesgit\Instances\vpn_extension.crx')
    o.add_experimental_option('detach', True)
    driver = webdriver.Chrome(options=o)
    driver.get('https://example.com')
    print('SUCCESS')
except Exception as e:
    print(traceback.format_exc())
