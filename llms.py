

from langchain_ollama import ChatOllama
def get_gmail_model():
    return ChatOllama(
        model="llama3.2"
    )

