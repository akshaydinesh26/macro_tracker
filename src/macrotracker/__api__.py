import os
import uvicorn

def main():
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.macrotracker:app", 
                host="0.0.0.0", 
                port=port)
    