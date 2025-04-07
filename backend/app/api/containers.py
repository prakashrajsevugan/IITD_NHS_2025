from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from .. import data_store

router = APIRouter()

@router.get("/containers")
def read_containers(skip: int = 0, limit: int = 100):
    containers = data_store.get_all_containers(skip, limit)
    return {
        "success": True,
        "containers": [container.to_dict() for container in containers]
    }

@router.get("/containers/{container_id}")
def read_container(container_id: str):
    container = data_store.get_container(container_id)
    if container is None:
        raise HTTPException(status_code=404, detail="Container not found")
    return container.to_dict()

@router.post("/containers")
def create_container(container: Dict[str, Any]):
    return data_store.create_container(container).to_dict()

@router.get("/containers/all")
def get_all_containers():
    try:
        # Get all containers
        containers = data_store.get_all_containers()
        
        # Get container statistics
        container_stats = []
        for container in containers:
            # Get items in this container
            all_items = data_store.get_all_items()
            items_in_container = [item for item in all_items if item.container_id == container.id]
            
            # Calculate statistics
            total_items = len(items_in_container)
            total_mass = sum(item.mass for item in items_in_container)
            waste_items = len([item for item in items_in_container if item.status == "Waste"])
            
            container_stats.append({
                "container": container.to_dict(),
                "total_items": total_items,
                "total_mass": total_mass,
                "waste_items": waste_items,
                "items": [item.to_dict() for item in items_in_container]
            })
        
        return {
            "success": True,
            "containers": container_stats
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
