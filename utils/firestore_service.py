from fastapi import FastAPI, HTTPException
from firebase_admin import credentials, firestore, initialize_app
from typing import List, Optional

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
    
    async def get_email(self, user_id: str) -> Optional[str]:
        """Get email for a specific user"""
        try:
            doc_ref = self.db.collection('onboarding').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            return data.get('email')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching email: {str(e)}")

# Example usage in FastAPI routes
app = FastAPI()
firestore_service = FirestoreService()

@app.get("/api/keywords/{user_id}")
async def get_user_keywords(user_id: str):
    return await firestore_service.get_keywords(user_id)