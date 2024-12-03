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

### 4. Run the `db.py` Script

Before running the chat application, you need to process the PDFs into the FAISS database. To do this, run the `db.py` script:

```bash
python db.py
```

This will load all PDFs from the `documents/` folder, process them into a FAISS vector database, and save the resulting database as a `.faiss` file.
