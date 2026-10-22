# AI Personal Finance Management System

## Team Members
- Kevin - Income & Expense Tracker
- Lex - Budget Manager
- Grace - Savings Goal Manager
- Luke - Bills & Payments Manager

## Technologies
- Python
- Flask
- SQLite
- Docker
- Docker Compose
- Ollama
- Qwen

## Get Code running in the terminal

1) Get to the AI personal finance file root
2) Make sure docker is opened on the computer
3) In four different terminals Run these commands
   - docker compose up --build -d
   - python .\ai-services\rag_server.py
   - python .\ai-services\mcp_server.py
   - python .\ai-services\multi_agent_server.py
4) Run the project on a browser on http://localhost:8080


## code on cloud

1) ssh -i "$HOME.ssh\id_ed25519" lebronjames@20.213.19.132 in terminal
2) cd ~/ai-personal-finance
3) docker compose up --build -d


- Open at http://20.213.19.132:8080/
