import json, asyncio, time, logging, re
from urllib.parse import unquote
from typing import Union, List, Dict
from ollama import AsyncClient
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse, FileResponse
from helpers.sutra import esutra_base_url, MeasureSearch, MeasureStatus
from helpers.scraper import init_driver
from db.models import Measure, Status, Term, Legislator, Body, Position, DistrictType, MeasureCategory

FORMAT = '%(levelname)s: %(asctime)s | %(module)s | %(funcName)s | %(message)s'
formatter = logging.Formatter(FORMAT)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
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
def split_legislator_name(full_name: str) -> Union[str, str, str, str]:
    middle_name = ""
    split_name = full_name.rsplit(' ')
    if 'Hon' in full_name:
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
        
    return unquote(first_name), unquote(middle_name), unquote(last_first_name), unquote(last_second_name)

async def get_all_measures(driver: webdriver.Remote, term: str, type: str, test_mode: int = 0) -> None:
    start = time.time()
    queue = asyncio.Queue()
    
    producer = asyncio.create_task(get_measure_ids(queue, driver, term, type, test_mode))

    num_consumers = 3
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
                        
            if test_mode > 0 and cnt >= test_mode:
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
        
        aisummary = await summarize(title)
              
        authors = search.get_measure_authors()        
        
        measure = Measure(
            number = measure_number,
            term = term,
            aisummary = aisummary['summary'],
            category = aisummary['category'],
            type = type,
            status = measure_status,
            url = measure_url,
            is_law = True if measure_status == Status.GOVERNOR_APPROVED.name else False,
            filled_date = date_filled
        )
        
        # Store data in db
        if measure:            
            await measure.save()            
            logger.info(f"{measure_number} stored.")
            
        else:
            logger.error('Measure is none!')
        
        for author in authors:
            logger.debug(f'Searching for {author}')
            first_name, _, last_first_name, last_second_name = split_legislator_name(author)
            if 'Senado' in type:                
                senator = await Legislator.objects.get_or_none(
                    first_name=first_name, 
                    last_first_name=last_first_name,
                    last_second_name=last_second_name
                )
                if senator:
                    logger.debug(f'Adding senator author: {authors}')
                    await measure.authors.add(senator)
                else: 
                    logger.error(f'Could not find author: {author}')
              
        search.quit()
        # queue.task_done()
        
async def llama_chat(message: Union [Dict, List[Dict]], model: str = 'llama3.1:8b') -> str:
    client = AsyncClient(host='ollama')
    models = await client.list()
    model_names = [model['name'] for model in models['models']]
    if model not in model_names:
        await client.pull(model)
    response = await client.chat(model=model, messages=[message] if isinstance(message, Dict) else message)
    return response

async def chat(message: str):
    message = {'role': 'user', 'content': f'{message}'}
    response = await llama_chat(message=message)
    return response

async def summarize(measure: str):
    category_values = [member.value for member in MeasureCategory]
    messages=[
    {
        'role': 'system',
        'content': f'''
        You are a helpful assistant. Your objective is to summarize a legislative measure.
        Respond only with valid JSON with values in Spanish. Do not write an introduction or summary.
        Here is an example:
        
        {{
            "summary": "Resumen del propósito de la medida legislativa en no más de dos oraciones enfatizando los puntos mas importantes.",
            "category": "Decide a que categoría (una sola) pertenece esta medida de acuerdo a {category_values}"
        }}
        '''
    },
    {
        'role': 'user',
        'content': f'Summarize the following with the JSON structure specified: {measure}'
    }
    ]
    response = await llama_chat(message=messages)
    return json.loads(response['message']['content'])
         
@router.get("/load_measures", response_class=FileResponse)
async def load_legislator_measures(
    background_tasks: BackgroundTasks,
    term: str = '2021-2024', 
    type: str = 'Proyecto del Senado',
    test_mode: int = 10 # Only process first n measures in term
):
    
    driver = init_driver()
    driver.get(esutra_base_url)
    background_tasks.add_task(get_all_measures, driver, term, type, test_mode)

    return JSONResponse(
        content={'message': 'loading current measure data into db'}, 
        status_code=status.HTTP_200_OK
    )
    
