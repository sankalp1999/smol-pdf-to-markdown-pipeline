import os
import re
import cv2
from pathlib import Path

def convert_coordinates(coords):
    y_min, x_min, y_max, x_max = [float(coord) for coord in coords]
    if y_max < y_min:
        y_min, y_max = y_max, y_min
    if x_max < x_min:
        x_min, x_max = x_max, x_min
    return {
        'x': x_min / 1000,
        'y': y_min / 1000,
        'width': (x_max - x_min) / 1000,
        'height': (y_max - y_min) / 1000
    }

def extract_image(image_path, coords, output_path, image_number, page_number):
    print(f"Extracting image from {image_path}")
    print(f"Original coordinates: {coords}")
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Unable to read image at {image_path}")
            return None
        
        img_height, img_width = img.shape[:2]
        print(f"Image dimensions: {img_width}x{img_height}")
        
        # Convert coordinates to pixel values
        converted_coords = convert_coordinates(coords)
        x = int(converted_coords['x'] * img_width)
        y = int(converted_coords['y'] * img_height)
        w = int(converted_coords['width'] * img_width)
        h = int(converted_coords['height'] * img_height)
        
        print(f"Converted cropping rectangle: x={x}, y={y}, w={w}, h={h}")
        
        if w <= 0 or h <= 0:
            print("Error: Invalid width or height")
            return None
        
        if x < 0 or y < 0 or x + w > img_width or y + h > img_height:
            print("Error: Cropping rectangle is outside image boundaries")
            return None
        
        cropped = img[y:y+h, x:x+w]
        output_filename = f"image_page{page_number:02d}_{image_number:03d}.png"
        output_file_path = os.path.join(output_path, output_filename)
        cv2.imwrite(output_file_path, cropped)
        print(f"Cropped image saved to {output_file_path}")
        return output_filename
    except Exception as e:
        print(f"Error in extract_image: {str(e)}")
        return None

def process_markdown_file(markdown_path, images_folder, output_folder, markdown_images_folder):
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()

    image_pattern = r'<image>([\d.,\s]+)</image>'
    image_tags = re.findall(image_pattern, content)
    
    page_number = int(os.path.basename(markdown_path).split('_')[1].split('.')[0])
    
    for i, coords_str in enumerate(image_tags, start=1):
        coords = [float(coord.strip()) for coord in coords_str.split(',')]
        print(f"Processing coordinate set {i}: {coords}")
        if len(coords) != 4:
            print(f"Warning: Invalid coordinates in {markdown_path}: {coords_str}")
            continue
        
        image_file = f"Page_{page_number:02d}.jpeg"
        image_path = os.path.join(images_folder, image_file)
        print(f"Looking for image file: {image_path}")
        
        if os.path.exists(image_path):
            extracted_image = extract_image(image_path, coords, markdown_images_folder, i, page_number)
            if extracted_image:
                relative_path = f"../markdown_images/{extracted_image}"
                content = content.replace(f'<image>{coords_str}</image>', f'![Image {page_number}_{i}]({relative_path})')
            else:
                print(f"Warning: Failed to extract image from {image_path}")
        else:
            print(f"Warning: Image file not found for {markdown_path}")

    output_path = os.path.join(output_folder, os.path.basename(markdown_path))
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_pdf_folder(pdf_folder):
    markdown_folder = os.path.join(pdf_folder, "markdown")
    images_folder = os.path.join(pdf_folder, "images")
    markdown_images_folder = os.path.join(pdf_folder, "markdown_images")
    processed_markdown_folder = os.path.join(pdf_folder, "processed_markdown")

    Path(markdown_images_folder).mkdir(exist_ok=True)
    Path(processed_markdown_folder).mkdir(exist_ok=True)

    for markdown_file in os.listdir(markdown_folder):
        if markdown_file.endswith('.md'):
            markdown_path = os.path.join(markdown_folder, markdown_file)
            process_markdown_file(markdown_path, images_folder, processed_markdown_folder, markdown_images_folder)

    print(f"Processed markdown files for {pdf_folder}")

def process_all_pdfs(base_directory):
    for item in os.listdir(base_directory):
        item_path = os.path.join(base_directory, item)
        if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "markdown")):
            print(f"Processing folder: {item}")
            process_pdf_folder(item_path)

if __name__ == "__main__":
    base_directory = "."  # Current directory
    process_all_pdfs(base_directory)
    print("All markdown files have been processed and images extracted.")