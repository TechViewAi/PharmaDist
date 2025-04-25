from flask import Flask, render_template, request, jsonify
import os
import time
import json
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Import the information retrieval tool
from rag.information_retrieval_tool import information_retrieval_tool

# Import the simplified order management tool
from Postgres.order_management import order_management_tool

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)
# Initialize the LLM using API key from environment variable
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.6,
    # max_retries=2,  # Limit retries to avoid excessive API calls
    # timeout=30  # Set a timeout
)

# Define the tools list
tools = [
    Tool(
        name="information_retrieval",
        func=information_retrieval_tool,
        description="Use this tool for any questions about our products, services, company information, pricing, availability, or any other information about our pharmaceutical distribution business. This tool returns raw information from our database."
    ),
    Tool(
    name="order_management",
    func=order_management_tool,
    description="""Execute SQL queries for order management operations. You must construct the SQL queries based on the database schema and business logic.

You can send your input in either of these formats:
1. As a plain JSON string:
{"query_type": "select", "sql_query": "SELECT * FROM products WHERE generic_name LIKE '%paracetamol%' LIMIT 5"}

2. Or as a JSON code block (the tool will automatically extract the JSON):
```json
{
    "query_type": "select",
    "sql_query": "SELECT * FROM products WHERE generic_name LIKE '%paracetamol%' LIMIT 5"
}
```

The query_type must be one of: "select", "insert", "update", or "delete".
For any DML operations (insert, update, delete), always use RETURNING clauses to get generated IDs."""
)
]

# Define the prompt template with detailed order management guidance
template = '''You are a professional pharmaceutical distributor chatbot helping vendors and dealers with:
1. Information about drugs, pharmaceutical products, and our distribution services
2. Order placement and cancellation

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

WHEN TO USE EACH TOOL:
- Use the information_retrieval tool ONLY when you need to fetch specific product information, pricing, or company policies from our RAG database
- Use the order_management tool ONLY when you need to execute a database query (SELECT, INSERT, UPDATE, DELETE)
- Do NOT use any tool when you simply need to ask the user a question or when providing general responses

IMPORTANT: When you need information directly from the user (such as their vendor ID, what product they want, quantity, etc.), DO NOT use any tool - just ask the user directly in your Final Answer.

DATABASE SCHEMA:
Our pharmaceutical database has these tables:

1. vendors (vendor_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, vendor_type VARCHAR(50) NOT NULL, contact_person VARCHAR(100), phone VARCHAR(20), email VARCHAR(100), address TEXT, created_at TIMESTAMP DEFAULT NOW())

2. products (product_id SERIAL PRIMARY KEY, generic_name VARCHAR(100) NOT NULL, brand_name VARCHAR(100), active_ingredients TEXT[] NOT NULL, pharmacological_class VARCHAR(100), atc_codes VARCHAR[], indications TEXT, contraindications TEXT, mechanism_of_action TEXT, dosage_form VARCHAR(50), strength VARCHAR(50), route_of_administration VARCHAR(50), packaging VARCHAR(100), synonyms TEXT[], description TEXT, manufacturer VARCHAR(100), storage_conditions VARCHAR(100), price_per_unit DECIMAL(10,2) NOT NULL)

3. batches (batch_id SERIAL PRIMARY KEY, product_id INT REFERENCES products(product_id), batch_number VARCHAR(50) NOT NULL, expiry_date DATE NOT NULL, on_hand INT NOT NULL DEFAULT 0, reserved INT NOT NULL DEFAULT 0)

4. orders (order_id SERIAL PRIMARY KEY, vendor_id INT REFERENCES vendors(vendor_id), order_date TIMESTAMP DEFAULT NOW(), status VARCHAR(20) NOT NULL DEFAULT 'Pending')

5. order_items (order_item_id SERIAL PRIMARY KEY, order_id INT REFERENCES orders(order_id), product_id INT REFERENCES products(product_id), batch_id INT REFERENCES batches(batch_id), qty_requested INT NOT NULL, qty_reserved INT NOT NULL)

ORDER MANAGEMENT BUSINESS LOGIC:
When a user wants to place an order, follow these steps carefully:

1. First, determine if the user is a new or existing vendor by directly asking them (do NOT use any tool for this)
   
2. If they are an existing vendor:
   - Ask for their vendor_id (do NOT use any tool for this)
   - IMMEDIATELY verify the vendor_id exists by using the order_management tool with a SELECT query.
   - If the vendor_id doesn't exist, inform the user and ask for a valid vendor_id or if they want to register as a new vendor

3. If they are a new vendor:
   - Ask for ALL required vendor details: name, vendor_type, contact_person, phone, email, address (do NOT use any tool for this)
   - ONLY after collecting ALL details, create the vendor record using the order_management tool with an INSERT query.

4. ONLY after confirming a valid vendor_id, ask what product they want to order, if they haven't already (do NOT use any tool for this)

5. IMMEDIATELY verify the requested product exists by using the information_retrieval tool to check if we carry that product
   - If the product doesn't exist in our catalog, inform the user and suggest them similar products using information_retrieval results.
   - If the product exists, retrieve its product_id from the information_retrieval results

6. ONLY after confirming the product exists, ask for the quantity they want to order, if they haven't already (do NOT use any tool for this)

7. Once you have the product name and quantity, check product availability:
   - Use information_retrieval tool to get the product_id
   - Use order_management tool to find batches with available stock: (on_hand - reserved) >= requested quantity
   - Select batches with earliest expiry date first

8. After confirming availability, proceed with the order:
   - If the user is a new vendor, use order_management tool to create a vendor record first
   - Use order_management tool to create an order with vendor_id and status 'Pending'
   - Use order_management tool to create order_items and update batch.reserved

For order cancellation:
1. Ask the user for their vendor_id and order_id
2. Use order_management tool to update the order status to cancelled. Realease reserved inventory by batches.reserved-=order_items.qty_reserved and DELETE row from order_items.

QUERY CONSTRUCTION GUIDELINES:
- Always use RETURNING clauses in INSERT statements to get generated IDs
- For inventory checks, calculate available stock as: (on_hand - reserved)

Remember:
- NEVER use "Action: None" - if you don't need to use a tool, go directly to Final Answer
- DO NOT use information_retrieval when you simply need to ask the user a question
- Only use order_management tool to execute actual SQL queries, not for conversation
- Always ask the user directly for any missing information before constructing queries
- For product information and general inquiries, use the information_retrieval tool
- Always verify vendor_id using the database BEFORE proceeding with product selection

Chat History:
{chat_history}

Begin!

Question: {input}
{agent_scratchpad}'''

