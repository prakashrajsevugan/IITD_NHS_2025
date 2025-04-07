from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from .. import data_store

router = APIRouter()

@router.post("/items")
def create_item(item: Dict[str, Any] = Body(...)):
    return data_store.create_item(item).to_dict()

@router.get("/items")
def read_items(skip: int = 0, limit: int = 100):
    items = data_store.get_all_items(skip, limit)
    return [item.to_dict() for item in items]

@router.get("/items/{item_id}")
def read_item(item_id: str):
    item = data_store.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_dict()

@router.put("/items/{item_id}")
def update_item(item_id: str, item_data: Dict[str, Any] = Body(...)):
    item = data_store.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update item attributes
    for key, value in item_data.items():
        setattr(item, key, value)
    
    # Save updated item
    updated_item = data_store.update_item(item)
    
    return updated_item.to_dict()

@router.delete("/items/{item_id}")
def delete_item(item_id: str):
    item = data_store.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Remove item
    data_store.remove_item(item_id)
    
    return {"success": True, "message": f"Item {item_id} deleted successfully"}
