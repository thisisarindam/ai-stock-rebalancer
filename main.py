from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
import google.generativeai as genai

app = FastAPI()

# Enable CORS so your frontend (running on a different port/file) can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API Key (Make sure you set this as an environment variable)
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

@app.post("/rebalance")
async def rebalance_stock(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    try:
        if not api_key:
            raise ValueError("API Key is missing on the server. Please check Render Environment Variables.")
            
        # Read the uploaded Excel file into a Pandas DataFrame
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Convert the DataFrame to a CSV string to feed into the AI
        data_str = df.to_csv(index=False)
        
        # Construct the prompt for the AI
        prompt = f"""
        You are an expert Retail Inventory Analyst AI. 
        Analyze the following store inventory and sales velocity data.
        Recommend optimal stock re-balancing transfers. 
        Look for items with high stock and slow movement in one store, and suggest moving them to a store with low stock and high sales velocity.
        Clearly indicate which stock, from which store, to which store, and the exact quantity to transfer.
        
        Data:
        {data_str}
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return {"result": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))