import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS


def process_pdfs(folder_path, db_name="combined_nomic"):
    db_path = f"{db_name}.faiss"

    if not os.path.exists(db_path):
        print("Processing all PDFs...")
        all_documents = []

        pdf_files = [
            os.path.join(folder_path, file)
            for file in os.listdir(folder_path)
            if file.endswith(".pdf")
        ]

        if not pdf_files:
            print(f"No PDF files found in folder: {folder_path}")
            return

        for file_path in pdf_files:
            print(f"Loading {file_path}...")
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=500
            )
            documents = text_splitter.split_documents(docs)
            all_documents.extend(documents)

        print("Creating the combined database...")
        db = FAISS.from_documents(
            all_documents, OllamaEmbeddings(model="nomic-embed-text")
        )
        db.save_local(db_path)
        print(f"Combined database saved to {db_path}")
    else:
        print(f"Database already exists at {db_path}")


if __name__ == "__main__":
    load_dotenv()
    folder_path = "documents"

    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
    else:
        process_pdfs(folder_path)
        print("Database creation for all PDFs is complete.")
