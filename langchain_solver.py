from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import json
import re


# Load environment variables
load_dotenv()
# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Get API keys from environment variables
solution_api_key = os.getenv("SOLUTION_API_KEY")
graph_api_key = os.getenv("GRAPH_API_KEY")

# Initialize the two LLMs
solution_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=solution_api_key
)

graph_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=graph_api_key
)

# Store chat history
chat_history = []

class ProblemRequest(BaseModel):
    problem: str

def solve_problem(question):
    global chat_history
    history_text = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in chat_history])
    
    full_prompt = f"""{history_text}
    User: {question}
    System: Please provide a detailed step-by-step explanation in JSON format like this:
    
    {{
        "step1": "Explain the concept involved.",
        "step2": "Break down the first part of the solution.",
        "step3": "Continue solving the problem step by step.",
        "final_answer": "Provide the final answer here."
    }}
    
    If you cannot fully solve the problem, provide as much information as possible about the concepts involved and any partial steps you can determine.
    Ensure that the response is a valid JSON object.
    """
    


    try:
        response = solution_llm.invoke(full_prompt)
        print(response)

        if not response or not hasattr(response, "content") or not response.content.strip():
            return {"error": "Sorry, I couldn't generate a response. Try rephrasing the question."}
        
        ai_response = response.content.strip()
        
        # Extract JSON content if it's wrapped in code blocks
        if "```json" in ai_response:
            json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
            if json_match:
                ai_response = json_match.group(1)
        
        # Ensure the response is valid JSON
        try:
            structured_response = json.loads(ai_response)
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            try:
                # Replace single quotes with double quotes
                fixed_response = ai_response.replace("'", '"')
                structured_response = json.loads(fixed_response)
            except:
                return {"error": "AI response is not in valid JSON format. Try asking again."}
        
        # Append to chat history
        chat_history.append({"user": question, "ai": structured_response})
        return structured_response
    except Exception as e:
        print("Error calling Solution API:", str(e))
        return {"error": f"An error occurred while generating a solution: {str(e)}"}

def generate_graph_data(equation):
    graph_prompt = f"""
    Analyze the following equation: {equation}
    
    Extract or determine the mathematical function expressed in this equation.
    Create a dataset of (x,y) points that represent this function.
    
    Generate 11 data points with x values ranging from -5 to 5 in increments of 1.
    Calculate the corresponding y values based on the equation.
    
    Return ONLY a valid JSON array in the following format:
    [
        {{ "x": -5, "y": value }}, 
        {{ "x": -4, "y": value }},
        ...
        {{ "x": 5, "y": value }}
    ]
    Do not include any explanations or additional text - just the JSON array.
    if graph data is not possible to form for you just give a empty array
    """
    
    try:
        response = graph_llm.invoke(graph_prompt)
        print(response)
        if not response or not hasattr(response, "content") or not response.content.strip():
            return {"error": "Could not generate graph data"}
        
        graph_response = response.content.strip()
        
        # Extract JSON content if it's wrapped in code blocks
        if "```json" in graph_response:
            json_match = re.search(r'```json\s*(.*?)\s*```', graph_response, re.DOTALL)
            if json_match:
                graph_response = json_match.group(1)
        elif "```" in graph_response:
            json_match = re.search(r'```\s*(.*?)\s*```', graph_response, re.DOTALL)
            if json_match:
                graph_response = json_match.group(1)
        
        # Parse the JSON data
        try:
            graph_data = json.loads(graph_response)
            return graph_data
        except json.JSONDecodeError:
            # Attempt to fix common JSON issues
            graph_response = graph_response.replace("'", '"')
            try:
                graph_data = json.loads(graph_response)
                return graph_data
            except:
                return {"error": "Could not parse graph data into JSON format"}
    except Exception as e:
        print("Error calling Graph API:", str(e))
        return {"error": f"An error occurred while generating graph data: {str(e)}"}

def extract_equation(question):
    # Try to extract an equation from the problem text
    # This is a simple implementation - you might want to enhance this
    equation_patterns = [
        r'y\s*=\s*[^,;.]+',  # Match y = ...
        r'f\(x\)\s*=\s*[^,;.]+',  # Match f(x) = ...
        r'equation[:\s]+[^,;.]+',  # Match equation: ...
        r'function[:\s]+[^,;.]+',  # Match function: ...
    ]
    
    for pattern in equation_patterns:
        matches = re.search(pattern, question, re.IGNORECASE)
        if matches:
            return matches.group(0)
    
    # If no clear equation is found, let the LLM figure it out
    return question

@app.get("/")
def home():
    return {"message": "Hello, FastAPI is working with dual LLM capabilities!"}

@app.post("/solve")
def solve_math_physics_problem(request: ProblemRequest):
    if not request.problem:
        raise HTTPException(status_code=400, detail="Problem cannot be empty")
    
    # Get the step-by-step solution
    solution = solve_problem(request.problem)
    
    # Extract equation and generate graph data
    equation = extract_equation(request.problem)
    graph_data = generate_graph_data(equation)
    
    return {
        "solution": solution,
        "graphData": graph_data
    }