# Create a function to format chat history as a string
def format_chat_history(messages):
    if not messages:
        return "No previous messages."
    
    history_str = ""
    for message in messages:
        if isinstance(message, HumanMessage):
            history_str += f"Human: {message.content}\n"
        elif isinstance(message, AIMessage):
            history_str += f"AI: {message.content}\n"
        elif isinstance(message, SystemMessage):
            # Optionally include system messages
            pass  # Skip system messages in the formatted history
    
    return history_str.strip()

# Update the prompt template to include chat_history
prompt = PromptTemplate.from_template(template)
prompt = prompt.partial(chat_history="")  # Default empty chat history

# Create the agent
agent = create_react_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    handle_parsing_errors=True,  # Add error handling
    max_iterations=8 # Increased iterations for complex order operations with multiple steps
)

# Initialize chat history
chat_history = []

# Set an initial system message
system_message = SystemMessage(content="""You are a pharmaceutical distributor chatbot. 
When users ask about products or company information, you will use the information_retrieval tool 
to get relevant documents, then craft a helpful response based on that information.

For order placement or cancellation, you must construct SQL queries step-by-step and use the order_management tool to execute them.""")

# Store the welcome message
welcome_message = """
Welcome to PharmaDist, your pharmaceutical distribution partner!

I can help you with:
1. Information about our pharmaceutical products and services
2. Placing or canceling orders

How can I assist you today?
"""

# Initialize chat history with system message
chat_history.append(system_message)
# Add AI welcome message to history
ai_welcome = AIMessage(content=welcome_message.strip())
chat_history.append(ai_welcome)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    global chat_history
    
    # Get user input from request
    data = request.json
    query = data.get('message', '')
    
    try:
        # Add user message to chat history
        chat_history.append(HumanMessage(content=query))
        
        # Format chat history for the prompt
        formatted_history = format_chat_history(chat_history[:-1])  # Exclude the latest message
        
        # Process with agent
        result = agent_executor.invoke({
            "input": query,  # Pass only the current query as input
            "chat_history": formatted_history  # Pass formatted history separately
        })
        
        response = result.get("output", "I'm sorry, I couldn't process that request.")
        
        # Add AI response to chat history
        chat_history.append(AIMessage(content=response))
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
        
        return jsonify({
            'message': response,
            'timestamp': time.strftime('%H:%M')
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        error_message = "I'm having some technical difficulties. Please try again."
        return jsonify({
            'message': error_message,
            'timestamp': time.strftime('%H:%M'),
            'error': True
        })

# API endpoint to reset the chat
@app.route('/api/reset', methods=['POST'])
def reset_chat():
    global chat_history
    # Reset chat history
    chat_history = [system_message, ai_welcome]
    return jsonify({'success': True, 'message': 'Chat history has been reset'})

if __name__ == '__main__':
    app.run(debug=True)