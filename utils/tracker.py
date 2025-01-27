from datetime import datetime
from utils.firestore_service import FirestoreService
import praw
import time
import logging
from typing import Dict, Set
from statistics import mean

class MetricsTracker:
    def __init__(self, reddit_client: praw.Reddit, firestore_service: FirestoreService):
        self.reddit = reddit_client
        self.firestore = firestore_service

    async def add_reply(self, user_id: str, reply_id: str):
        """Add a new reply ID for a specific user in Firestore"""
        await self.firestore.add_reply_to_user(user_id, reply_id)

    async def get_metrics(self, user_id: str) -> Dict:
        """Calculate metrics for all tracked replies for a specific user"""
        try:
            tracked_replies = await self.firestore.get_replies_for_user(user_id)
            total_score = 0
            total_replies = 0
            positive_comments = 0
            negative_comments = 0
            scores = []
            valid_replies = set()

            for reply_id in tracked_replies:
                try:
                    comment = self.reddit.comment(id=reply_id)
                    comment.refresh()

                    if comment.author is None:  # Deleted comments
                        continue

                    total_score += comment.score
                    total_replies += len(comment.replies)
                    scores.append(comment.score)

                    if comment.score > 0:
                        positive_comments += 1
                    elif comment.score < 0:
                        negative_comments += 1
                    valid_replies.add(reply_id)
                    
                except Exception:
                    continue  # Ignore failed fetches
            
            total_comments = len(valid_replies)
            
            if total_comments == 0:
                return {
                    "total_comments": 0,
                    "total_score": 0,
                    "total_replies": 0,
                    "average_score": 0,
                    "average_replies": 0,
                    "positive_ratio": 0,
                    "negative_ratio": 0,
                    "highest_score": 0,
                    "lowest_score": 0,
                }

            return {
                "total_comments": total_comments,
                "total_score": total_score,
                "total_replies": total_replies,
                "average_score": round(total_score / total_comments, 2),
                "average_replies": round(total_replies / total_comments, 2),
                "positive_ratio": round(positive_comments / total_comments * 100, 2),
                "negative_ratio": round(negative_comments / total_comments * 100, 2),
                "highest_score": max(scores),
                "lowest_score": min(scores),
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}


