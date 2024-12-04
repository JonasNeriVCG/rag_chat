import pymupdf  # PyMuPDF
import os
import re

def sanitize_filename(filename):
    # Convert to lowercase
    filename = filename.lower()
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove special characters (keep alphanumeric, underscores, and periods)
    filename = re.sub(r'[^a-z0-9_.]', '', filename)
    return filename

def rename_pdfs(input_folder):
    # Loop through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):  # Check if the file is a PDF
            # Sanitize the filename without the extension
            sanitized_filename = sanitize_filename(filename[:-4])  # Exclude '.pdf' for sanitization
            trimmed_filename = sanitized_filename[:50]  # Truncate to 50 characters

            # Re-add the .pdf extension
            new_filename = f"{trimmed_filename}.pdf"

            # Create full paths for renaming
            old_file_path = os.path.join(input_folder, filename)
            new_file_path = os.path.join(input_folder, new_filename)

            # Rename the file if the new name is different
            if old_file_path != new_file_path:
                os.rename(old_file_path, new_file_path)
                print(f'Renamed: {old_file_path} to {new_file_path}')

def extract_advanced_info(pdf_file, output_base_folder):
    # Get the base name of the PDF file (without extension) to create the output folder
    base_name = os.path.splitext(os.path.basename(pdf_file))[0]
    
    # Truncate the base name to a maximum of 50 characters to avoid long filenames
    max_length = 50
    if len(base_name) > max_length:
        base_name = base_name[:max_length]

    output_folder = os.path.join(output_base_folder, base_name)  # Create path for output folder

    # Open the PDF
    doc = pymupdf.open(pdf_file)

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Metadata
    metadata = doc.metadata
    print("Metadata:")
    print(metadata)

    # Number of pages
    print(f"Number of pages: {doc.page_count}")

    # Extract text from each page in reverse order
    full_text = ""
    for page_num in range(len(doc) - 1, -1, -1):
        page = doc.load_page(page_num)
        full_text = page.get_text() + full_text
    
    # Regular expression to find the start of the references section
    ref_start_pattern = r"(References|Bibliography)"
    
    start_index = None
    for page_num in range(len(doc) - 1, -1, -1):
        page = doc.load_page(page_num)
        text = page.get_text()

        if re.search(ref_start_pattern, text, flags=re.IGNORECASE):
            start_index = page_num
            break

    if start_index is not None:
        references_text = ""
        for page_num in range(start_index, len(doc)):
            page = doc.load_page(page_num)
            references_text += page.get_text()
    else:
        references_text = ""

    # Save the references text and metadata
    print("References:")
    print(references_text)

    with open(os.path.join(output_folder, "references.txt"), "w", encoding="utf-8") as ref_file:
        ref_file.write("Metadata:\n")
        ref_file.write(str(metadata) + "\n\n")
        ref_file.write("References:\n")
        ref_file.write(references_text)

    # Extract embedded images
    print("Saved Images:")
    image_counter = 0
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)

            image_bytes = base_image["image"]
            image_filename = os.path.join(output_folder, f"image{image_counter}.png")
            
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)
            print(f"{image_counter}: {image_filename}")
            image_counter += 1

# Main function to process all PDFs in the documents folder
def process_all_pdfs(input_folder, output_folder):
    # Create the output base folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):  # Check if the file is a PDF
            pdf_file_path = os.path.join(input_folder, filename)
            print(f"Processing: {pdf_file_path}")
            extract_advanced_info(pdf_file_path, output_folder)

# Example usage
input_folder = r'C:\Users\Usuario\Desktop\rag_chat\documents'
output_folder = r'C:\Users\Usuario\Desktop\rag_chat\documents_data'

# First, rename the PDFs
rename_pdfs(input_folder)
# Then, process the renamed PDFs
process_all_pdfs(input_folder, output_folder)