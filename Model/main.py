from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# ⭐ ENABLE CORS ⭐
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],  # Add frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        response = llm.invoke(prompt)
        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/ask-text")
async def ask_text(request: TextRequest):
    try:
        response = llm.invoke(request.prompt)
        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/ask-with-image")
async def ask_with_image(request: ImageRequest):
    try:
        base64_image = request.image
        for prefix in ["data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,"]:
            base64_image = base64_image.replace(prefix, "")

        message = HumanMessage(
            content=[
                {"type": "text", "text": request.prompt},
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{base64_image}"
                }
            ]
        )

        response = llm.invoke([message])
        return {"response": response.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/analyze-image")
async def analyze_image(request: ImageRequest):
    try:
        base64_image = request.image
        for prefix in ["data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,"]:
            base64_image = base64_image.replace(prefix, "")

        analysis_prompt = request.prompt or """
        Analyze this image and identify any:
        - Mathematical expressions
        - Equations
        - Graphs
        - Shapes
        - Data
        Solve anything found.
        """

        message = HumanMessage(
            content=[
                {"type": "text", "text": analysis_prompt},
                {"type": "image_url", "image_url": f"data:image/png;base64,{base64_image}"}
            ]
        )

        response = llm.invoke([message])
        return {"analysis": response.content, "success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")


@app.post("/save-image")
async def save_image(request: ImageRequest):
    try:
        base64_image = request.image
        for prefix in ["data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,"]:
            base64_image = base64_image.replace(prefix, "")

        math_prompt = """
        Analyze the image for math-related content:
        1. Identify all expressions
        2. Solve step-by-step
        3. Give final answer
        """

        message = HumanMessage(
            content=[
                {"type": "text", "text": math_prompt},
                {"type": "image_url", "image_url": f"data:image/png;base64,{base64_image}"}
            ]
        )

        response = llm.invoke([message])
        return {"result": response.content, "success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")