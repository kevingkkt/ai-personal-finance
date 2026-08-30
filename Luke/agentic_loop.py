import requests
import sqlite3
import os

#stuff from sample but I plan to not do all that
from pathlib import Path
#Ai Genetic loop



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
    response = requests.get("http://127.0.0.1:5002/bills", timeout=10)

    if response.status_code == 200:
        return response.json()

    return None
    
    
    
    
def main():
    print("AGENTIC LOOP STARTED")
    #I want to keep the agentic loop simple  taking a input and parts of the system and then sending it to the ai and getting a response
    #Ill probably just have functions up above with differnt parts of the system focused on for each
    
    db_data = get_data_from_db()
    get_ai_response_database(db_data)
    
if __name__ == "__main__":
    main()