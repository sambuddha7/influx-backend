from fastapi import FastAPI, HTTPException
from firebase_admin import credentials, firestore, initialize_app
from typing import List, Optional
from datetime import datetime


# Initialize Firebase Admin SDK
# cred = credentials.Certificate("../serviceAccountKey.json")
cred = credentials.Certificate("./serviceAccountKey.json")

initialize_app(cred)

# Initialize Firestore client
db = firestore.client()

class FirestoreService:
    def __init__(self):
        self.db = firestore.client()
    
    async def get_keywords(self, user_id: str) -> List[str]:
        """Get keywords for a specific user"""
        try:
            doc_ref = self.db.collection('onboarding').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return []
                
            data = doc.to_dict()
            return data.get('keywords', [])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching keywords: {str(e)}")
    
    async def get_company_description(self, user_id: str) -> Optional[str]:
        """Get company description for a specific user"""
        try:
            doc_ref = self.db.collection('onboarding').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            return data.get('company_desc')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching company description: {str(e)}")
    async def add_post(self, user_id: str, reddit_object: List[str]) -> str:
        """Add a post to the 'reddit-posts' collection for a specific user"""
        try:
            # Extract post details from the reddit_object
            post_data = {
                "id": reddit_object[0],
                "subreddit": reddit_object[1],
                "title": reddit_object[2],
                "content": reddit_object[3],
                "suggestedReply": reddit_object[4],
                "createdAt": datetime.now()
            }
            
            # Reference to the "posts" subcollection for the user
            posts_collection_ref = self.db.collection("reddit-posts").document(user_id).collection("posts")
            
            # Add the post to Firestore
            post_doc_ref = posts_collection_ref.document(post_data["id"])
            post_doc_ref.set(post_data)

            return f"Post {post_data['id']} added successfully!"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error adding post: {str(e)}")

# Example usage in FastAPI routes
app = FastAPI()
firestore_service = FirestoreService()

@app.get("/api/keywords/{user_id}")
async def get_user_keywords(user_id: str):
    return await firestore_service.get_keywords(user_id)