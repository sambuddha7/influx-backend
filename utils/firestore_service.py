from fastapi import FastAPI, HTTPException
from firebase_admin import credentials, firestore, initialize_app
from typing import List, Optional
from datetime import datetime
import firebase_admin
import os 
from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv()


# Initialize Firebase Admin SDK
service_account_key_json = {
    "type": os.getenv("type"),
    "project_id": os.getenv("project_id"),
    "private_key_id": os.getenv("private_key_id"),
    "private_key": os.getenv("private_key").replace('\\n', '\n'),
    "client_email": os.getenv("client_email"),
    "client_id": os.getenv("client_id"),
    "auth_uri": os.getenv("auth_uri"),
    "token_uri": os.getenv("token_uri"),
    "auth_provider_x509_cert_url": os.getenv("auth_provider_x509_cert_url"),
    "client_x509_cert_url": os.getenv("client_x509_cert_url"),
    "universe_domain": os.getenv("universe_domain")
}



cred = service_account.Credentials.from_service_account_info(service_account_key_json)
# firebase_admin.initialize_app(cred, {'projectId': 'influx-18581'})
firebase_admin.initialize_app(cred, {'projectId': os.getenv("project_id")})


# Initialize Firestore client
db = firestore.client()

class FirestoreService:
    def __init__(self):
        self.db = firestore.client()

    async def get_active_user_ids(self) -> List[str]:
        """Retrieve all user IDs where accountStatus is 'active' from the 'account-details' collection"""
        try:
            users_ref = self.db.collection("account-details").where("accountStatus", "==", "active")
            docs = users_ref.stream()
            user_ids = [doc.get("userId") for doc in docs if doc.get("userId")]
            return user_ids
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching active user IDs: {str(e)}")
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
    async def get_primary_keywords(self, user_id: str) -> List[str]:
        """Get keywords for a specific user"""
        try:
            doc_ref = self.db.collection('onboarding').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return []
                
            data = doc.to_dict()
            return data.get('primaryKeywords', [])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching keywords: {str(e)}")
    async def get_secondary_keywords(self, user_id: str) -> List[str]:
        """Get keywords for a specific user"""
        try:
            doc_ref = self.db.collection('onboarding').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return []
                
            data = doc.to_dict()
            return data.get('secondaryKeywords', [])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching keywords: {str(e)}")
    async def get_company_name(self, user_id: str) -> Optional[str]:
        """Get company name for a specific user"""
        try:
            doc_ref = self.db.collection('onboarding').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            return data.get('companyName', None)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching company name: {str(e)}")
    async def get_user_role(self, user_id: str) -> Optional[str]:
        """Get company description for a specific user"""
        try:
            doc_ref = self.db.collection('ai-training').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            return data.get('postAs', None)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching user roles: {str(e)}")
    async def get_sample_reply(self, user_id: str) -> Optional[str]:
        """Get company description for a specific user"""
        try:
            doc_ref = self.db.collection('ai-training').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            return data.get('sampleReply', None)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching sample replies: {str(e)}")
    async def get_marketing_objectives(self, user_id: str) -> Optional[str]:
        """Get company description for a specific user"""
        try:
            doc_ref = self.db.collection('ai-training').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            return data.get('marketingGoals', None)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching marketing goals: {str(e)}")
    async def get_pain_points(self, user_id: str) -> Optional[str]:
        """Get pain points for a specific user"""
        try:
            doc_ref = self.db.collection('ai-training').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            return data.get('marketingGoals', None)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching pain points: {str(e)}")
    async def get_company_description(self, user_id: str) -> Optional[str]:
        """Get company description for a specific user"""
        try:
            doc_ref = self.db.collection('onboarding').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            return data.get('companyDescription', None)
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
                "url": reddit_object[5],
                "date_created": reddit_object[6],
                "createdAt": datetime.now(),
            }
            if isinstance(reddit_object[6], datetime):
                post_data["date_created"] = reddit_object[6].isoformat() + "Z"
            elif isinstance(reddit_object[6], int) or isinstance(reddit_object[6], float):
                post_data["date_created"] = datetime.utcfromtimestamp(reddit_object[6]).isoformat() + "Z"
            else:
                raise TypeError(f"Unexpected type for date_created: {type(reddit_object[6])}")
            if isinstance(post_data["createdAt"], datetime):
                post_data["createdAt"] = post_data["createdAt"].isoformat() + "Z"
            elif isinstance(post_data["createdAt"], (int, float)):
                post_data["createdAt"] = datetime.utcfromtimestamp(post_data["createdAt"]).isoformat() + "Z"
            else:
                raise TypeError(f"Unexpected type for createdAt: {type(post_data['createdAt'])}")

            
            # Reference to the "posts" subcollection for the user
            posts_collection_ref = self.db.collection("reddit-posts").document(user_id).collection("posts")
            
            # Add the post to Firestore
            post_doc_ref = posts_collection_ref.document(post_data["id"])
            post_doc_ref.set(post_data)

            return f"Post {post_data['id']} added successfully!"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error adding post: {str(e)}")
        
    async def add_reply_to_user(self, user_id: str, reply_id: str):
        user_doc = self.db.collection('track-replies').document(user_id)
        user_doc.set({'replies': firestore.ArrayUnion([reply_id])}, merge=True)

    async def get_replies_for_user(self, user_id: str) -> List[str]:
        user_doc = self.db.collection('track-replies').document(user_id)
        doc = user_doc.get()
        if doc.exists:
            return doc.to_dict().get('replies', [])
        return []
    
    async def get_user_posts(self, user_id):
        posts_collection_ref = self.db.collection("reddit-posts").document(user_id).collection("posts")
        
        try:
            posts = posts_collection_ref.get()
            post_list = [post.to_dict() for post in posts]
            return post_list
        except Exception as e:
            print(f"Error fetching posts: {e}")
            return []

    async def get_excluded_reddits(self, user_id: str) -> List[str]:
        user_doc = self.db.collection('excluded-subreddits').document(user_id)
        doc = user_doc.get()
        if doc.exists:
            return doc.to_dict().get('subreddits', '')
        return []
# Example usage in FastAPI routes
app = FastAPI()
firestore_service = FirestoreService()

@app.get("/api/keywords/{user_id}")
async def get_user_keywords(user_id: str):
    return await firestore_service.get_keywords(user_id)