from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .. import data_store
import pandas as pd

router = APIRouter()

# Global variable for current date
CURRENT_DATE = datetime(2025, 4, 5)

@router.get("/simulation/status")
def get_simulation_status():
    try:
        # Get current date
        global CURRENT_DATE
        
        # Get statistics
        all_items = data_store.get_all_items()
        all_containers = data_store.get_all_containers()
        
        # Calculate statistics
        total_items = len(all_items)
        total_containers = len(all_containers)
        items_in_containers = len([item for item in all_items if item.container_id])
        waste_items = len([item for item in all_items if item.status == "Waste"])
        
        # Get items expiring soon (within 30 days)
        expiry_date_30_days = CURRENT_DATE + timedelta(days=30)
        expiring_soon = []
        
        for item in all_items:
            if hasattr(item, 'expiry_date') and item.expiry_date:
                item_expiry = datetime.fromisoformat(item.expiry_date)
                if CURRENT_DATE <= item_expiry <= expiry_date_30_days:
                    expiring_soon.append(item.to_dict())
        
        return {
            "success": True,
            "current_date": CURRENT_DATE.isoformat(),
            "statistics": {
                "total_items": total_items,
                "total_containers": total_containers,
                "items_in_containers": items_in_containers,
                "waste_items": waste_items,
                "items_expiring_soon": len(expiring_soon)
            },
            "expiring_soon": expiring_soon
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/simulation/date")
def get_current_date():
    global CURRENT_DATE
    return {"success": True, "current_date": CURRENT_DATE.isoformat()}

@router.post("/simulate/day")
def simulate_day(request: Dict[str, Any] = Body(None)):
    try:
        global CURRENT_DATE
        
        # Get simulation parameters
        num_of_days = request.get("numOfDays", 1) if request else 1
        to_timestamp = request.get("toTimestamp") if request else None
        items_to_use = request.get("itemsToBeUsedPerDay", []) if request else []
        
        # Calculate days to simulate
        days_to_simulate = num_of_days
        if to_timestamp:
            target_date = datetime.fromisoformat(to_timestamp)
            days_to_simulate = (target_date - CURRENT_DATE).days
            if days_to_simulate < 1:
                return {"success": False, "message": "Target date must be in the future"}
        
        # Initialize changes tracking
        changes = {
            "itemsUsed": [],
            "itemsExpired": [],
            "itemsDepletedToday": []
        }
        
        # Simulate each day
        for _ in range(days_to_simulate):
            # Advance the date
            CURRENT_DATE += timedelta(days=1)
            
            # Check for expiring items
            all_items = data_store.get_all_items()
            
            for item in all_items:
                if hasattr(item, 'expiry_date') and item.expiry_date:
                    expiry_date = datetime.fromisoformat(item.expiry_date)
                    if CURRENT_DATE >= expiry_date and item.status != "Waste":
                        # Mark item as waste
                        item.status = "Waste"
                        data_store.update_item(item)
                        
                        # Add to expired items
                        changes["itemsExpired"].append({
                            "itemId": item.id,
                            "name": item.name
                        })
                        
                        # Log the expiry
                        data_store.create_log({
                            "action_type": "ITEM_EXPIRED",
                            "description": f"Item {item.id} expired on {CURRENT_DATE.isoformat()}",
                            "item_id": item.id
                        })
            
            # Process item usage
            for item_info in items_to_use:
                # Get item ID or name
                item_id = item_info.get("itemId")
                item_name = item_info.get("name")
                
                # Find the item
                item = None
                if item_id:
                    item = data_store.get_item(item_id)
                elif item_name:
                    # Find item by name (simplified, in a real implementation we'd use a proper query)
                    for i in all_items:
                        if i.name == item_name:
                            item = i
                            break
                
                if item:
                    # Increment usage count
                    if not hasattr(item, 'usage_count'):
                        item.usage_count = 0
                    
                    item.usage_count += 1
                    
                    # Add to used items
                    changes["itemsUsed"].append({
                        "itemId": item.id,
                        "name": item.name,
                        "remainingUses": item.usage_limit - item.usage_count if hasattr(item, 'usage_limit') and item.usage_limit else None
                    })
                    
                    # Check if item has reached usage limit
                    if hasattr(item, 'usage_limit') and item.usage_limit and item.usage_count >= item.usage_limit:
                        item.status = "Waste"
                        
                        # Add to depleted items
                        changes["itemsDepletedToday"].append({
                            "itemId": item.id,
                            "name": item.name
                        })
                        
                        # Log the usage limit reached
                        data_store.create_log({
                            "action_type": "USAGE_LIMIT_REACHED",
                            "description": f"Item {item.id} reached usage limit of {item.usage_limit}",
                            "item_id": item.id
                        })
                    
                    # Update item in data store
                    data_store.update_item(item)
                    
                    # Log the usage
                    data_store.create_log({
                        "action_type": "ITEM_USED",
                        "description": f"Item {item.id} used on {CURRENT_DATE.isoformat()}",
                        "item_id": item.id
                    })
        
        # Log the simulation
        data_store.create_log({
            "action_type": "SIMULATION",
            "description": f"Simulated {days_to_simulate} days, current date: {CURRENT_DATE.isoformat()}"
        })
        
        return {
            "success": True,
            "newDate": CURRENT_DATE.isoformat(),
            "changes": changes
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
