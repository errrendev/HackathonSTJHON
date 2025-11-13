from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  
    google_api_key=api_key
)

# Initialize FastAPI
app = FastAPI()

# Request models
class ImageRequest(BaseModel):
    image: str 
    prompt: Optional[str] = "Describe this image in detail"

class TextRequest(BaseModel):
    prompt: str

@app.get("/")
def root():
    return {"message": "✅ LangChain + Gemini + FastAPI running successfully!"}

@app.get("/ask")
async def ask(prompt: str):
    """Simple text-based question"""
    try:
        response = llm.invoke(prompt)
        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/ask-text")
async def ask_text(request: TextRequest):
    """POST endpoint for text questions"""
    try:
        response = llm.invoke(request.prompt)
        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/ask-with-image")
async def ask_with_image(request: ImageRequest):
    """
    Send an image along with a text prompt to Gemini
    """
    try:
      
        base64_image = request.image
        for prefix in ["data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,"]:
            base64_image = base64_image.replace(prefix, "")
        
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": request.prompt
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{base64_image}"
                }
            ]
        )
        
       
        response = llm.invoke([message])
        
        return {
            "response": response.content,
            "prompt": request.prompt
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/analyze-image")
async def analyze_image(request: ImageRequest):
    """
    Analyze an image for mathematical expressions, equations, or graphical problems
    """
    try:
        
        base64_image = request.image
        for prefix in ["data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,"]:
            base64_image = base64_image.replace(prefix, "")
        
       
        analysis_prompt = request.prompt or """
        Analyze this image and identify any:
        - Mathematical expressions or equations
        - Graphs or charts
        - Geometric shapes
        - Data visualizations
        - Handwritten calculations
        
        Provide a detailed analysis of what you see and solve any equations if present.
        """
        
       
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": analysis_prompt
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{base64_image}"
                }
            ]
        )
        
       
        response = llm.invoke([message])
        
        return {
            "analysis": response.content,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")

@app.post("/save-image")
async def save_image(request: ImageRequest):
    """
    Compatible with your original Node.js endpoint structure
    Processes mathematical expressions from images
    """
    try:
       
        base64_image = request.image
        for prefix in ["data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,"]:
            base64_image = base64_image.replace(prefix, "")
        
      
        math_prompt = """
        You have been provided with an image that contains mathematical expressions, equations, or graphical problems.
        
        Please analyze the image and:
        1. Identify all mathematical expressions, equations, or problems
        2. Solve them step by step
        3. Provide the final answer
        4. If there are graphs, describe them and extract key information
        
        Return your response in a clear, structured format.
        """
        
        # Create message with image
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": math_prompt
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{base64_image}"
                }
            ]
        )
        
        # Get response from Gemini
        response = llm.invoke([message])
        
        return {
            "result": response.content,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")