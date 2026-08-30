import requests
import sqlite3
import os

#stuff from sample but I plan to not do all that
from pathlib import Path
#Ai Genetic loop

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "database",
    "bills.db"
)

BACKEND_URL = "http://127.0.0.1:5001"


#def function to actually talking to ai and getting a response'
def get_ai_response_database(input):
    
    with open("prompt.txt", "r") as file:
        text = file.read()
    try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "deepseek-r1:1.5b",
                    "prompt": text + "\n" + str(input),
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()

                print("AI Review:")
                print(result["response"])
            else:
                print("AI review could not be generated.")

    except requests.exceptions.RequestException:
            print("Could not connect to Ollama.")
    
    
    
def get_data_from_db():
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Execute a query to fetch all bills
    cursor.execute("SELECT * FROM bills")
    bills = cursor.fetchall()

    # Close the database connection
    conn.close()

    return bills
    
    
    
    
def main():
    print("AGENTIC LOOP STARTED")
    #I want to keep the agentic loop simple  taking a input and parts of the system and then sending it to the ai and getting a response
    #Ill probably just have functions up above with differnt parts of the system focused on for each
    
    db_data = get_data_from_db()
    get_ai_response_database(db_data)
    
if __name__ == "__main__":
    main()