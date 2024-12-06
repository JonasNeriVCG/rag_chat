import hashlib
import pymupdf  # PyMuPDF
import os
import re
import json
import shutil  # For copying files

def sanitize_filename(filename):
    # Convert to lowercase
    filename = filename.lower()
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove special characters (keep alphanumeric, underscores, and periods)
    filename = re.sub(r'[^a-z0-9_.]', '', filename)
    return filename

def generate_unique_id(metadata):
    # Serialize the metadata dictionary to a string
    metadata_string = json.dumps(metadata, sort_keys=True)  # Sort keys for consistent ordering
    
    # Generate a SHA-256 hash of the serialized string
    unique_id = hashlib.sha256(metadata_string.encode('utf-8')).hexdigest()
    return unique_id

def rename_pdfs(input_folder):
    # Loop through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):  # Check if the file is a PDF
            # Sanitize the filename without the extension
            sanitized_filename = sanitize_filename(filename[:-4])
            trimmed_filename = sanitized_filename[:50]

            new_filename = f"{trimmed_filename}.pdf"
            old_file_path = os.path.join(input_folder, filename)
            new_file_path = os.path.join(input_folder, new_filename)

            if old_file_path != new_file_path:
                os.rename(old_file_path, new_file_path)
                print(f'Renamed: {old_file_path} to {new_file_path}')

def extract_advanced_info(pdf_file, output_base_folder):
    base_name = os.path.splitext(os.path.basename(pdf_file))[0]
    max_length = 50
    if len(base_name) > max_length:
        base_name = base_name[:max_length]

    output_folder = os.path.join(output_base_folder, base_name)
    doc = pymupdf.open(pdf_file)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    metadata = doc.metadata
    print("Metadata:")
    print(metadata)

    unique_id = generate_unique_id(metadata)
    metadata['unique_id'] = unique_id  # Add unique identifier to metadata
    print(f"Unique Identifier: {unique_id}")

    num_pages = doc.page_count
    print(f"Number of pages: {num_pages}")

    # Extract full text and references
    full_text = ""
    for page_num in range(len(doc) - 1, -1, -1):
        page = doc.load_page(page_num)
        full_text = page.get_text() + full_text

    # Improved references extraction
    def clean_and_normalize_references(references_text):
        # Remove extra whitespace and newlines
        references_text = re.sub(r'\s+', ' ', references_text).strip()
        
        # Split references, handling potential multi-line references
        reference_list = []
        current_ref = []
        lines = references_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Check if line looks like a new reference (starts with author or number)
            if re.match(r'^[\[\d]+\s*[A-Z]', line) or re.match(r'^[A-Z]', line):
                # If we have a previous reference, join and add it
                if current_ref:
                    reference_list.append(' '.join(current_ref))
                    current_ref = []
                current_ref.append(line)
            elif line:  # Add non-empty lines to current reference
                current_ref.append(line)
        
        # Add the last reference
        if current_ref:
            reference_list.append(' '.join(current_ref))
        
        return reference_list

    def format_references(reference_list):
        # Apply some basic formatting
        formatted_refs = []
        for i, ref in enumerate(reference_list, 1):
            # Remove multiple spaces
            ref = re.sub(r'\s+', ' ', ref).strip()
            
            # Try to separate author, year, title, etc.
            formatted_ref = f"{i}. {ref}"
            formatted_refs.append(formatted_ref)
        
        return formatted_refs

    # Find references section
    ref_start_pattern = r"(References|Bibliography|Literature Cited)"
    references_text = ""
    start_index = None

    # Iterate through pages in reverse to find references section
    for page_num in range(len(doc) - 1, -1, -1):
        page = doc.load_page(page_num)
        text = page.get_text()

        # Search for references section header
        ref_match = re.search(ref_start_pattern, text, flags=re.IGNORECASE)
        if ref_match:
            # Find the exact index of the references section header
            header_pos = ref_match.start()
            
            # Extract text from the line with "References" onwards
            section_text = text[header_pos:]
            
            # Start extraction from this page
            start_index = page_num
            references_text = section_text
            
            # Continue extracting subsequent pages
            for subsequent_page_num in range(page_num + 1, len(doc)):
                subsequent_page = doc.load_page(subsequent_page_num)
                references_text += subsequent_page.get_text()
            
            break

    # Save the updated metadata with the unique identifier as the filename
    metadata_file_path = os.path.join(output_folder, f"{unique_id}.json")  # Use unique ID as the filename
    with open(metadata_file_path, "w", encoding="utf-8") as meta_file:
        json.dump(metadata, meta_file, ensure_ascii=False, indent=4)

    # Clean and format references
    if references_text:
        raw_references = clean_and_normalize_references(references_text)
        formatted_references = format_references(raw_references)

        # Save formatted references
        references_file_path = os.path.join(output_folder, "references.txt")
        with open(references_file_path, "w", encoding="utf-8") as ref_file:
            ref_file.write("\n\n".join(formatted_references))
        
        print(f"Formatted references saved to references.txt.")
    else:
        print("No references section found in the document.")

    # Save the original PDF to the output folder
    original_pdf_filename = os.path.basename(pdf_file)
    output_pdf_path = os.path.join(output_folder, original_pdf_filename)
    shutil.copyfile(pdf_file, output_pdf_path)
    print(f"Original PDF saved to {output_pdf_path}")

    # Extract images
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

def process_all_pdfs(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):
            pdf_file_path = os.path.join(input_folder, filename)
            print(f"Processing: {pdf_file_path}")
            extract_advanced_info(pdf_file_path, output_folder)

# Example usage
input_folder = r'C:\Users\Usuario\Desktop\rag_chat\documents'
output_folder = r'C:\Users\Usuario\Desktop\rag_chat\documents_with_data'

# First, rename the PDFs
rename_pdfs(input_folder)
# Then, process the renamed PDFs
process_all_pdfs(input_folder, output_folder)