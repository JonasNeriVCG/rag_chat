import gradio as gr
import os
import re
import subprocess
import sys
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)

main_prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful assistant. Your task is to reply to user queries as completely and extensively as possible.
    <context>
    {context}
    </context>
    New question: {input}
    """
)

def ensure_faiss_database():
    """Ensure that at least one FAISS database is present, otherwise run preprocessing and database creation."""
    faiss_files = [f for f in os.listdir() if f.endswith(".faiss")]
    if not faiss_files:
        print("No FAISS database found. Running preprocessing and database creation scripts...")
        # Use the current Python executable explicitly
        python_executable = sys.executable
        subprocess.run([python_executable, "preprocess.py"], check=True)
        subprocess.run([python_executable, "db.py"], check=True)
        print("FAISS database created.")
    else:
        print("FAISS database found. Proceeding with the application.")

def load_database(db_path):
    db = FAISS.load_local(
        db_path,
        OpenAIEmbeddings(model="text-embedding-3-large"),
        allow_dangerous_deserialization=True,
    )
    return db

def extract_references_and_update_metadata(docs_and_scores):
    updated_docs_and_scores = []
    for doc, score in docs_and_scores:
        text = doc.page_content
        references = set()
        matches = re.findall(r'\[(.*?)\]', text)
        for match in matches:
            parts = match.split(',')
            for part in parts:
                part = part.strip()
                if '–' in part or '-' in part:
                    try:
                        part = part.replace('–', '-').replace('—', '-')
                        start, end = map(int, part.split('-'))
                        references.update(range(start, end + 1))
                    except ValueError:
                        pass
                else:
                    try:
                        references.add(int(part))
                    except ValueError:
                        pass
        doc.metadata["references"] = ", ".join(map(str, sorted(references)))
        updated_docs_and_scores.append((doc, score))
    return updated_docs_and_scores

def generate_stepback_question(question):
    prompt = f"""
    You are an expert at taking a specific question and extracting a more generic question that gets at \
    the underlying principles needed to answer the specific question.
    If you don't recognize a word or acronym to not try to rewrite it.
    Write concise questions.: {question}"""
    stepback_question = llm.invoke(prompt).strip()
    return stepback_question

def ask_question(db, question, top_k=5):
    stepback_question = generate_stepback_question(question)
    docs_and_scores = db.similarity_search_with_score(stepback_question, k=top_k)
    docs_and_scores = extract_references_and_update_metadata(docs_and_scores)
    
    formatted_chunks = []
    for i, (doc, score) in enumerate(docs_and_scores, start=1):
        chunk_content = doc.page_content
        references = doc.metadata.get("references", "N/A")
        
        # Constructing metadata info with line breaks
        metadata_info = (
            f"Title: {doc.metadata.get('title', 'N/A')}\n"
            f"Author: {doc.metadata.get('author', 'N/A')}\n"
            f"Keywords: {doc.metadata.get('keywords', 'N/A')}"
        )
        
        formatted_chunks.append(
            f"Chunk {i} (Similarity: {score:.4f}):\n\n{chunk_content}\n\nMetadata:\n{metadata_info}\n\nReferences: {references}"
        )
    
    context = "\n\n".join([doc.page_content for doc, _ in docs_and_scores])
    prompt_input = {"context": context, "input": question}
    response = llm.invoke(main_prompt.format_prompt(**prompt_input).to_string())
    return response.strip(), "\n\n".join(formatted_chunks), stepback_question

def generate_response(db_name, question):
    db_path = f"{db_name}.faiss"
    db = load_database(db_path)
    answer, formatted_context, stepback_question = ask_question(db, question)
    return answer, formatted_context, stepback_question

def get_database_names():
    return [os.path.splitext(f)[0] for f in os.listdir() if f.endswith(".faiss")]

# Ensure FAISS database is available
ensure_faiss_database()

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
    stepback_output = gr.Textbox(label="Stepback Question", interactive=False)

    submit_button = gr.Button("Send")
    submit_button.click(
        fn=generate_response,
        inputs=[db_input, question_input],
        outputs=[answer_output, context_output, stepback_output],
    )

demo.launch()
