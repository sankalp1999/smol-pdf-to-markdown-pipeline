import os
import base64
from pathlib import Path
from openai import OpenAI
from os import getenv
from io import BytesIO
from PIL import Image
import json

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY"),
)

PROMPT = '''
I will provide you image of a PDF. 
Give me the plain text markdown output without backticks, using formatting to match the structure of the page as closely as possible. Only output the markdown and nothing else.
- Return relevant inline LaTeX or block LaTeX for math equations. 
- For diagrams, images and big figures, output the following tag: <image_here> where they appear. Do not describe what's in the images.
- Keep the section and subsection numbers. Include footnotes or references at the end of the document. If you encounter potential OCR errors or unclear text, represent them with [unclear] in the output. Ignore page headers and footers unless they contain essential information.
- If the page has a multi-column layout, process the text from left to right, top to bottom, as if it were a single column.
- Do not explain the output, just return it. If the page is empty, just write 'empty'.'''

BOUNDING_BOX_PROMPT = '''
give bounding box for relevant figures. output a json in the format without backticks. [ { "figure" : "name", "bbox" : [ y_min, x_min, y_max, x_max]}]
'''

MODEL = "google/gemini-flash-1.5"
print(MODEL)

def image_to_markdown(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }]
            }],
            max_tokens=4096
        )
        response = completion.choices[0].message.content
        print(response)
        return response
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return f"Error: Failed to process image {image_path}"

def get_bounding_boxes(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": BOUNDING_BOX_PROMPT
                }, {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }]
            }],
            max_tokens=1000
        )
        response = completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"Error getting bounding boxes: {str(e)}")
        return "Error: Failed to get bounding boxes"

def process_image(image_path, i, total_images):
    print(f"Processing image {i}/{total_images}...")
    print(image_path)
    markdown = image_to_markdown(image_path)
    bounding_boxes = get_bounding_boxes(image_path)
    print(bounding_boxes)
    return i, markdown, bounding_boxes


def parse_bounding_boxes(bounding_boxes_str):
    try:
        bounding_boxes = json.loads(bounding_boxes_str)
        return [bbox['bbox'] for bbox in bounding_boxes]
    except json.JSONDecodeError:
        print(f"Error parsing JSON: {bounding_boxes_str}")
        return []

def insert_coordinates(markdown, bounding_boxes):
    coordinates = parse_bounding_boxes(bounding_boxes)
    placeholder = '<image_here>'
    
    for coord in coordinates:
        if placeholder in markdown:
            replacement = f'<bbox>{coord[0]:.2f},{coord[1]:.2f},{coord[2]:.2f},{coord[3]:.2f}</bbox>'
            markdown = markdown.replace(placeholder, replacement, 1)
        else:
            print(f"Warning: More coordinates than {placeholder} tags")
            break

    # Check if there are unused tags
    remaining_placeholders = markdown.count(placeholder)
    if remaining_placeholders > 0:
        print(f"Warning: {remaining_placeholders} unused {placeholder} tags")

    # Check if there are unused coordinates
    used_coordinates = markdown.count('<bbox>')
    unused_coordinates = len(coordinates) - used_coordinates
    if unused_coordinates > 0:
        print(f"Warning: {unused_coordinates} unused coordinates")

    return markdown

def process_pdf_folder(pdf_name):
    images_folder = os.path.join(pdf_name, "images")
    markdown_folder = os.path.join(pdf_name, "markdown")
    Path(markdown_folder).mkdir(exist_ok=True)

    image_files = sorted([f for f in os.listdir(images_folder) if f.lower().endswith(('.jpeg', '.jpg', '.png'))])
    total_images = len(image_files)

    for i, image in enumerate(image_files, start=1):
        image_path = os.path.join(images_folder, image)
        i, markdown, bounding_boxes = process_image(image_path, i, total_images)
        
        updated_markdown = insert_coordinates(markdown, bounding_boxes)
        output_path = os.path.join(markdown_folder, f"page_{i:03d}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(updated_markdown)
        print(f"Page {i} markdown with coordinated image tags saved to {output_path}")

def process_all_pdfs(base_directory):
    for item in os.listdir(base_directory):
        item_path = os.path.join(base_directory, item)
        if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "images")):
            print(f"Processing folder: {item}")
            process_pdf_folder(item_path)

if __name__ == "__main__":
    base_directory = "."  # Current directory
    process_all_pdfs(base_directory)
    print("All PDF images have been processed and converted to markdown with coordinated image tags.")