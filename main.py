from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import subreddit, reply,post
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from contextlib import asynccontextmanager
from routers.post import get_relevant_posts_weekly_job  # Import the cron job function
from pytz import timezone


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: scheduler starts before the app
    scheduler.start()
    yield
    # Shutdown: scheduler stops when the app stops
    scheduler.shutdown()
app = FastAPI(lifespan=lifespan)


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
app.include_router(post.router)

# scheduler.add_job(lambda: asyncio.run(get_relevant_posts_weekly_job()), "interval", minutes=1)
scheduler.add_job(
    lambda: asyncio.run(get_relevant_posts_weekly_job()),
    "cron",
    hour=0,
    minute=0,
    timezone=timezone('US/Central')
)



@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
