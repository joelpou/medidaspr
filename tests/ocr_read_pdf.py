import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Path to the PDF file
pdf_path = 'data/ps0002-21.pdf'

# Convert PDF to a list of image objects
images = convert_from_path(pdf_path)

full_text = ""

# Loop through the images and perform OCR
for i, image in enumerate(images):
    # Save image if you want to verify what was extracted
    # image.save(f'page_{i + 1}.png', 'PNG')
    
    # Perform OCR on the image
    text = pytesseract.image_to_string(image)
    
    # Print or store the extracted text
    print(f"Text from page {i + 1}:")
    print(text)
    print("-" * 100)
    
    full_text += text
    
print(full_text)
