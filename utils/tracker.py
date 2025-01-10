from datetime import datetime
import praw
import time
import logging
from typing import Dict, Set
from statistics import mean

class MetricsTracker:
    def __init__(self, reddit_client: praw.Reddit):
        self.reddit = reddit_client
        self.tracked_replies: Set[str] = set()  

    def add_reply(self, reply_id: str):
        """Add a new reply ID to track"""
        self.tracked_replies.add(reply_id)

    def get_metrics(self) -> Dict:
        """Calculate metrics for all tracked replies on demand"""
        try:
            total_score = 0
            total_replies = 0
            positive_comments = 0
            negative_comments = 0
            scores = []

            for reply_id in self.tracked_replies:
                try:
                    comment = self.reddit.comment(id=reply_id)
                    comment.refresh()
                    
                    # Accumulate basic metrics
                    total_score += comment.score
                    total_replies += len(comment.replies)
                    scores.append(comment.score)
                    
                    # Track positive/negative comments
                    if comment.score > 0:
                        positive_comments += 1
                    elif comment.score < 0:
                        negative_comments += 1

                except Exception as e:
                    continue  
            
            total_comments = len(self.tracked_replies)
            if total_comments == 0:
                return {"status": "no_data", "message": "No comments being tracked"}

            return {
                "total_comments": total_comments,
                "total_score": total_score,
                "total_replies": total_replies,
                "average_score": round(total_score / total_comments, 2),
                "average_replies": round(total_replies / total_comments, 2),
                "positive_ratio": round(positive_comments / total_comments * 100, 2),
                "negative_ratio": round(negative_comments / total_comments * 100, 2),
                "highest_score": max(scores) if scores else 0,
                "lowest_score": min(scores) if scores else 0,
                "fetched_at": datetime.now().isoformat()
            }
                    
        except Exception as e:
            return {"status": "error", "message": str(e)}