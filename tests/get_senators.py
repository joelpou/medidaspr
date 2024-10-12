import time
from selenium import webdriver
from selenium.webdriver.common.by import By

browser = webdriver.Chrome()
base_url = 'https://senado.pr.gov/index.cfm?module=senadores'
browser.get(base_url)
 
def get_senators():
    
    senator_list = []
    senator_divs = browser.find_elements(By.CLASS_NAME, 'senator_cont')
    
    for div in senator_divs:
        href = div.find_element(By.TAG_NAME, 'a')
        link_bio = href.get_attribute('href')
        link_pic = href.find_element(By.TAG_NAME, 'img').get_attribute('src')
        full_name = href.find_element(By.CLASS_NAME, 'name').text
        position = href.find_element(By.CLASS_NAME, 'position').text
        party = href.find_element(By.CLASS_NAME, 'partido').text
        
        original_window = browser.current_window_handle
        browser.execute_script(f"window.open('{link_bio}', '_blank');")
        
        # Get type of senator(por distrito vs por acumulacion)
        type = browser.find_elements(By.CLASS_NAME, 'section_titles')[0].text        
        browser.switch_to.window(original_window)        
        
        senator_info = {
            'full_name': full_name,
            'position': position if position else None,
            'type': type,
            'party' : party,
            'bio': link_bio,
            'pic': link_pic
            
        }
        senator_list.append(senator_info)
    
    time.sleep(5)
    browser.quit()
    
if __name__ == '__main__':
    get_senators()