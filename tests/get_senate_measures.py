import sys, os

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_path)

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.helpers.sutra import MeasureSearch, MeasureStatus
    
def get_senate_voted_measures():
    
    term = '2021-2024'
    type = 'Proyecto del Senado'
    
    search = MeasureSearch(term=term, type=type)    
    search.submit_form() 
      
    # time.sleep(1)
    
    voted_measure_numbers = []
    previous_page_number = 1   
    
    while True:
        measures = search.get_measures_in_page()
        
        for row in measures:
            # Get status tracker button
            status = search.get_measure_status(row)        
            if status != MeasureStatus.FILLED.name:
                measure_number = search.get_measure_number(row.text)
                if measure_number not in voted_measure_numbers:
                    voted_measure_numbers.append(measure_number)

        next_page_number = search.next_page()
        
        if previous_page_number == next_page_number:
            break
        else:
            previous_page_number = next_page_number        
        
    with open(f'{term}_Medidas_{type}.txt', 'w') as file:
        for measure_number in voted_measure_numbers:
            file.write(f"{measure_number},\n")

    # time.sleep(5) # Let the user actually see something!
    search.quit()
    
def get_votes_from_measures():
    term = '2021-2024'
    number = 'PS0283'
    
    search = MeasureSearch(term=term, num=number)
    search.submit_form()   
    search.submit_form()   
    
    time.sleep(5)
    
if __name__ == '__main__':  
    get_senate_voted_measures()
    # get_votes_from_measures()