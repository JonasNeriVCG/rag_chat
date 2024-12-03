Context-Aware Chat Assistant with Similarity Matching
This project consists of a Python-based system designed to process PDF documents, generate a FAISS vector database, and provide a chat interface that retrieves relevant document content and answers user queries in a context-aware manner. The project leverages LangChain, Ollama, and Gradio for its functionality.

Project Structure
project/
├── documents/              # Folder containing PDF files to process
├── db.py                   # Script for creating a FAISS database from PDF files
├── app.py                  # Gradio-based application for querying the FAISS database
├── requirements.txt        # Dependencies for the project
└── README.md               # Documentation for the project

Setup Instructions
Prerequisites
Ensure you have the following installed:

Python 3.9 or higher
A modern web browser to run the Gradio interface
Installation
Clone the repository and navigate to the project directory:

git clone <repository_url>
cd project
Install dependencies using pip:

pip install -r requirements.txt
Set up a .env file in the project root to configure any required environment variables. For example:

LANGCHAIN_API_KEY=<your-api-key>
Place the PDF files you want to process in the documents/ folder.

Usage
1. Create the FAISS Database
Run the db.py script to process the PDFs and generate the FAISS database:

python db.py
This script processes all PDFs in the documents/ folder and saves the resulting FAISS database as combined_nomic.faiss.
2. Launch the Chat Application
Run the app.py script to start the Gradio interface:

python app.py
Open the provided link in your web browser to access the chat interface.
Select the FAISS database and input a query to get answers based on the document content.
Dependencies
All dependencies are listed in requirements.txt. Install them using:

pip install -r requirements.txt
Key libraries used:

LangChain: For document processing, text splitting, and embeddings.
Gradio: For creating the chat-based user interface.
FAISS: For efficient vector storage and similarity search.
dotenv: For managing environment variables.
Features
PDF Processing: Extracts content from PDFs and creates a searchable vector database.
Context-Aware Responses: Incorporates context from documents and conversation memory to generate accurate and relevant answers.
Interactive Interface: User-friendly chat interface powered by Gradio.
Troubleshooting
No PDFs Found: Ensure that the documents/ folder contains PDF files. If not, create the folder and add the PDFs.

Missing Dependencies: If you encounter errors about missing modules, ensure you have installed all dependencies from requirements.txt.

Database Not Created: If db.py reports no database creation, check the documents/ folder for valid PDF files.

