from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from typing import Dict, Any
from .. import data_store

router = APIRouter()

@router.post("/import/containers")
async def import_containers(file: UploadFile = File(...)):
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(contents))
        
        # Process containers from CSV
        imported_containers = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Handle different possible column names
                container_id = row.get("container_id", row.get("id", ""))
                zone = row.get("zone", "")
                width = float(row.get("width_cm", row.get("width", 0)))
                depth = float(row.get("depth_cm", row.get("depth", 0)))
                height = float(row.get("height_cm", row.get("height", 0)))
                # Add mass field with a default value if not present in CSV
                mass = float(row.get("mass_kg", row.get("mass", 0)))
                
                container_data = {
                    "id": container_id,
                    "zone": zone,
                    "width": width,
                    "depth": depth,
                    "height": height,
                    "mass": mass  # Include mass in the container data
                }
                
                # Create container in data store
                container = data_store.create_container(container_data)
                imported_containers.append(container.to_dict())
            except Exception as e:
                errors.append({
                    "row": index + 2,  # +2 for header and 0-indexing
                    "message": str(e)
                })
        
        # Log the import
        data_store.create_log({
            "action_type": "IMPORT_CONTAINERS",
            "description": f"Imported {len(imported_containers)} containers from CSV"
        })
        
        return {
            "success": True,
            "containersImported": len(imported_containers),
            "errors": errors
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}
