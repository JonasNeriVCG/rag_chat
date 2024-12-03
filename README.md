# PDF-based Context-Aware Chat Assistant

This project allows you to process PDFs into a FAISS vector database and interact with it via a Gradio-powered chat interface. The workflow consists of two main Python files: `db.py` for processing PDFs and `app.py` for creating the interactive chat.

## Setup Instructions

### 1. Clone the Repository
Clone this repository to your local machine:

```bash
git clone https://github.com/JonasNeriVCG/rag_chat.git
```

### 2. Create a Virtual Environment

Create a Python virtual environment to manage the dependencies:

```bash
python -m venv venv
```

Activate the virtual environment:

* On Linux/Mac:

```bash
source venv/bin/activate
```

* On Windows:

```bash
venv\Scripts\activate
```

### 3. Install the required dependencies from the requirements.txt file:

```bash
pip install -r requirements.txt
```

### 4. Install Ollama and LLM Models

To run the app, you need to download Ollama from the official website and install it:

1. Go to [Ollama's website](https://ollama.com/) and download the installer for your operating system.
2. Follow the installation instructions to install Ollama.

Once Ollama is installed, you will need to download the Llama 3.1 LLM and the nomic-embed-text embedding model:

1. Open your terminal or command prompt.
2. Use the Ollama CLI to download the models by running the following commands:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

These models will be used in the `db.py` and `app.py` script for creating the FAISS database and generating responses based on it.

### 5. Run the `db.py` Script:

Before running the chat application, you need to process the PDFs into the FAISS database. To do this, run the `db.py` script:

```bash
python db.py
```

This will load all PDFs from the `documents/` folder, process them into a FAISS vector database, and save the resulting database as a `.faiss` file.

### 6. Run the `app.py` Script:

After the database is created, you can launch the Gradio-powered chat interface by running:

```bash
python app.py
```

This will start the app, and you can interact with it via the web interface. Select the FAISS database from the dropdown menu and ask any question related to the contents of the PDFs.

### Project Structure Overview

```bash
rag_chat/
│
├── app.py                # Gradio app for querying the FAISS database
├── db.py                 # Script for processing PDFs into a FAISS database
├── documents/            # Folder containing PDF files to be processed
└── requirements.txt      # List of dependencies for the project
```

### Notes

* Make sure that the PDFs you want to process are placed in the `documents/` folder.
* The database is created once using `db.py` and can be reused for querying with `app.py`.
* You can customize the PDF processing or chat functionality by modifying the `db.py` or `app.py` scripts.

### License

This project is open-source and available under the MIT License.
