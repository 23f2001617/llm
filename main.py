from fastapi import FastAPI, Form, File, UploadFile
import httpx
import csv
import zipfile
import io

# AI Proxy Configuration
AI_PROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AI_PROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDE2MTdAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.Jmaik-gF9pJSyc6DqNjBsLFz4AgDMKHI7t41IWukESc"   

app = FastAPI()

@app.get('/hello')
async def root():
    return {"example": "this is an example", "data": 0}

@app.post("/api/")
async def answer_question(question: str = Form(...), file: UploadFile = None):
    # Handle CSV files inside ZIP
    if file:
        content = await file.read()
        if file.filename.endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(content), "r") as z:
                    for filename in z.namelist():
                        if filename.endswith(".csv"):
                            with z.open(filename) as f:
                                reader = csv.DictReader(io.TextIOWrapper(f))
                                for row in reader:
                                    if "answer" in row:
                                        return {"answer": row["answer"]}
                return {"answer": "No 'answer' column found in CSV."}
            except zipfile.BadZipFile:
                return {"error": "Invalid ZIP file."}

    # Send request to AI Proxy
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                AI_PROXY_URL,
                json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": question}]},
                headers={"Authorization": f"Bearer {AI_PROXY_TOKEN}"},
            )
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return {"answer": data["choices"][0]["message"]["content"]}
            else:
                return {"error": "AI Proxy returned an invalid response."}
    except Exception as e:
        return {"error": f"Failed to connect to AI Proxy: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
