import time, logging
from typing import Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    options = Options()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager(driver_version="129.0.6668.89").install()), 
        options=options)
    return driver            

class Scraper:
    
    def __init__(self, driver = None, url = None) -> None:
        self.browser: webdriver.Chrome = driver
        
        if url and not driver:            
            self.browser = init_driver()
            self.browser.get(url)  

    def _get_driver(self) -> webdriver.Chrome:
        return self.browser
        
    def _wait(self, func, *args, **kwargs):
        if not func: return None
        call = None
        while True:
            try:
                call = func(*args, **kwargs)
                # print("Tab clicked successfully!")
                break
            
            except StaleElementReferenceException:
                logging.debug("Stale element, retrying...")
                time.sleep(0.5)
        return call
    # def wait(self, func, *args, **kwargs):
    #     wait = WebDriverWait(self.browser, 10)  # Adjust timeout as needed
    #     try:
    #         return wait.until(lambda driver: func(*args, **kwargs))
    #     except TimeoutException:
    #         logging.debug(f"Timed out waiting for {func}")
    #         return None  # or raise an exception

    
    def find_by_class(self, _class):  
        return self._wait(self.browser.find_element, By.CLASS_NAME, _class)
    
    def finds_by_class(self, _class):  
        return self._wait(self.browser.find_elements, By.CLASS_NAME, _class)
    
    def finds_by_driver_and_class(
        self, driver: Union[webdriver.Chrome , WebElement], 
        _class: str
    ) -> WebElement:
        return self._wait(driver.find_elements, By.CLASS_NAME, _class)
    
    def find_by_id(self, id):
        # WebDriverWait(self.browser, 10).until(
        #     EC.visibility_of_element_located((By.ID, id))
        # )
        # return self._wait(self.browser.find_element, By.ID, id)
        return self._wait(self.browser.find_element, By.ID, id)
    
    def finds_by_id(self, id):
        return self._wait(self.browser.find_elements, By.ID, id)
    
    def finds_by_driver_and_id(self, driver: Union[webdriver.Chrome, WebElement], id: str) -> WebElement:
        return self._wait(driver.find_element, By.ID, id)
    
    def find_by_driver_and_id(self, driver: Union[webdriver.Chrome, WebElement], id: str) -> WebElement:
        return self._wait(driver.find_element, By.ID, id)
    
    def find_by_xpath(self, xpath):
        return self._wait(self.browser.find_element, By.XPATH, xpath)
    
    def find_by_driver_and_xpath(self, driver: Union[webdriver.Chrome, WebElement], xpath: str) -> WebElement:
        return self._wait(driver.find_element, By.XPATH, xpath)
    
    def finds_by_xpath(self, xpath):  
        return self._wait(self.browser.find_elements, By.XPATH, xpath)
    
    def select_option(self, input_element, option):
        select = Select(input_element)
        self._wait(select.select_by_visible_text, option)
        
    def input_text(self, id, text):
        input_element = self.find_by_id(id)
        self._wait(input_element.clear)
        self._wait(input_element.send_keys, text)
        
    def _submit_form(self, id):
        submit_button = self.find_by_id(id)
        self._wait(self.browser.execute_script, "arguments[0].scrollIntoView(true);", submit_button)
        self._wait(submit_button.click)
        
    def select_input(self, id, option):
        input_element = self.find_by_id(id)
        self._wait(self.select_option, input_element, option)
        
    def select_tab(self, id):
        tab = self.find_by_id(id)
        self._wait(self.browser.execute_script, "arguments[0].scrollIntoView(true);", tab)
        self._wait(tab.click)
        
        