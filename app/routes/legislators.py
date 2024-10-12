import json, asyncio, time, logging, re
from urllib.parse import unquote
from typing import Union, List
from ollama import AsyncClient
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse, FileResponse
from helpers.sutra import esutra_base_url, MeasureSearch, MeasureStatus
from helpers.scraper import init_driver
from db.models import Measure, Status, Term, Senator, Body, Position

FORMAT = '%(levelname)s: %(asctime)s | %(module)s | %(funcName)s | %(message)s'
formatter = logging.Formatter(FORMAT)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger = logging.getLogger('medidaspr')
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addHandler(console_handler)

# logging.basicConfig(level=logging.INFO, format=FORMAT)
logging.getLogger('webdriver_manager').setLevel(logging.CRITICAL)
logging.getLogger('selenium').setLevel(logging.CRITICAL)

router = APIRouter(
    prefix="/legislators",
    tags=["legislators"],
    responses={status.HTTP_401_UNAUTHORIZED: {"user": "Not authorized"}}
)

async def get_all_measures(driver: webdriver.Remote, term: str, type: str, test_mode: int = 0) -> None:
    start = time.time()
    queue = asyncio.Queue()
    
    producer = asyncio.create_task(get_measure_ids(queue, driver, term, type, test_mode))

    num_consumers = 5
    consumers = [asyncio.create_task(search_measure(queue, term, type)) for _ in range(num_consumers)]

    # Wait for all tasks to complete
    await asyncio.gather(producer, *consumers)
    
    end = time.time()
    total_time = end - start
    logger.info("Elapsed time: "+ str(round(total_time, 2)/3600) + " hours")
        
# Producer function: extracts strings from divs and puts them into the queue
async def get_measure_ids(
    queue: asyncio.Queue, 
    driver: webdriver.Remote, 
    term: str, type:str, 
    test_mode: int
) -> None:  
     
    search = MeasureSearch(driver=driver, term=term, type=type)    
    search.submit_form() 
    logger.info(f'Start get_measure_ids')
    
    time.sleep(1)
    
    voted_measure_numbers = []
    cnt = 1
    
    while True:
        search.switch_to_view_all_measures()        
        measures = search.get_measures_in_page()
        
        logger.info(f'Iterating measures')
        for row in measures:
            status = search.get_measure_status(row)        
            # if status != MeasureStatus.FILLED.name: # skip non-voted measures
            measure_number = search.get_measure_number(row.text)
            if measure_number not in voted_measure_numbers:                    
                onclick = row.get_attribute("onclick")            
                match = re.search(r"'(.*?)'", onclick)

                if match:
                    extracted_url = match.group(1)  # Extract the matched group
                    measure_url = f'{esutra_base_url}/{extracted_url.lower()}'
                    await queue.put((measure_number, status, measure_url))
                    logger.info(f'{cnt} | {measure_number} put in queue')
                    cnt += 1
                    
                else:
                    logger.error(f'No match found!')
                        
            if len(test_mode) > 0 and cnt >= test_mode:
                break          
        break

# Consumer function: takes strings from the queue and performs the search
async def search_measure(queue: asyncio.Queue, term: str, type: str):
    
    while True:
        measure_number, measure_status, measure_url = await queue.get()
        if measure_number is None:
            queue.put(None)  # Signal other consumers that work is done
            break
        
        logger.info(f"Processing: {measure_number}")
        search = MeasureSearch(url=measure_url)
        
        date_filled = datetime.strptime(search.get_measure_filled_date(),'%m/%d/%Y')
        title = search.get_measure_description()        
        authors = search.get_measure_authors()
        
        aisummary = await summarize(title)
        
        measure = Measure(
            number = measure_number,
            term = term,
            aisummary = aisummary,
            authors = authors,
            type = type,
            status = measure_status,
            url = measure_url,
            is_law = True if measure_status == Status.GOVERNOR_APPROVED.name else False,
            filled_date = date_filled
        )          
        
        # Store data in db
        await measure.save()
        search.quit()
        
        logger.info(f"{measure_number} stored.")
        queue.task_done() 
        
