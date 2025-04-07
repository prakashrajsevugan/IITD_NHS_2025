from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, List
from .. import data_store

router = APIRouter()

@router.post("/placement")
async def placement(request_data: Dict[str, Any] = Body(...)):
    try:
        # Get items and containers from request
        items_data = request_data.get('items', [])
        containers_data = request_data.get('containers', [])
        
        # Process items
        new_items = []
        for item_data in items_data:
            # Map API field names to internal field names
            item_id = item_data.get('itemId', item_data.get('id', ''))
            name = item_data.get('name', '')
            width = float(item_data.get('width', 0))
            depth = float(item_data.get('depth', 0))
            height = float(item_data.get('height', 0))
            priority = int(item_data.get('priority', 1))
            expiry_date = item_data.get('expiryDate', None)
            usage_limit = item_data.get('usageLimit', None)
            preferred_zone = item_data.get('preferredZone', None)
            
            # Create item data dictionary
            processed_item_data = {
                "id": item_id,
                "name": name,
                "width": width,
                "depth": depth,
                "height": height,
                "priority": priority
            }
            
            # Add optional fields
            if expiry_date:
                processed_item_data["expiry_date"] = expiry_date
            if usage_limit:
                processed_item_data["usage_limit"] = usage_limit
            if preferred_zone:
                processed_item_data["preferred_zone"] = preferred_zone
            
            # Check if item already exists
            existing_item = data_store.get_item(item_id)
            if not existing_item:
                # Create new item
                item = data_store.create_item(processed_item_data)
                new_items.append(item)
            else:
                new_items.append(existing_item)
        
        # Process containers
        processed_containers = []
        for container_data in containers_data:
            # Map API field names to internal field names
            container_id = container_data.get('containerId', container_data.get('id', ''))
            zone = container_data.get('zone', '')
            width = float(container_data.get('width', 0))
            depth = float(container_data.get('depth', 0))
            height = float(container_data.get('height', 0))
            
            # Create container data dictionary
            processed_container_data = {
                "id": container_id,
                "zone": zone,
                "width": width,
                "depth": depth,
                "height": height
            }
            
            # Check if container already exists
            existing_container = data_store.get_container(container_id)
            if not existing_container:
                # Create new container
                container = data_store.create_container(processed_container_data)
                processed_containers.append(container)
            else:
                processed_containers.append(existing_container)
        
        # If no containers were provided, use all available containers
        if not processed_containers:
            processed_containers = data_store.get_all_containers()
        
        # Find placement for items
        placements = []
        unplaced_items = []
        
        for item in new_items:
            placed = False
            
            # Sort containers by preferred zone (if specified) and available space
            def container_sort_key(container):
                # Check if item has a preferred zone
                preferred_zone_match = 0
                if hasattr(item, 'preferred_zone') and item.preferred_zone:
                    preferred_zone_match = 0 if container.zone == item.preferred_zone else 1
                
                # Calculate available volume
                available_volume = (container.width * container.depth * container.height) - container.occupied_volume
                
                return (preferred_zone_match, -available_volume)  # Negative for descending order
            
            sorted_containers = sorted(processed_containers, key=container_sort_key)
            
            for container in sorted_containers:
                # Calculate volumes
                item_volume = item.width * item.depth * item.height
                container_volume = container.width * container.depth * container.height
                available_volume = container_volume - container.occupied_volume
                
                # Check if item fits in container
                if item_volume <= available_volume:
                    # Place item in container
                    placement = data_store.place_item(item.id, container.id)
                    
                    if placement:
                        # Calculate position (simplified for in-memory implementation)
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
                        
                        placements.append({
                            "itemId": item.id,
                            "containerId": container.id,
                            "position": position
                        })
                        placed = True
                        break
            
            if not placed:
                unplaced_items.append(item.id)
        
        # For now, we don't implement rearrangements
        rearrangements = []
        
        # Log the placement
        data_store.create_log({
            "action_type": "PLACEMENT",
            "description": f"Placed {len(placements)} items, {len(unplaced_items)} items could not be placed"
        })
        
        return {
            "success": True,
            "placements": placements,
            "rearrangements": rearrangements
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
