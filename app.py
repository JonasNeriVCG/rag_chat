import gradio as gr
import os
import re
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

llm = Ollama(model="llama3.1")

main_prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful assistant. Your task is to reply to user queries as completely and extensively as possible.
    <context>
    {context}
    </context>
    New question: {input}
    """
)

def load_database(db_path):
    """
    Load the FAISS database and initialize the retriever.

    Args:
        db_path (str): Path to the FAISS database file.

    Returns:
        db: The FAISS database object for similarity search.
    """
    db = FAISS.load_local(
        db_path,
        OllamaEmbeddings(model="nomic-embed-text"),
        allow_dangerous_deserialization=True,
    )
    return db

import re

def extract_references_and_update_metadata(docs_and_scores):
    """
    Extract references from chunk text and add them to the document metadata.

    Args:
        docs_and_scores (list): A list of tuples where each tuple contains a document and its similarity score.

    Returns:
        list: The updated list of documents and scores with references added to metadata.
    """
    updated_docs_and_scores = []

    for doc, score in docs_and_scores:
        text = doc.page_content
        references = set()  # To avoid duplicates

        # Match all bracketed content
        matches = re.findall(r'\[(.*?)\]', text)  # Captures content within brackets
        
        for match in matches:
            # Split content by commas to handle mixed cases like [5, 10-15]
            parts = match.split(',')
            for part in parts:
                part = part.strip()  # Remove whitespace
                if '-' in part:  # Handle ranges like [10-15]
                    try:
                        start, end = map(int, part.split('-'))
                        references.update(range(start, end + 1))  # Add range of numbers
                    except ValueError:
                        pass  # Skip malformed ranges
                else:  # Handle single numbers like [5]
                    try:
                        references.add(int(part))
                    except ValueError:
                        pass  # Skip malformed numbers

        # Add references to metadata
        doc.metadata["references"] = ", ".join(map(str, sorted(references)))
        updated_docs_and_scores.append((doc, score))

    return updated_docs_and_scores

def ask_question(db, question, top_k=30):
    """
    Generate a response to a user's question based on retrieved documents.

    Args:
        db: The FAISS database object for similarity search.
        question (str): The user's question.
        top_k (int): Number of top similar documents to use (default: 30).

    Returns:
        tuple: A tuple containing the response and the retrieved chunks with metadata.
    """
    docs_and_scores = db.similarity_search_with_score(question, k=top_k)

    # Extract references and update metadata
    docs_and_scores = extract_references_and_update_metadata(docs_and_scores)

    # Format retrieved chunks with metadata and scores
    formatted_chunks = []
    for i, (doc, score) in enumerate(docs_and_scores, start=1):
        chunk_label = f"Chunk {i} (Similarity: {score:.4f})"
        metadata = "\n".join(
            [f"{key}: {value}" for key, value in doc.metadata.items()]
        )
        chunk_content = doc.page_content
        formatted_chunks.append(
            f"{chunk_label}:\n{chunk_content}\nMetadata:\n{metadata}\n"
        )

    context = "\n\n".join([doc.page_content for doc, _ in docs_and_scores])
    prompt_input = {"context": context, "input": question}

    response = llm.predict(main_prompt.format_prompt(**prompt_input).to_string())
    return response.strip(), "\n\n".join(formatted_chunks)

def generate_response(db_name, question):
    """
    Generate the response and retrieve the context for a Gradio interface.

    Args:
        db_name (str): The name of the FAISS database (without the extension).
        question (str): The user's question.

    Returns:
        tuple: The response and the formatted retrieved context.
    """
    db_path = f"{db_name}.faiss"
    db = load_database(db_path)
    answer, formatted_context = ask_question(db, question)
    return answer, formatted_context

def get_database_names():
    """
    Retrieve the names of available FAISS database files in the current directory.

    Returns:
        list: A list of database names without file extensions.
    """
    return [os.path.splitext(f)[0] for f in os.listdir() if f.endswith(".faiss")]

# Gradio interface
with gr.Blocks() as demo:
    gr.Markdown(
        """
        # Context-aware Chat Assistant with Similarity Matching
        Select your saved FAISS database and ask any question about its contents.
        """
    )
    db_names = get_database_names()
    db_input = gr.Dropdown(choices=db_names, label="Select saved FAISS database")
    question_input = gr.Textbox(
        label="Ask a question", placeholder="Enter your question here..."
    )
    answer_output = gr.Textbox(label="Answer", interactive=False)
    context_output = gr.Textbox(label="Retrieved Context", interactive=False, lines=10)

    submit_button = gr.Button("Send")
    submit_button.click(
        fn=generate_response,
        inputs=[db_input, question_input],
        outputs=[answer_output, context_output],
    )

demo.launch()