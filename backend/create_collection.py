# create_portfolios_collection.py
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# Initialize Firebase
cred = credentials.Certificate('service-account-key.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# Create a test document in portfolios collection
test_data = {
    'name': 'Test Portfolio',
    'uid': 'test_user_123',
    'holdings': [],
    'createdAt': firestore.SERVER_TIMESTAMP,
    'updatedAt': firestore.SERVER_TIMESTAMP,
    'totalCostBasis': 0
}

# This will create the collection if it doesn't exist
db.collection('portfolios').document('test_document').set(test_data)
print("✅ Portfolios collection created with test document")

# Delete the test document
db.collection('portfolios').document('test_document').delete()
print("✅ Test document cleaned up")
print("🎉 Portfolios collection is now ready for use")