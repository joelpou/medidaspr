import json, threading, time, logging, re
from datetime import datetime
from queue import Queue
from selenium import webdriver
from selenium.webdriver.common.by import By
from fastapi import APIRouter, UploadFile, Request, BackgroundTasks, status, File, Depends
from fastapi.responses import JSONResponse, FileResponse
from helpers.sutra import esutra_base_url, MeasureSearch, MeasureStatus
from helpers.scraper import init_driver
from db.models import Measure

FORMAT = '%(levelname)s: %(asctime)s | %(module)s | %(funcName)s | %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

router = APIRouter(
    prefix="/legislators",
    tags=["legislators"],
    responses={status.HTTP_401_UNAUTHORIZED: {"user": "Not authorized"}}
)

# def init_driver() -> webdriver.Remote:
#     # Set up Selenium (assumes connection to Selenium container)
#     options = webdriver.ChromeOptions()
#     options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     driver = webdriver.Remote(command_executor="http://selenium:4444/wd/hub", options=options)
#     return driver

def get_all_measures(driver: webdriver.Remote, term: str, type:str) -> None:
    queue = Queue()

    # Start the producer (string extractor)
    producer_thread = threading.Thread(target=get_measure_ids, args=(queue, driver, term, type))
    producer_thread.start()

    # Start multiple consumers (search performers)
    num_consumers = 5  # Set number of consumer threads (i.e., concurrent searches)
    consumers = []
    for _ in range(num_consumers):
        consumer_thread = threading.Thread(target=search_measure, args=(queue, term, type))
        consumers.append(consumer_thread)
        consumer_thread.start()

    # Wait for the producer and all consumers to finish
    producer_thread.join()
    for consumer_thread in consumers:
        consumer_thread.join()
        
# Producer function: extracts strings from divs and puts them into the queue
def get_measure_ids(queue: Queue, driver: webdriver.Remote, term: str, type:str) -> None:   
    search = MeasureSearch(driver=driver, term=term, type=type)    
    search.submit_form() 
      
    time.sleep(1)
    
    voted_measure_numbers = []
    
    while True:
        search.switch_to_view_all_measures()        
        measures = search.get_measures_in_page()
        
        for row in measures:
            # Get status tracker button
            status = search.get_measure_status(row)        
            if status != MeasureStatus.FILLED.name:
                measure_number = search.get_measure_number(row.text)
                if measure_number not in voted_measure_numbers:                    
                    onclick = row.get_attribute("onclick")            
                    match = re.search(r"'(.*?)'", onclick)

                    if match:
                        extracted_url = match.group(1)  # Extract the matched group
                        measure_url = f'{esutra_base_url}/{extracted_url.lower()}'
                        queue.put((measure_number, status, measure_url))
                        
                    else:
                        print("No match found")  
        

# Consumer function: takes strings from the queue and performs the search
def search_measure(queue: Queue, term: str, type: str):
    
    while True:
        measure_number, measure_status, measure_url = queue.get()
        if measure_number is None:
            queue.put(None)  # Signal other consumers that work is done
            break

        # Perform search using the string
        search = MeasureSearch(url=measure_url)
        
        date_filled = datetime.strptime(search.get_measure_filled_date(),'%m/%d/%Y')
        title = search.get_measure_description()        
        authors = search.get_measure_authors()
        
        # measure_info = {
        #     'status': measure_status,
        #     'date_filled': date_filled,
        #     'description': title,
        #     'authors': authors,
        # }
        
        measure = Measure(
            number = measure_number,
            term = term,
            title = title,
            authors = authors,
            type = type,
            status = measure_status,
            filled_date = date_filled
        )
        
        logging.info(f'{measure_number} get in queue')
        
        # await measure.save()
        
        # measures.append({measure_number: measure_info})
        search.quit()
        
        print(f"Consumed and searched for: {measure_number}") 

         
@router.get("/load_senator_measures", response_class=FileResponse)
async def load_legislator_measures(
    background_tasks: BackgroundTasks,
    term: str = '2021-2024', 
    type: str = 'Proyecto del Senado'
):
    
    driver =  init_driver()
    driver.get(esutra_base_url)
    background_tasks.add_task(get_all_measures, driver, term, type)

    return JSONResponse(
        content={'message': 'loading current measure data into db'}, 
        status_code=status.HTTP_200_OK
    )
    

@router.get("/get_senators")
async def get_senators():    
    driver = init_driver()    
    driver.get("https://senado.pr.gov/index.cfm?module=senadores")
    
    senator_list = []
    senator_divs = driver.find_elements(By.CLASS_NAME, 'senator_cont')
    
    for div in senator_divs:
        href = div.find_element(By.TAG_NAME, 'a')
        link_bio = href.get_attribute('href')
        link_pic = href.find_element(By.TAG_NAME, 'img').get_attribute('src')
        full_name = href.find_element(By.CLASS_NAME, 'name').text
        position = href.find_element(By.CLASS_NAME, 'position').text
        party = href.find_element(By.CLASS_NAME, 'partido').text
        senator_info = {
            'full_name': full_name,
            'position': position if position else None,
            'party' : party,
            'bio': link_bio,
            'pic': link_pic            
        }
        
        senator_list.append(senator_info)
           
    driver.quit()
    
    ppds = sum(1 for d in senator_list if d['party'] == 'Partido Popular Democrático')
    pnps = sum(1 for d in senator_list if d['party'] == 'Partido Nuevo Progresista')
    mvcs = sum(1 for d in senator_list if d['party'] == 'Movimiento Victoria Ciudadana')
    pds = sum(1 for d in senator_list if d['party'] == 'Proyecto Dignidad')
    indes = sum(1 for d in senator_list if d['party'] == 'Independiente')
    
    senator_info = {
        'total': str(len(senator_list)),
        'ppds': str(ppds),
        'pnps': str(pnps),
        'mvcs': str(mvcs),
        'pds': str(pds),
        'indeps': str(indes)        
    }

    return {"message": f"PR Senator info: {senator_info}", "senators": senator_list}         

   