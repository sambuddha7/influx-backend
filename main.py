from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import subreddit, reply
import uvicorn

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(subreddit.router)
app.include_router(reply.router)


# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
