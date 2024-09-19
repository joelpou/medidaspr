import time, re

from enum import Enum
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

browser = webdriver.Chrome()
base_url = 'https://sutra.oslpr.org/osl'
browser.get(f'{base_url}/esutra/')

status_tracker_url = f'{base_url}/SUTRA/tracker'

class Status(Enum):
    RADICADO = f'{status_tracker_url}/6/PS-1.png'
    SEN_APRO = f'{status_tracker_url}/8/PS-2.png'
    CAM_APRO = f'{status_tracker_url}/7/PS-3.png'
    ENV_GOBE = f'{status_tracker_url}/9/PS-4.png'
    LEY = f'{status_tracker_url}/10/PS-5.png'
    
    def get_enum_name_from_value(value):
        for member in Status:
            if member.value == value:
                return member.name
        return None
    
def get_measure_number(title):
    number = None
    # Regular expression to find the code in the format (PS0001)
    match = re.search(r'\(PS\d{4}\)', title)
    if match: number = match.group(0)[1:-1]    
    return number 
    

def select_option(selection, option):    
    class_name = 'FormFieldSpace'
    select_element = browser.find_element(By.XPATH, 
                                          f"//div[contains(@class, \
                                                '{class_name}')]//label[contains(text(), \
                                                '{selection}')]/following-sibling::select \
                                          ")
    select = Select(select_element)
    select.select_by_visible_text(option)
    
def next_page():
    next_button = browser.find_element(By.ID, "ctl00_CPHBody_Tramites_NextPage")
    browser.execute_script("arguments[0].scrollIntoView(true);", next_button)

    time.sleep(1)
    next_button.click()
    
    next_page_number = browser.find_element(By.ID, "ctl00_CPHBody_Tramites_lblpagefooter")
    next_page_number = next_page_number.text.rsplit(':')[1].strip()
    
    return int(next_page_number)
    
def main():

    cuatrienio = '2021-2024'
    tipo_medida = 'Proyecto del Senado'
    select_option('Cuatrienio', cuatrienio)
    select_option('Tipo de Medida', tipo_medida)
    select_option('Cuerpo', 'S - Senado') 
    
    submit_button = browser.find_element(By.CSS_SELECTOR, "input[type='submit'].CommandBtn")
    submit_button.click()
    
    time.sleep(1)
    
    voted_measure_numbers = []
    previous_page_number = 1   
    
    while True:
        title_value = 'Presione para navegar a la Medida...'
        measures = browser.find_elements(By.XPATH, "//table[contains(@class, 'datagrid')]//tr[@title='{}']".format(title_value)) 
        
        for row in measures:
            # Get status tracker button
            img_element = row.find_element(By.XPATH, ".//td//div//img[contains(@class, 'tracker-bg')]")        
            status_url = img_element.get_attribute('src')
            
            # Store measure number as long as it is not in filed state
            if status_url in [status.value for status in Status]:
                status = Status.get_enum_name_from_value(status_url)
                if status != Status.RADICADO.name:
                    measure_number = get_measure_number(row.text)
                    if measure_number not in voted_measure_numbers:
                        voted_measure_numbers.append(measure_number)

        next_page_number = next_page()
        
        if previous_page_number == next_page_number:
            break
        else:
            previous_page_number = next_page_number        
        
    with open(f'{cuatrienio}_Medidas_{tipo_medida}.txt', 'w') as file:
        for measure_number in voted_measure_numbers:
            file.write(f"{measure_number},\n")

    time.sleep(5) # Let the user actually see something!
    browser.quit()
    
if __name__ == '__main__':
    main()