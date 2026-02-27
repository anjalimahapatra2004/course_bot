A full-stack Generative AI application built using:

- Backend: FastAPI  
- Model Execution: Modal  
- Frontend: Streamlit  

---

## Project Overview

This application allows users to interact with an AI model through a Streamlit UI.  
The frontend communicates with a FastAPI backend, which processes requests and interacts with Modal or external LLM APIs.

##  Installation Guide 

###  Clone the Repository

git clone https://github.com/anjalimahapatra2004/course_bot.git
cd course_bot

###  Set up Guide 
pip install

create .env file and set GROQ_API_KEY and MODEL_NAME

EX: GROQ_API_KEY=dlkfjadlfjdsljflsdjf ,  MODEL_NAME=llama-3.1-8b-instant

###  Run the project 

open terminal run this command for server run  

step-1 uvicorn app:app --reload

open another terminal run this command for run streamlit 

step -2 streamlit run streamlit_app.py

setp-3 open the borwser http://localhost:8501 use this link
