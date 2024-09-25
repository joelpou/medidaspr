from selenium import webdriver
from selenium.webdriver.common.by import By
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/legislators",
    tags=["legislators"],
    responses={status.HTTP_401_UNAUTHORIZED: {"user": "Not authorized"}}
)

# Function to scrape voting data
@router.get("/senators")
async def get_senators():
    # Set up Selenium (assumes connection to Selenium container)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Remote(command_executor="http://selenium:4444/wd/hub", options=options)
    driver.get("https://senado.pr.gov/index.cfm?module=senadores")  # Replace with actual URL
    
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
    # 'https://www.camara.pr.gov/page-team/'
   
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