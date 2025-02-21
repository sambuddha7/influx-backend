import asyncio
from routers.post import get_relevant_posts_weekly_job

async def main():
    await get_relevant_posts_weekly_job()

if __name__ == "__main__":
    asyncio.run(main())