@router.get("/get_senators")
async def get_senators(term: str = '2021-2024'):
    
    senator_list = []
    senators = await Legislator.objects.all(term=term, body=Body.SENATE.value)
    
    for senator in senators:
        if senator.middle_name:
            full_name = f'{senator.first_name} {senator.middle_name} {senator.last_first_name} {senator.last_second_name}'
        else:
            full_name = f'{senator.first_name} {senator.last_first_name} {senator.last_second_name}'

        senator_info = {
            'full_name': full_name,
            'position': senator.position,
            'district' : senator.district,
            'party' : senator.party,
            'bio': senator.bio,
            'pic': senator.pic            
        }
        
        senator_list.append(senator_info)
    
    ppds = sum(1 for d in senator_list if d['party'] == 'Partido Popular Democrático')
    pnps = sum(1 for d in senator_list if d['party'] == 'Partido Nuevo Progresista')
    mvcs = sum(1 for d in senator_list if d['party'] == 'Movimiento Victoria Ciudadana')
    pds = sum(1 for d in senator_list if d['party'] == 'Proyecto Dignidad')
    indes = sum(1 for d in senator_list if d['party'] == 'Independiente')
    
    party_distro = {
        'ppds': str(ppds),
        'pnps': str(pnps),
        'mvcs': str(mvcs),
        'pds': str(pds),
        'indeps': str(indes),
        'total': str(len(senator_list))     
    }

    return {
        "term": term,
        "party distribution": party_distro, 
        "senators": senator_list
    } 

@router.get("/load_senators")
async def load_senators(): 
    driver = init_driver()    
    driver.get("https://senado.pr.gov/index.cfm?module=senadores")
    
    senator_divs = driver.find_elements(By.CLASS_NAME, 'senator_cont')
    
    for div in senator_divs:
        original_window = driver.current_window_handle
        href = div.find_element(By.TAG_NAME, 'a')
        link_bio = unquote(href.get_attribute('href'))
        link_pic = unquote(href.find_element(By.TAG_NAME, 'img').get_attribute('src'))
        full_name = href.find_element(By.CLASS_NAME, 'name').text
        position = href.find_element(By.CLASS_NAME, 'position').text
        party = href.find_element(By.CLASS_NAME, 'partido').text           
        
        first_name, middle_name, last_first_name, last_second_name = split_legislator_name(full_name)
            
        driver.execute_script(f"window.open('{link_bio}', '_blank');")
        new_window = driver.window_handles[-1]
        driver.switch_to.window(new_window)
        # await asyncio.sleep(1)
        # TODO district from senators.pr.gov does not give district municipality :/
        district = driver.find_elements(By.CLASS_NAME, 'section_titles')[0].text        
        driver.switch_to.window(original_window)
        
        position_values = [pos.value for pos in Position]
        pos = position       
        
        for value in position_values:
            if value in position:
                pos = value
                
        senator_type_values = [pos.value for pos in DistrictType]
        dist = district
        
        for value in senator_type_values:
            if value in district:
                dist = value
        
        senator = Legislator(
            term = Term._2021.value,
            district = dist,
            first_name = first_name,
            middle_name = middle_name,
            last_first_name = last_first_name,
            last_second_name = last_second_name,
            party = party,
            body = Body.SENATE.value,
            position = pos,
            bio = link_bio,
            pic = link_pic,
            active = True           
        )
        
        await senator.save()       
           
    driver.quit()

    return {"message": f"Senators saved in db!"}         

@router.post("/chat/")
async def chat(message: str):
    result = await chat(message)
    return {"response": result}

@router.post("/sum/")
async def summarize_measure(message: str):
    result = await summarize(message)
    return {"response": result}