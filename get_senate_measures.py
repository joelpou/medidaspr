import time, re
from enum import Enum
from selenium import webdriver
from selenium.webdriver.common.by import By
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
    
class Measure():
    def __init__(self, term, type = None, body = None, num = None) -> None:
        self.term = term
        self.type = type
        self.body = body
        self.num = num
        
        if term: self.select_term(term)
        if type: self.select_type(type)
        if body: self.select_body(body)
        if num: self.input_measure_number(num)        
    
    def find_by_id(self, id):
        return browser.find_element(By.ID, id)
    
    def select_option(self, input_element, option):
        select = Select(input_element)
        select.select_by_visible_text(option)
        
    def input_text(self, input_element, text):
        input_element.clear()
        input_element.send_keys(text)
        
    def submit_form(self):
        submit_button = self.find_by_id('ctl00_CPHBody_Tramites_btnFilter')
        submit_button.click()
        
    def select_term(self, option):
        input_element = self.find_by_id('ctl00_CPHBody_Tramites_lovCuatrienio')
        self.select_option(input_element, option)
        
    def select_type(self, option):
        input_element = self.find_by_id('ctl00_CPHBody_Tramites_lovTipoMedida')
        self.select_option(input_element, option)
        
    def select_body(self, option):
        input_element = self.find_by_id('ctl00_CPHBody_Tramites_lovCuerpoId')
        self.select_option(input_element, option)
        
    def input_measure_number(self, measure_number):
        input_element = self.find_by_id('ctl00_CPHBody_Tramites_txt_Medida')
        self.input_text(input_element, measure_number)
        
    def get_measure_list(self):
        title_value = 'Presione para navegar a la Medida...'
        return browser.find_elements(By.XPATH, 
                                     "//table[contains(@class, 'datagrid')]//tr[@title='{}']".format(title_value))
        
    def get_measure_status(self, measure):
        status = None
        img_element = measure.find_element(By.XPATH, ".//td//div//img[contains(@class, 'tracker-bg')]")        
        status_url = img_element.get_attribute('src')
            
        # Store measure number as long as it is not in filed state
        if status_url in [status.value for status in Status]:
            status = Status.get_enum_name_from_value(status_url)
            
        return status
    
def get_measure_number(title):
    number = None
    # Regular expression to find the code in the format (PS0001)
    match = re.search(r'\(PS\d{4}\)', title)
    if match: number = match.group(0)[1:-1]    
    return number  
    
def next_page():
    next_button = browser.find_element(By.ID, "ctl00_CPHBody_Tramites_NextPage")
    browser.execute_script("arguments[0].scrollIntoView(true);", next_button)

    time.sleep(1)
    next_button.click()
    
    next_page_number = browser.find_element(By.ID, "ctl00_CPHBody_Tramites_lblpagefooter")
    next_page_number = next_page_number.text.rsplit(':')[1].strip()
    
    return int(next_page_number)
    
def get_senate_voted_measures():
    
    cuatrienio = '2021-2024'
    tipo_medida = 'Proyecto del Senado'
    
    measure = Measure(cuatrienio, tipo_medida)    
    measure.submit_form() 
      
    time.sleep(1)
    
    voted_measure_numbers = []
    previous_page_number = 1   
    
    while True:
        measures = measure.get_measure_list()
        
        for row in measures:
            # Get status tracker button
            status = measure.get_measure_status(row)        
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
    
def get_votes_from_measures():
    cuatrienio = '2021-2024'
    num_medida = 'PS0283'
    
    measure = Measure(cuatrienio, num=num_medida)
    measure.submit_form()   
    measure.submit_form()   
    
    time.sleep(5)
    
if __name__ == '__main__':
    # get_senate_voted_measures()
    get_votes_from_measures()