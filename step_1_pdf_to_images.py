import os
from pathlib import Path
from pdf2image import convert_from_path

def pdf_to_images(pdf_path, dpi=300):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_folder = pdf_name
    image_folder = os.path.join(output_folder, "images")
    
    Path(image_folder).mkdir(parents=True, exist_ok=True)
    
    print(f"Converting PDF '{pdf_name}' to images with DPI={dpi}...")
    images = convert_from_path(pdf_path, dpi=dpi, fmt='jpeg')
    
    total_pages = len(images)
    digits = len(str(total_pages))
    
    for i, image in enumerate(images, start=1):
        image_path = os.path.join(image_folder, f"Page_{str(i).zfill(digits)}.jpeg")
        image.save(image_path, "JPEG")
        print(f"Page {i} saved as image: {image_path}")
    
    print(f"PDF '{pdf_name}' conversion to JPEG images complete.")

def process_all_pdfs(pdf_directory):
    for filename in os.listdir(pdf_directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            pdf_to_images(pdf_path)

if __name__ == "__main__":
    pdf_directory = "pdfs"
    process_all_pdfs(pdf_directory)
    print("All PDFs have been processed.")