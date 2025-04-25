import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables from .env
load_dotenv()

def initialize_vectorstore():
    """Initialize and return the Chroma vector store."""
    # Define the persistent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    persistent_directory = os.path.join(current_dir, "db", "chroma_db")
    
    # Define the embedding model
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        task_type="retrieval_query"
    )
    
    # Load the existing vector store with the embedding function
    db = Chroma(persist_directory=persistent_directory,
                embedding_function=embeddings)
    
    return db

def information_retrieval_tool(query: str) -> str:
    """
    Tool for retrieving relevant documents about products or the distributor.
    This tool only returns the raw document chunks, not a processed response.
    
    Args:
        query: The user's query about products, services, or company information
        
    Returns:
        A string containing the relevant document chunks
    """
    try:
        # Initialize the vector store
        db = initialize_vectorstore()
        
        # Retrieve relevant documents based on the query
        retriever = db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3},  # Retrieve top 3 most relevant chunks
        )
        relevant_docs = retriever.invoke(query)
        
        # Check if any documents were retrieved
        if not relevant_docs:
            return "No relevant information found in our database."
        
        # Format the relevant documents as a string
        docs_str = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
        return f"Relevant information from our database:\n\n{docs_str}"
        
    except Exception as e:
        print(f"Error in information_retrieval_tool: {str(e)}")
        return "Error retrieving information from the database."