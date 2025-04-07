from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from .. import data_store

router = APIRouter()

@router.get("/search")
def search_items(
    item_id: Optional[str] = None,
    item_name: Optional[str] = None,
    user_id: Optional[str] = None,
    zone: Optional[str] = None,
    priority_min: Optional[int] = None,
    priority_max: Optional[int] = None,
    expiry_before: Optional[str] = None,
    expiry_after: Optional[str] = None,
    usage_min: Optional[int] = None,
    usage_max: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 100
):
    try:
        # Get all items
        all_items = data_store.get_all_items()
        
        # Apply filters
        filtered_items = all_items
        
        if item_id:
            filtered_items = [item for item in filtered_items if item_id.lower() in item.id.lower()]
        
        if item_name:
            filtered_items = [item for item in filtered_items if item.name and item_name.lower() in item.name.lower()]
        
        if zone:
            # Get containers in the specified zone
            containers = [c for c in data_store.get_all_containers() if c.zone.lower() == zone.lower()]
            container_ids = [c.id for c in containers]
            filtered_items = [item for item in filtered_items if item.container_id in container_ids]
        
        if priority_min is not None:
            filtered_items = [item for item in filtered_items if item.priority >= priority_min]
        
        if priority_max is not None:
            filtered_items = [item for item in filtered_items if item.priority <= priority_max]
        
        if expiry_before:
            expiry_date = datetime.fromisoformat(expiry_before)
            filtered_items = [item for item in filtered_items if hasattr(item, 'expiry_date') and item.expiry_date and datetime.fromisoformat(item.expiry_date) <= expiry_date]
        
        if expiry_after:
            expiry_date = datetime.fromisoformat(expiry_after)
            filtered_items = [item for item in filtered_items if hasattr(item, 'expiry_date') and item.expiry_date and datetime.fromisoformat(item.expiry_date) >= expiry_date]
        
        if status:
            filtered_items = [item for item in filtered_items if item.status.lower() == status.lower()]
        
        # If we have exactly one item, prepare retrieval steps
        if len(filtered_items) == 1:
            item = filtered_items[0]
            container = data_store.get_container(item.container_id) if item.container_id else None
            
            # Create position data (simplified for in-memory implementation)
            position = None
            if container:
                position = {
                    "startCoordinates": {
                        "width": 0,
                        "depth": 0,
                        "height": 0
                    },
                    "endCoordinates": {
                        "width": item.width,
                        "depth": item.depth,
                        "height": item.height
                    }
                }
            
            # Create retrieval steps
            retrieval_steps = []
            if container:
                retrieval_steps = [
                    {
                        "step": 1,
                        "action": "remove",
                        "itemId": item.id,
                        "itemName": item.name
                    },
                    {
                        "step": 2,
                        "action": "retrieve",
                        "itemId": item.id,
                        "itemName": item.name
                    }
                ]
            
            # Log the search
            data_store.create_log({
                "action_type": "SEARCH",
                "description": f"Item {item.id} found and retrieved",
                "item_id": item.id,
                "user_id": user_id
            })
            
            return {
                "success": True,
                "found": True,
                "item": {
                    "itemId": item.id,
                    "name": item.name,
                    "containerId": item.container_id if item.container_id else None,
                    "zone": container.zone if container else None,
                    "position": position
                },
                "retrievalSteps": retrieval_steps
            }
        
        # Apply pagination for multiple results
        total = len(filtered_items)
        paginated_items = filtered_items[(page - 1) * limit:page * limit]
        
        # Log the search
        data_store.create_log({
            "action_type": "SEARCH",
            "description": f"Found {total} items matching search criteria",
            "user_id": user_id
        })
        
        return {
            "success": True,
            "found": total > 0,
            "items": [item.to_dict() for item in paginated_items],
            "page": page,
            "limit": limit,
            "total": total
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
