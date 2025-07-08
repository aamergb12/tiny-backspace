from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import CodingAgent
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Tiny Backspace", version="1.0.0")

# ✅ Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    repoUrl: str
    prompt: str

# Initialize the coding agent
coding_agent = CodingAgent(use_local_sandbox=False)

@app.post("/code")
async def code_endpoint(request: CodeRequest):
    """Main endpoint that streams the coding process"""
    return StreamingResponse(
        coding_agent.process_coding_request(request.repoUrl, request.prompt),
        media_type="text/event-stream",
    )

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
