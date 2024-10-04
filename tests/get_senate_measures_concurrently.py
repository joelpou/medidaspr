import sys, os

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_path)

import threading
import time
from queue import Queue
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from app.helpers.sutra import MeasureSearch, MeasureStatus

measures = []
cnt = 1

# Producer function: extracts strings from divs and puts them into the queue
def get_measure_ids(queue):
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
            if status != MeasureStatus.RADICADO.name:
                measure_number = search.get_measure_number(row.text)
                if measure_number not in voted_measure_numbers:
                    queue.put((measure_number, status))

        next_page_number = search.next_page()
        
        if previous_page_number == next_page_number:
            queue.put(None)  # Signal that the producer is done
            search.quit()
            break
        else:
            previous_page_number = next_page_number 
        

# Consumer function: takes strings from the queue and performs the search
def perform_search(queue):
    term = '2021-2024'
    
    while True:
        measure_number, measure_status = queue.get()  # Take a string from the queue
        if measure_number is None:
            queue.put(None)  # Signal other consumers that work is done
            break

        # Perform search using the string
        search = MeasureSearch(term=term, num=measure_number)
        search.submit_form()
        search.submit_form()
        
        # time.sleep(0.5)   
        
        measure = search.get_measures_in_page()[0]        
        measure.click()
        
        date_filled = search.get_measure_filled_date()
        title = search.get_measure_description()        
        authors = search.get_measure_authors()
        
        measure_info = {
            'status': measure_status,
            'date_filled': date_filled,
            'description': title,
            'authors': authors,
        }
        
        measures.append({measure_number: measure_info})
        search.quit()
        
        print(f"Consumed and searched for: {measure_number}")  # Optional print for debug 

        # time.sleep(2)  # Simulate wait for the search to complete (adjust as needed)    
    
    

# Main function to coordinate producer-consumer workflow
def main():
    queue = Queue()

    # Start the producer (string extractor)
    producer_thread = threading.Thread(target=get_measure_ids, args=(queue,))
    producer_thread.start()

    # Start multiple consumers (search performers)
    num_consumers = 3  # Set number of consumer threads (i.e., concurrent searches)
    consumers = []
    for _ in range(num_consumers):
        consumer_thread = threading.Thread(target=perform_search, args=(queue,))
        consumers.append(consumer_thread)
        consumer_thread.start()

    # Wait for the producer and all consumers to finish
    producer_thread.join()
    for consumer_thread in consumers:
        consumer_thread.join()

if __name__ == "__main__":
    main()
