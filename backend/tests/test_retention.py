import sys
import os
import time
import uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta
from qdrant_client.http import models

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.vector.client import get_qdrant_client
from app.core.memory.retention import archive_memories, COLD_STORAGE_DIR

def test_retention_policy():
    print("\n--- ❄️ Testing Retention Policy ---")
    client = get_qdrant_client()
    collection_name = "knowledge_base"
    
    # 1. Insert Old Memory (1 year ago)
    old_date = datetime.now() - relativedelta(months=12)
    old_id = str(uuid.uuid4())
    
    print(f"1. Inserting old memory (ID: {old_id}, Date: {old_date.isoformat()})...")
    
    client.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=old_id,
                vector=[0.1] * 384, # Dummy vector
                payload={
                    "type": "chat_log",
                    "timestamp": old_date.isoformat(),
                    "content": "This is an ancient memory.",
                    "user_id": 999
                }
            )
        ]
    )
    
    # 2. Insert Recent Memory (1 month ago) - Should NOT be archived
    recent_date = datetime.now() - relativedelta(months=1)
    recent_id = str(uuid.uuid4())
    
    print(f"2. Inserting recent memory (ID: {recent_id}, Date: {recent_date.isoformat()})...")
    
    client.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=recent_id,
                vector=[0.1] * 384,
                payload={
                    "type": "chat_log",
                    "timestamp": recent_date.isoformat(),
                    "content": "This is a fresh memory.",
                    "user_id": 999
                }
            )
        ]
    )
    
    # Wait for indexing? Usually immediate for single points but good to pause briefly
    # time.sleep(1) 
    
    # 3. Run Retention (Threshold: 6 months)
    print("3. Running archive_memories(retention_months=6)...")
    archive_memories(retention_months=6)
    
    # 4. Verify Old Memory is GONE from Qdrant
    print("4. Verifying Qdrant state...")
    old_points = client.retrieve(
        collection_name=collection_name,
        ids=[old_id]
    )
    
    if not old_points:
        print("✅ Old memory successfully removed from Qdrant.")
    else:
        print("❌ Old memory STILL in Qdrant!")
        
    # 5. Verify Recent Memory is STILL THERE
    recent_points = client.retrieve(
        collection_name=collection_name,
        ids=[recent_id]
    )
    
    if recent_points:
        print("✅ Recent memory correctly preserved in Qdrant.")
    else:
        print("❌ Recent memory was incorrectly removed!")
        
    # 6. Verify File Creation
    print("5. Verifying Cold Storage...")
    files = sorted(os.listdir(COLD_STORAGE_DIR))
    if files:
        latest_file = files[-1]
        print(f"✅ Found archive file: {latest_file}")
        
        with open(os.path.join(COLD_STORAGE_DIR, latest_file), 'r') as f:
            data = f.read()
            if old_id in data:
                print("✅ Old memory ID found in archive file.")
            else:
                print("❌ Old memory ID NOT found in archive file content.")
    else:
        print("❌ No archive files found in cold_storage!")

if __name__ == "__main__":
    test_retention_policy()
