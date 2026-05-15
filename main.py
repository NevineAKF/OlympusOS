from fastapi import FastAPI

app = FastAPI(title="OlympusOS")


@app.get("/")
def root():
    return {"status": "OlympusOS running"}
