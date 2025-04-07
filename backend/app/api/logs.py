from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from .. import data_store

router = APIRouter()

@router.get("/logs")
def get_logs(
    action_type: Optional[str] = None,
    user_id: Optional[str] = None,
    item_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 100
):
    try:
        # Get all logs
        all_logs = data_store.get_all_logs()
        
        # Apply filters
        filtered_logs = all_logs
        
        if action_type:
            filtered_logs = [log for log in filtered_logs if log.action_type == action_type]
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if hasattr(log, 'user_id') and log.user_id == user_id]
        
        if item_id:
            filtered_logs = [log for log in filtered_logs if hasattr(log, 'item_id') and log.item_id == item_id]
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end]
        
        # Apply pagination
        total = len(filtered_logs)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        paginated_logs = filtered_logs[(page - 1) * limit:page * limit]
        
        return {
            "success": True,
            "logs": [log.to_dict() for log in paginated_logs],
            "page": page,
            "limit": limit,
            "total": total
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
