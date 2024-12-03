import gradio as gr
import os
import time
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.llms import Ollama
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

llm = Ollama(model="llama3.1")

memory = []

main_prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful assistant. Your task is to reply to user queries as completely and extensively as possible.
    <context>
    {context}
    </context>
    Previous questions and answers: {memory}
    New question: {input}
    """
)


def load_database(db_path, top_k=30):
    """
    Load the FAISS database and initialize the retriever.

    Args:
        db_path (str): Path to the FAISS database file.
        top_k (int): Number of top similar documents to retrieve.

    Returns:
        retriever: A retriever object for similarity search.
    """
    db = FAISS.load_local(
        db_path,
        OllamaEmbeddings(model="nomic-embed-text"),
        allow_dangerous_deserialization=True,
    )
    retriever = db.as_retriever(search_kwargs={"k": top_k})
    return retriever


def ask_question(retriever, question, memory, top_k=30):
    """
    Generate a response to a user's question based on retrieved documents and memory.

    Args:
        retriever: The retriever object for document similarity search.
        question (str): The user's question.
        memory (list): Previous questions and answers stored in memory.
        top_k (int): Number of top similar documents to use (default: 30).

    Returns:
        str: The generated response.
    """
    similar_docs = retriever.get_relevant_documents(question)

    context = "\n\n".join([doc.page_content for doc in similar_docs])
    context_memory = "\n".join(
        [f"Question: {q['question']}\nAnswer: {q['answer']}" for q in memory]
    )

    prompt_input = {"context": context, "memory": context_memory, "input": question}

    response = llm.predict(main_prompt.format_prompt(**prompt_input).to_string())
    return response.strip()


def letter_by_letter_response(db_name, question):
    """
    Generate the response letter by letter for a Gradio interface.

    Args:
        db_name (str): The name of the FAISS database (without the extension).
        question (str): The user's question.

    Yields:
        str: The response, letter by letter.
    """
    global memory
    db_path = f"{db_name}.faiss"

    retriever = load_database(db_path)
    answer = ask_question(retriever, question, memory)

    response_text = ""
    for letter in answer:
        response_text += letter
        time.sleep(0.005)
        yield response_text

    memory.append({"question": question, "answer": answer})


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
    output = gr.Textbox(label="Answer", interactive=False)

    submit_button = gr.Button("Send")
    submit_button.click(
        fn=letter_by_letter_response,
        inputs=[db_input, question_input],
        outputs=output,
    )

demo.launch()
