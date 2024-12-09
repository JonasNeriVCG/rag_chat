import os
import json
import pymupdf
import pymupdf4llm
from dotenv import load_dotenv
from langchain.text_splitter import MarkdownTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings

def extract_pdf_metadata(file_path):
    """
    Extract comprehensive metadata from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
    
    Returns:
        dict: Extracted metadata
    """
    try:
        # Open the PDF file
        doc = pymupdf.open(file_path)
        
        # Extract basic metadata
        metadata = {
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "total_pages": len(doc),
            "file_size_bytes": os.path.getsize(file_path)
        }
        
        # Try to extract more detailed metadata from the PDF
        pdf_metadata = doc.metadata or {}
        
        # Map PDF-specific metadata
        metadata.update({
            "title": pdf_metadata.get("title", ""),
            "author": pdf_metadata.get("author", ""),
            "subject": pdf_metadata.get("subject", ""),
            "keywords": pdf_metadata.get("keywords", ""),
            "creator": pdf_metadata.get("creator", ""),
            "producer": pdf_metadata.get("producer", ""),
            "creation_date": pdf_metadata.get("creationDate", ""),
            "modification_date": pdf_metadata.get("modDate", "")
        })
        
        # Additional file system metadata
        stat = os.stat(file_path)
        metadata.update({
            "created_at": stat.st_ctime,
            "last_modified": stat.st_mtime,
            "last_accessed": stat.st_atime
        })
        
        return metadata
    
    except Exception as e:
        return {
            "filename": os.path.basename(file_path),
            "error": str(e)
        }

def process_pdfs(folder_path):
    """
    Process PDF files in the given folder and create JSON metadata files.
    
    Args:
        folder_path (str): Path to the folder containing PDFs
    
    Returns:
        list: List of processed documents with metadata
    """
    all_documents = []
    
    # Traverse through all folders and subfolders
    for root, dirs, files in os.walk(folder_path):
        pdf_files = [file for file in files if file.endswith(".pdf")]
        
        if not pdf_files:
            print(f"No PDF files found in folder: {root}")
            continue
        
        for pdf_file in pdf_files:
            file_path = os.path.join(root, pdf_file)
            print(f"Processing {file_path}...")
            
            # Extract metadata and create JSON sidecar file
            metadata = extract_pdf_metadata(file_path)
            
            # Create JSON sidecar file
            json_path = os.path.splitext(file_path)[0] + '.json'
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(metadata, json_file, indent=4, default=str)
            
            # Convert PDF to Markdown
            md_text = pymupdf4llm.to_markdown(file_path)
            
            # Split the Markdown text
            splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=1000)
            
            # Create documents with metadata
            documents = []
            for chunk in splitter.split_text(md_text):
                doc = Document(
                    page_content=chunk,
                    metadata=metadata  # Pass the entire metadata to each document chunk
                )
                documents.append(doc)
            
            # Append the created documents to the all_documents list
            all_documents.extend(documents)
    
    return all_documents

def main():
    """
    Main function to process PDFs and create vector database.
    """
    load_dotenv()
    folder_path = "documents_with_data"
    
    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
        return
    
    # Step 1: Process all PDFs
    all_documents = process_pdfs(folder_path)
    
    # Check if documents were created
    if not all_documents:
        print("No documents were created. Please check your PDF files.")
        return
    
    # Create the FAISS database
    db_path = "database.faiss"
    db = FAISS.from_documents(
        all_documents, OpenAIEmbeddings(model="text-embedding-3-large")
    )
    db.save_local(db_path)
    print(f"Database created and saved to {db_path}")

if __name__ == "__main__":
    main()