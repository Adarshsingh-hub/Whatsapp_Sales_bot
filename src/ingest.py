import logging
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_documents(data_path: str) -> list:
    documents = []
    path = Path(data_path)
    
    for pdf in path.glob("**/*.pdf"):
        documents.extend(PyPDFLoader(str(pdf)).load())
        logger.info(f"Loaded: {pdf.name}")
    
    for txt in path.glob("**/*.txt"):
        documents.extend(TextLoader(str(txt), encoding="utf-8").load())
        logger.info(f"Total documents loaded: {len(documents)}")
        
    return documents

def chunk_documents(documents: list) -> list:
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150, length_function = len, separators= ["\n\n", "\n", ".", " "])
    chunks = splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunks")
    
    return chunks

def build_vectorstore(chunks: list) -> Chroma:
    embeddings = OpenAIEmbeddings(
    model=config.EMBED_MODEL,openai_api_key=config.OPENAI_API_KEY)
    vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=config.CHROMA_PATH
    )
    vectorstore.persist()
    logger.info("Vector store saved.")
    
    return vectorstore

def run_ingestion():
    docs = load_documents(config.DATA_PATH)
    chunks = chunk_documents(docs)
    build_vectorstore(chunks)
    print("Ingestion complete. Ready to chat")


if __name__ == "__main__":
    run_ingestion()
    
        