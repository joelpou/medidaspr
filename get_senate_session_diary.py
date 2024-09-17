import time
from PyPDF2 import PdfReader
import requests
from io import BytesIO

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
# service = Service('/usr/local/bin/chrome-linux64/chrome')
# service.start()
# driver = webdriver.Remote(service.service_url)
browser = webdriver.Chrome()
browser.get('https://senado.pr.gov/index.cfm?module=session-diary')


session_rows = browser.find_elements(By.TAG_NAME, 'tr')

for row in session_rows:
    # Extract cells from each row
    cells = row.find_elements(By.TAG_NAME, "td")
    for i, cell in enumerate(cells):
        title, session = '', ''
        if i == 0:
            title = cell.accessible_name
        elif i == 1:
            session = cell.accessible_name
        # Check if the cell contains a link
        link = cell.find_element(By.TAG_NAME, "a").get_attribute("href")
        if link.endswith(".pdf"):
            # Process the PDF link
            response = requests.get(link)
            pdf_content = BytesIO(response.content)
            
            # Process the PDF content (example using PyPDF2 library)
            pdf_reader = PdfReader(pdf_content)
            num_pages = len(pdf_reader.pages)
            
            pdf_title = f'{title} - {session}.txt'
            
            # Append each page's text to the output file
            with open(pdf_title, "a", encoding="utf-8") as f:
                f.write(f"PDF Link: {link}\n")
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    f.write(f"Page {page_num + 1}:\n{text}\n\n")
                    print(f"Page {page_num + 1} appended to {pdf_title}")
    
    
    # row_data = [cell.text for cell in cells]
    # print(row_data)

time.sleep(5) # Let the user actually see something!
browser.quit()