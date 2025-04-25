import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables from .env file
load_dotenv()

def setup_rag():
    # Define the directory structure
    current_dir = os.path.dirname(os.path.abspath(__file__))
    content_file = os.path.join(current_dir, "content.txt")
    persistent_directory = os.path.join(current_dir, "db", "chroma_db")
    
    
    # Check if the Chroma vector store already exists
    if not os.path.exists(persistent_directory):
        print("Persistent directory does not exist. Initializing vector store...")
        
        # Ensure the text file exists
        if not os.path.exists(content_file):
            raise FileNotFoundError(
                f"The file {content_file} does not exist. Please check the path."
            )
        
        # Read the text content from the file
        loader = TextLoader(content_file)
        documents = loader.load()
        
        # Split the document into chunks - using RecursiveCharacterTextSplitter for better results with technical content
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Smaller chunks for detailed pharmaceutical info
            chunk_overlap=100,  # Larger overlap to maintain context
            separators=["\n\n", "\n", ". ", " ", ""],  # Custom separators for pharmaceutical data
            length_function=len
        ) 
        docs = text_splitter.split_documents(documents)
        
        # Display information about the split documents
        print("\n--- Document Chunks Information ---")
        print(f"Number of document chunks: {len(docs)}")
        if docs:
            print(f"Sample chunk:\n{docs[0].page_content[:200]}...\n")
        
        # Create embeddings using Google's Generative AI (compatible with your Gemini model)
        print("\n--- Creating embeddings ---")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY"),  # Get API key from environment variable
            task_type="retrieval_query"  # Optimized for RAG applications
        )
        print("\n--- Finished creating embeddings ---")
        
        # Create the vector store and persist it automatically
        print("\n--- Creating vector store ---")
        db = Chroma.from_documents(
            docs, embeddings, persist_directory=persistent_directory)
        print("\n--- Finished creating vector store ---")
        print(f"Vector store created at: {persistent_directory}")
        
        return db
    else:
        print("Vector store already exists. No need to initialize.")
        print(f"Vector store location: {persistent_directory}")
        return None

if __name__ == "__main__":
    setup_rag()