async def llama_chat(message: Union [str, List], model: str = 'llama3.2:1b') -> AsyncClient:
    client = AsyncClient(host='ollama')
    if model not in await client.list():
        await client.pull(model)
    response = await client.chat(model=model, 
                                 messages=[message] if isinstance(message, str) else message)
    return response

async def chat(message: str, ):
    message = {'role': 'user', 'content': f'{message}'}
    response = await llama_chat(message=message)
    return response

async def summarize(measure: str):
    messages=[
        {
            'role': 'system',
            'content': '''
            Eres un experto en la legislación de Puerto Rico y tu objetivo es enseñar a los adolescentes sobre las diversas 
            medidas que se debaten y analizan dentro de esta rama del gobierno de una forma básica. Explica concisamente y brevemente.:
            '''
        },
        {
            'role': 'user',
            'content': f'Resume la siguiente medida en una oración: {measure}.',
        }
    ]
    response = await llama_chat(message=messages)
    return response['message']['content']
         
@router.get("/load_senator_measures", response_class=FileResponse)
async def load_legislator_measures(
    background_tasks: BackgroundTasks,
    term: str = '2021-2024', 
    type: str = 'Proyecto del Senado',
    test_mode: int = 50 # Only process first n measures in term
):
    
    driver = init_driver()
    driver.get(esutra_base_url)
    background_tasks.add_task(get_all_measures, driver, term, type, test_mode)

    return JSONResponse(
        content={'message': 'loading current measure data into db'}, 
        status_code=status.HTTP_200_OK
    )   

@router.get("/load_senators")
async def get_senators(): 
    driver = init_driver()    
    driver.get("https://senado.pr.gov/index.cfm?module=senadores")
    
    senator_list = []
    senator_divs = driver.find_elements(By.CLASS_NAME, 'senator_cont')
    
    for div in senator_divs:
        original_window = driver.current_window_handle
        href = div.find_element(By.TAG_NAME, 'a')
        link_bio = unquote(href.get_attribute('href'))
        link_pic = unquote(href.find_element(By.TAG_NAME, 'img').get_attribute('src'))
        full_name = href.find_element(By.CLASS_NAME, 'name').text
        position = href.find_element(By.CLASS_NAME, 'position').text
        party = href.find_element(By.CLASS_NAME, 'partido').text           
        
        split_name = full_name.rsplit(' ')[1:]
        if len(split_name) == 4:
            first_name = split_name[0]
            middle_name = split_name[1]
            last_first_name = split_name[2]
            last_second_name = split_name[3]
        else:
            first_name = split_name[0]
            last_first_name = split_name[1]
            last_second_name = split_name[2]    
            
        driver.execute_script(f"window.open('{link_bio}', '_blank');")
        new_window = driver.window_handles[-1]
        driver.switch_to.window(new_window)   
        # await asyncio.sleep(1)        
        district = driver.find_elements(By.CLASS_NAME, 'section_titles')[0].text        
        driver.switch_to.window(original_window)
        
        # position_values = [pos.value for pos in Position]
        # pos = None       
        
        # for value in position_values:
        #     if value in position:
        #         pos = value
        #     if 'Portavoz' in position:
        #         pos = Position.SPOKEPERSON.value
        
        senator = Senator(
            term = Term._2021.value,
            district = district,
            first_name = first_name,
            middle_name = middle_name,
            last_first_name = last_first_name,
            last_second_name = last_second_name,
            party = party,
            body = Body.SENATE.value,
            position = position,
            bio = link_bio,
            pic = link_pic,
            active = True           
        )
        
        await senator.save()       
        
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

@router.get("/chat/")
async def query(message: str):
    result = await chat(message)
    return {"response": result}