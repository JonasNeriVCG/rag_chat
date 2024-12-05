import os
from dotenv import load_dotenv
import pymupdf4llm
from langchain.text_splitter import MarkdownTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

def process_pdfs(folder_path):
    all_documents = []

    # Traverse through all folders and subfolders
    for root, dirs, files in os.walk(folder_path):
        pdf_files = [file for file in files if file.endswith(".pdf")]

        if not pdf_files:
            print(f"No PDF files found in folder: {root}")
            continue

        for pdf_file in pdf_files:
            file_path = os.path.join(root, pdf_file)
            print(f"Loading {file_path}...")

            # Convert PDF to Markdown
            md_text = pymupdf4llm.to_markdown(file_path)  # Get markdown for all pages

            # Split the Markdown text
            splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=1000)
            documents = splitter.create_documents([md_text])

            # Append the created documents to the all_documents list
            all_documents.extend(documents)  # Add this line to store documents

    return all_documents

if __name__ == "__main__":
    load_dotenv()
    folder_path = "documents_with_data"

    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
    else:
        # Step 1: Process all PDFs
        all_documents = process_pdfs(folder_path)

        # Check if documents were created
        if not all_documents:
            print("No documents were created. Please check your PDF files.")
        else:
            # Create the FAISS database
            db_path = "combined_nomic.faiss"
            db = FAISS.from_documents(
                all_documents, OllamaEmbeddings(model="nomic-embed-text")
            )
            db.save_local(db_path)
            print(f"Database created and saved to {db_path}")