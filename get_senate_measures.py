import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

browser = webdriver.Chrome()
browser.get('https://sutra.oslpr.org/osl/esutra/')

def select_option(selection, option):    
    class_name = 'FormFieldSpace'
    select_element = browser.find_element(By.XPATH, 
                                          f"//div[contains(@class, \
                                                '{class_name}')]//label[contains(text(), \
                                                '{selection}')]/following-sibling::select \
                                          ")
    select = Select(select_element)
    select.select_by_visible_text(option)    
    
def main():

    select_option('Cuatrienio', '2021-2024')
    select_option('Tipo de Medida', 'Proyecto del Senado')
    select_option('Cuerpo', 'S - Senado') 
    
    submit_button = browser.find_element(By.CSS_SELECTOR, "input[type='submit'].CommandBtn")
    submit_button.click()
    
    time.sleep(1)
    
    # rows = browser.find_elements(By.XPATH, "//table[contains(@class, 'datagrid')]//tr")

    # # Iterate over the rows and do something
    # for row in rows:
    #     print(row.text)
    
    title_value = 'Presione para navegar a la Medida...'

    # Find all <tr> elements under the table with class 'datagrid' that contain the accessible name
    rows = browser.find_elements(By.XPATH, "//table[contains(@class, 'datagrid')]//tr[@title='{}']".format(title_value))

    # Iterate over the found rows and perform actions (e.g., print their content)
    for row in rows:
        print(row.text)
    

    time.sleep(5) # Let the user actually see something!
    browser.quit()
    
if __name__ == '__main__':
    main()