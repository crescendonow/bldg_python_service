from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import extract, jobs, download

app = FastAPI(title="Building Extractor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(download.router, prefix="/api")


@app.get("/health")
def health():
    return {"ok": True, "service": "python-processor"}
