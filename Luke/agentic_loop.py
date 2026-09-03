import requests
import sqlite3
import os

#stuff from sample but I plan to not do all that
from pathlib import Path
#Ai Genetic loop



BACKEND_URL = "http://127.0.0.1:5001"


#def function to actually talking to ai and getting a response'
def get_ai_response(input):
    prompt_path = os.path.join(os.path.dirname(__file__), "Prompts", "prompt.txt")
    with open(prompt_path, "r") as file:
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

def get_endpoints():
    #Trying to check each endpoint
    healthResponse = requests.get("http://127.0.0.1:5001/health")
    billsResponse = requests.get("http://127.0.0.1:5001/bills")
    singleBillResponse = requests.get("http://127.0.0.1:5001/bills/1")
    
    TogetherResponse = {"health": healthResponse.status_code,
        "bills": billsResponse.status_code,
        "single_bill": singleBillResponse.status_code}
    
def get_architecture():
    #Architecture seems to be about the design / structure so Im going to use docker compose file and have ai read that
    with open("docker-compose.yml", "r") as file:
        return file.read()
    
    
def main():
    print("AGENTIC LOOP STARTED")
    #I want to keep the agentic loop simple  taking a input and parts of the system and then sending it to the ai and getting a response
    #Ill probably just have functions up above with differnt parts of the system focused on for each
    value = True
    while value== True:
        print("AGENTIC LOOP RUNNING")
        #I want to split it off into cases
        print("Choose an option:")
        print("1. Get AI review of database data")
        print("2. Get AI to review endpoints")
        print("3. Get AI to review architecture")
        print("0. Exit Loop")
        user_input = input("Enter your choice: ")
        while user_input not in ["0", "1", "2", "3"]:
            print("Please Only Choose 1, 2, 3 or 0.")
            user_input = input("Enter your choice: ")
        match user_input:
            case "0":
                print("Exiting loop.")
                value = False
            case "1":
                print("AI will analyse with database data:")
                db_data = get_data_from_db()
                get_ai_response(db_data)
            case "2":
                print("AI will use the endpoints data to help review the data")
                endpointsData = get_endpoints()
                get_ai_response(endpointsData)
            case "3":
                print("Getting AI review of architecture")
                architecture_data = get_architecture()
                get_ai_response(architecture_data)
    
if __name__ == "__main__":
    main()