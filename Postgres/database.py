import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from typing import Dict, List, Union, Optional, Tuple, Any

# Load environment variables
load_dotenv()

# Database connection parameters
db_params = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME")
}

def execute_dml_query(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a DML query (INSERT, UPDATE, DELETE) constructed by the LLM.
    
    Args:
        query: The SQL query string
        params: Optional parameters for parameterized queries to prevent SQL injection
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if the operation succeeded
        - operation_type: The type of DML operation (INSERT, UPDATE, DELETE)
        - affected_rows: Number of rows affected
        - returned_data: Any data returned by the operation (e.g., RETURNING clause)
        - error: Error message if the operation failed
    """
    result = {
        "success": False,
        "operation_type": None,
        "affected_rows": 0,
        "returned_data": None,
        "error": None
    }
    
    # Determine operation type from query
    query_upper = query.strip().upper()
    if query_upper.startswith("INSERT"):
        result["operation_type"] = "INSERT"
    elif query_upper.startswith("UPDATE"):
        result["operation_type"] = "UPDATE"
    elif query_upper.startswith("DELETE"):
        result["operation_type"] = "DELETE"
    else:
        result["error"] = "Unsupported operation. Only INSERT, UPDATE, and DELETE operations are allowed."
        return result
    
    # Connect to the database
    connection = None
    try:
        connection = psycopg2.connect(**db_params)
        
        # Create a cursor that returns results as dictionaries
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Execute the query
            cursor.execute(query, params)
            
            # Get the number of affected rows
            result["affected_rows"] = cursor.rowcount
            
            # If the query has a RETURNING clause, fetch the results
            if "RETURNING" in query_upper:
                result["returned_data"] = [dict(row) for row in cursor.fetchall()]
            
            # Commit the transaction
            connection.commit()
            
            result["success"] = True
            
    except Exception as e:
        result["error"] = str(e)
        # Rollback if there was an exception
        if connection:
            connection.rollback()
    finally:
        # Close the connection
        if connection:
            connection.close()
    
    return result

def execute_select_query(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a SELECT query constructed by the LLM.
    
    Args:
        query: The SQL query string
        params: Optional parameters for parameterized queries to prevent SQL injection
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if the operation succeeded
        - data: List of dictionaries containing the query results
        - row_count: Number of rows returned
        - error: Error message if the operation failed
    """
    result = {
        "success": False,
        "data": None,
        "row_count": 0,
        "error": None
    }
    
    # Verify this is a SELECT query
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        result["error"] = "Only SELECT operations are allowed with this function."
        return result
    
    # Connect to the database
    connection = None
    try:
        connection = psycopg2.connect(**db_params)
        
        # Create a cursor that returns results as dictionaries
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Execute the query
            cursor.execute(query, params)
            
            # Fetch all results
            data = cursor.fetchall()
            result["data"] = [dict(row) for row in data]
            result["row_count"] = len(result["data"])
            
            result["success"] = True
            
    except Exception as e:
        result["error"] = str(e)
    finally:
        # Close the connection
        if connection:
            connection.close()
    
    return result

# Example usage:
if __name__ == "__main__":
    # Example DML insert with RETURNING clause
    insert_query = """
    INSERT INTO vendors (
        name, 
        vendor_type, 
        contact_person, 
        phone, 
        email, 
        address
    ) 
    VALUES (
        'ABC Pharmacy', 
        'Retail Pharmacy', 
        'John Doe', 
        '555-1234', 
        'john.doe@abcpharmacy.com', 
        '123 Health Street, Medical District, NY 10001'
    )
    RETURNING vendor_id, name, created_at
    """
    
    result = execute_dml_query(insert_query)
    print(f"DML Result: {result}")
    
    # Example SELECT query
    select_query = "SELECT * FROM vendors LIMIT 5"
    select_result = execute_select_query(select_query)
    print(f"SELECT Result: {select_result}")