import os
import json
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from qdrant_client.http import models
from app.core.vector.client import get_qdrant_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLD_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cold_storage")

def archive_memories(retention_months: int = 6, dry_run: bool = False):
    """
    Archives memories older than `retention_months` to cold storage (JSON files)
    and removes them from the hot vector database (Qdrant).
    
    Args:
        retention_months (int): Memories older than this will be archived.
        dry_run (bool): If True, only simulates the process without deleting.
    """
    client = get_qdrant_client()
    collection_name = "knowledge_base"
    
    # 1. Calculate cutoff date
    cutoff_date = datetime.now() - relativedelta(months=retention_months)
    cutoff_iso = cutoff_date.isoformat()
    
    logger.info(f"🛡️ Starting Retention Policy Execution")
    logger.info(f"📅 Cutoff Date: {cutoff_iso} ({retention_months} months ago)")
    
    # 2. Filter: type='chat_log' AND timestamp < cutoff_iso
    # Using DatetimeRange for ISO8601 strings (Requires DATETIME index)
    filter_condition = models.Filter(
        must=[
            models.FieldCondition(
                key="type",
                match=models.MatchValue(value="chat_log")
            ),
            models.FieldCondition(
                key="timestamp",
                range=models.DatetimeRange(
                    lt=cutoff_iso
                )
            )
        ]
    )
    
    # 3. Fetch points to archive
    # We use scroll to get all matching points
    points_to_archive = []
    next_offset = None
    
    while True:
        records, next_offset = client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_condition,
            limit=100,
            offset=next_offset,
            with_payload=True,
            with_vectors=False
        )
        points_to_archive.extend(records)
        if next_offset is None:
            break
            
    if not points_to_archive:
        logger.info("✅ No memories found to archive.")
        return

    logger.info(f"📦 Found {len(points_to_archive)} memories to archive.")

    # 4. Prepare Cold Storage
    if not os.path.exists(COLD_STORAGE_DIR):
        os.makedirs(COLD_STORAGE_DIR)
        
    archive_filename = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    archive_path = os.path.join(COLD_STORAGE_DIR, archive_filename)
    
    # Convert points to serializable dicts
    data_to_save = [
        {
            "id": str(point.id),
            "payload": point.payload,
            "archived_at": datetime.now().isoformat()
        }
        for point in points_to_archive
    ]
    
    # 5. Save to File
    if not dry_run or (dry_run and len(data_to_save) > 0):
        try:
            with open(archive_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Archived data saved to: {archive_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save archive file: {e}")
            return

    # 6. Delete from Qdrant
    if not dry_run:
        points_ids = [point.id for point in points_to_archive]
        client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(points=points_ids)
        )
        logger.info(f"🗑️ Deleted {len(points_ids)} points from Qdrant.")
    else:
        logger.info("🚫 Dry run: Skipping deletion.")

if __name__ == "__main__":
    # For testing purposes, we can set retention to 0 months or use a flag
    # But by default run standard policy
    archive_memories(retention_months=6)
