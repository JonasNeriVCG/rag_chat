import requests
import json
import hashlib
import pymupdf  # PyMuPDF
import os
import re
import shutil  # For copying files
import time  # For implementing retry delays

# === Utility Functions ===
def sanitize_filename(filename):
    filename = filename.lower()
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^a-z0-9_.]', '', filename)
    return filename

def generate_unique_id(metadata):
    metadata_string = json.dumps(metadata, sort_keys=True)
    unique_id = hashlib.sha256(metadata_string.encode('utf-8')).hexdigest()
    return unique_id

# === Retry Decorator ===
def retry_request(func):
    def wrapper(*args, **kwargs):
        max_retries = 10
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(1)  # Wait 1 second before retrying
        print("Max retries reached. Request failed.")
        return None
    return wrapper

# === Semantic Scholar Functions ===
@retry_request
def fetch_with_retries(url, params=None):
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
    return response.json()

def get_paper_references(paper_title):
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": paper_title,
        "limit": 1,
        "fields": "title,referenceCount,references,url,authors"
    }

    try:
        search_data = fetch_with_retries(search_url, params)

        if not search_data.get('data'):
            print(f"No paper found with title: {paper_title}")
            return []

        paper = search_data['data'][0]
        paper_id = paper['paperId']
        references_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references"

        ref_params = {"fields": "title,authors,url,year,referenceCount"}
        references_data = fetch_with_retries(references_url, params=ref_params)

        references = []
        for ref in references_data.get('data', []):
            reference = ref.get('citedPaper', {})
            references.append({
                'title': reference.get('title', 'N/A'),
                'authors': [author.get('name', 'Unknown') for author in reference.get('authors', [])],
                'year': reference.get('year', 'N/A'),
                'url': reference.get('url', ''),
                'referenceCount': reference.get('referenceCount', 0)
            })
        return references

    except Exception as e:
        print(f"Error fetching references: {e}")
        return []

def save_semantic_scholar_references(references, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as ref_file:
            json.dump(references, ref_file, ensure_ascii=False, indent=4)
        print(f"Semantic Scholar references saved to {output_path}")
    except Exception as e:
        print(f"Error saving Semantic Scholar references: {e}")

# === PDF References Extraction Functions ===
def extract_references_from_pdf(doc):
    ref_start_pattern = r"(References|Bibliography|Literature Cited)"
    references_text = ""
    start_index = None

    for page_num in range(len(doc) - 1, -1, -1):
        page = doc.load_page(page_num)
        text = page.get_text()

        ref_match = re.search(ref_start_pattern, text, flags=re.IGNORECASE)
        if ref_match:
            header_pos = ref_match.start()
            section_text = text[header_pos:]
            start_index = page_num
            references_text = section_text

            for subsequent_page_num in range(page_num + 1, len(doc)):
                subsequent_page = doc.load_page(subsequent_page_num)
                references_text += subsequent_page.get_text()
            break

    references_list = clean_and_normalize_references(references_text)
    return references_list

def clean_and_normalize_references(references_text):
    references_text = re.sub(r'\s+', ' ', references_text).strip()
    reference_list = []
    current_ref = []
    lines = references_text.split('\n')

    for line in lines:
        line = line.strip()
        if re.match(r'^[\[\d]+\s*[A-Z]', line) or re.match(r'^[A-Z]', line):
            if current_ref:
                reference_list.append(' '.join(current_ref))
                current_ref = []
            current_ref.append(line)
        elif line:
            current_ref.append(line)

    if current_ref:
        reference_list.append(' '.join(current_ref))
    return reference_list

def format_references(reference_list):
    formatted_refs = []
    for i, ref in enumerate(reference_list, 1):
        ref = re.sub(r'\s+', ' ', ref).strip()
        formatted_ref = f"{i}. {ref}"
        formatted_refs.append(formatted_ref)
    return formatted_refs

# === Image Extraction Function ===
def extract_images(doc, output_folder):
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
            print(f"Extracted image saved to {image_filename}")
            image_counter += 1

# === Main Extraction Function ===
def extract_and_fetch_references(pdf_file, output_base_folder):
    base_name = os.path.splitext(os.path.basename(pdf_file))[0]
    max_length = 50
    if len(base_name) > max_length:
        base_name = base_name[:max_length]

    output_folder = os.path.join(output_base_folder, base_name)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Copy the source PDF to the output folder
    output_pdf_path = os.path.join(output_folder, os.path.basename(pdf_file))
    shutil.copy(pdf_file, output_pdf_path)
    print(f"Source PDF saved to {output_pdf_path}")

    doc = pymupdf.open(pdf_file)
    metadata = doc.metadata
    unique_id = generate_unique_id(metadata)
    metadata['unique_id'] = unique_id

    metadata_file_path = os.path.join(output_folder, f"{unique_id}.json")
    with open(metadata_file_path, "w", encoding="utf-8") as meta_file:
        json.dump(metadata, meta_file, ensure_ascii=False, indent=4)
    print(f"Metadata saved to {metadata_file_path}")

    paper_title = metadata.get('title', 'Unknown Title')
    print(f"Extracted Title: {paper_title}")

    references_file_path = os.path.join(output_folder, "references.txt")

    if paper_title and paper_title != 'Unknown Title':
        semantic_references = get_paper_references(paper_title)

        if semantic_references:
            references_output_path = os.path.join(output_folder, "semantic_references.json")
            save_semantic_scholar_references(semantic_references, references_output_path)
            print(f"Semantic Scholar references saved for: {paper_title}")
        else:
            print("No references found via API. Extracting from PDF...")
            raw_references = extract_references_from_pdf(doc)
            formatted_references = format_references(raw_references)
            with open(references_file_path, "w", encoding="utf-8") as ref_file:
                ref_file.write("\n\n".join(formatted_references))
            print(f"Extracted references saved to {references_file_path}")
    else:
        print("No title found. Extracting references directly from PDF...")
        raw_references = extract_references_from_pdf(doc)
        formatted_references = format_references(raw_references)
        with open(references_file_path, "w", encoding="utf-8") as ref_file:
            ref_file.write("\n\n".join(formatted_references))
        print(f"Extracted references saved to {references_file_path}")

    extract_images(doc, output_folder)

# === Workflow Functions ===
def process_all_pdfs(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):
            pdf_file_path = os.path.join(input_folder, filename)
            print(f"Processing: {pdf_file_path}")
            extract_and_fetch_references(pdf_file_path, output_folder)

# Example Usage
input_folder = r'C:\Users\Usuario\Desktop\rag_chat\documents'
output_folder = r'C:\Users\Usuario\Desktop\rag_chat\documents_with_data'

process_all_pdfs(input_folder, output_folder)