import time, re, logging
from enum import Enum
from .scraper import Scraper
from selenium import webdriver

sutra_base_url = 'https://sutra.oslpr.org/osl'
esutra_base_url = f'{sutra_base_url}/esutra'
status_tracker_url = f'{sutra_base_url}/SUTRA/tracker'

class MeasureStatus(Enum):
    FILLED = f'{status_tracker_url}/6/PS-1.png'
    SENATE_APPROVED = f'{status_tracker_url}/8/PS-2.png'
    HOUSE_APPROVED = f'{status_tracker_url}/7/PS-3.png'
    SENT_GOVERNOR = f'{status_tracker_url}/9/PS-4.png'
    GOVERNOR_APPROVED = f'{status_tracker_url}/10/PS-5.png'
    
    def get_enum_name_from_value(value):
        for member in MeasureStatus:
            if member.value == value:
                return member.name
        return None
    
class MeasureSearch(Scraper):
    def __init__(
        self, 
        term = None, 
        driver = None, 
        type = None, 
        body = None,
        num = None,
        url = None
    ) -> None:
        self.term: str = term
        self.browser: webdriver = driver
        self.type: str = type
        self.body: str = body
        self.num: str = num
        
        if not url:
            super().__init__(driver=driver, url=sutra_base_url)
        else:
            super().__init__(driver=driver, url=url)
        
        if term: self.select_term(term)
        if type: self.select_type(type)
        if body: self.select_body(body)
        if num: self.input_measure_number(num)
        
    def get_driver(self):
        return super()._get_driver()
    
    def get_windows(self):
        return self.get_driver().window_handles
        
    def wait(self, call):
        return super()._wait(call)
        
    def submit_form(self):
        self.wait(super()._submit_form('ctl00_CPHBody_Tramites_btnFilter'))
        
    def select_term(self, option):
        self.wait(super().select_input('ctl00_CPHBody_Tramites_lovCuatrienio', option))
        
    def select_type(self, option):
        self.wait(super().select_input('ctl00_CPHBody_Tramites_lovTipoMedida', option))
        
    def select_body(self, option):
        self.wait(super().select_input('ctl00_CPHBody_Tramites_lovCuerpoId', option))
        
    def switch_to_view_all_measures(self):
        self.wait(super().select_input('ctl00_CPHBody_Tramites_ddlPageSize', 'Todos'))
        
    def input_measure_number(self, measure_number):
        self.wait(super().input_text('ctl00_CPHBody_Tramites_txt_Medida', measure_number))
        
    def get_measure_filled_date(self):
        return super().find_by_id('ctl00_CPHBody_txt_FechaRadicada').text
        
    def get_measure_description(self):
        return super().find_by_id('ctl00_CPHBody_txtTitulo').text
    
    def get_measure_authors(self):        
        self.wait(super().select_tab('ctl00_CPHBody_AnejoTabsn1'))
        
        authors = []
        author_table = super().find_by_id('ctl00_CPHBody_TabAutores_dgResults')
        authors_class = super().finds_by_driver_and_class(author_table, 'DetailFormLbl')
        for author in authors_class:
            authors.append(author.text)
            
        return authors 
        
    def get_measures_in_page(self):
        title_value = 'Presione para navegar a la Medida...'
        return super().finds_by_xpath("//table[contains(@class, 'datagrid')]//tr[@title='{}']".format(title_value))
        
    def get_all_voted_measures(self):
        time.sleep(1)
        self.submit_form()
        
        voted_measure_numbers = []
        previous_page_number = 1   
        
        while True:
            measures = self.get_measures_in_page()
            
            for row in measures:
                # Get status tracker button
                status = self.get_measure_status(row)        
                if status != MeasureStatus.RADICADO.name:
                    measure_number = self.get_measure_number(row.text)
                    logging.info(f'Reading measure: {measure_number}')
                    if measure_number not in voted_measure_numbers:
                        voted_measure_numbers.append(measure_number)

            next_page_number = self.next_page()
            
            if previous_page_number == next_page_number:
                break
            else:
                previous_page_number = next_page_number
                
        self.quit()
                
        return voted_measure_numbers    
        
    def get_measure_status(self, measure):
        status = None
        
        # WebDriverWait(measure, 10).until(
        #     EC.visibility_of_element_located((By.XPATH, ".//td//div//img[contains(@class, 'tracker-bg')]"))
        # )
        # img_element = measure.find_element(By.XPATH, ".//td//div//img[contains(@class, 'tracker-bg')]")
        img_element = super().find_by_driver_and_xpath(measure, ".//td//div//img[contains(@class, 'tracker-bg')]")
        # self.browser.execute_script("arguments[0].scrollIntoView(true);", img_element)
        status_url = img_element.get_attribute('src')
            
        # Store measure number as long as it is not in filed state
        if status_url in [status.value for status in MeasureStatus]:
            status = MeasureStatus.get_enum_name_from_value(status_url)
            
        return status
 
    def get_measure_number(self, title):
        number = None
        # Regular expression to find the code in the format (PS0001)
        match = re.search(r'\(PS\d{4}\)', title)
        if match: number = match.group(0)[1:-1]    
        return number  
        
    def next_page(self):
        next_button = super().find_by_id("ctl00_CPHBody_Tramites_NextPage")
        super().get_driver().execute_script("arguments[0].scrollIntoView(true);", next_button)

        time.sleep(1)
        next_button.click()
        
        next_page_number = super().find_by_id("ctl00_CPHBody_Tramites_lblpagefooter")
        next_page_number = next_page_number.text.rsplit(':')[1].strip()
        
        return int(next_page_number)
    
    def quit(self):
        self.browser.quit()