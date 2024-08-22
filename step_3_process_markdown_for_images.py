import os
import re
import cv2
from pathlib import Path

def convert_coordinates(coords, img_width, img_height):
    # Assuming coords are scaled to 1000x1000
    scale_x = img_width / 1000.0
    scale_y = img_height / 1000.0
    
    y_min, x_min, y_max, x_max = [int(coord * scale_y) if i % 2 == 0 else int(coord * scale_x) for i, coord in enumerate(coords)]
    # y_min, x_min, y_max, x_max = [int(coord) for coord in coords]
    
    if y_max < y_min:
        y_min, y_max = y_max, y_min
    if x_max < x_min:
        x_min, x_max = x_max, x_min
    
    # Ensure coordinates are within image boundaries
    x_min = max(0, min(x_min, img_width))
    y_min = max(0, min(y_min, img_height))
    x_max = max(0, min(x_max, img_width))
    y_max = max(0, min(y_max, img_height))
    
    return {
        'x_min': x_min,
        'y_min': y_min,
        'x_max': x_max,
        'y_max': y_max
    }


def extract_image(image_path, coords, output_path, image_number, page_number, resize_dim=(1200, 1200)):
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
        converted_coords = convert_coordinates(coords, img_width, img_height)
        x_min = converted_coords['x_min']
        y_min = converted_coords['y_min']
        x_max = converted_coords['x_max']
        y_max = converted_coords['y_max']
        
        print(f"Converted cropping rectangle: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
        
        if x_max <= x_min or y_max <= y_min:
            print("Error: Invalid coordinates")
            return None
        
        # Draw bounding box on the original image
        cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        # Save the image with bounding boxes
        output_filename_bbox = f"image_page{page_number:02d}_{image_number:03d}_bbox.png"
        output_file_path_bbox = os.path.join(output_path, output_filename_bbox)
        cv2.imwrite(output_file_path_bbox, img)
        print(f"Image with bounding box saved to {output_file_path_bbox}")
        
        cropped = img[y_min:y_max, x_min:x_max]
        
        # Resize the cropped image
        # resized_cropped = cv2.resize(cropped, resize_dim, interpolation=cv2.INTER_AREA)
        
        output_filename = f"image_page{page_number:02d}_{image_number:03d}.png"
        output_file_path = os.path.join(output_path, output_filename)
        cv2.imwrite(output_file_path, cropped)
        print(f"Cropped and resized image saved to {output_file_path}")
        return output_filename
    except Exception as e:
        print(f"Error in extract_image: {str(e)}")
        return None

def process_markdown_file(markdown_path, images_folder, markdown_images_folder, processed_markdown_folder):
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()

    image_pattern = r'<bbox>([\d.,\s]+)</bbox>'
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
                content = content.replace(f'<bbox>{coords_str}</bbox>', f'![Image {page_number}_{i}]({relative_path})')
            else:
                print(f"Warning: Failed to extract image from {image_path}")
        else:
            print(f"Warning: Image file not found for {markdown_path}")

    output_path = os.path.join(processed_markdown_folder, os.path.basename(markdown_path))
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
            process_markdown_file(markdown_path, images_folder, markdown_images_folder, processed_markdown_folder)

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