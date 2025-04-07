from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from typing import Dict, Any
from .. import data_store

router = APIRouter()

@router.post("/import/items")
async def import_items(file: UploadFile = File(...)):
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(pd.io.common.BytesIO(contents))
        
        # Process items from CSV
        imported_items = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Handle different possible column names
                item_id = row.get("item_id", row.get("id", ""))
                name = row.get("name", "")
                width = float(row.get("width_cm", row.get("width", 0)))
                depth = float(row.get("depth_cm", row.get("depth", 0)))
                height = float(row.get("height_cm", row.get("height", 0)))
                mass = float(row.get("mass_kg", row.get("mass", 0)))
                priority = int(row.get("priority", 1))
                
                item_data = {
                    "id": item_id,
                    "name": name,
                    "width": width,
                    "depth": depth,
                    "height": height,
                    "mass": mass,
                    "priority": priority
                }
                
                # Add optional fields if present
                expiry_date_key = next((k for k in row.keys() if "expiry" in k.lower()), None)
                if expiry_date_key and not pd.isna(row[expiry_date_key]) and row[expiry_date_key] != "N/A":
                    item_data["expiry_date"] = row[expiry_date_key]
                
                usage_limit_key = next((k for k in row.keys() if "usage" in k.lower() and "limit" in k.lower()), None)
                if usage_limit_key and not pd.isna(row[usage_limit_key]):
                    try:
                        item_data["usage_limit"] = int(row[usage_limit_key])
                    except (ValueError, TypeError):
                        errors.append({
                            "row": index + 2,  # +2 for header and 0-indexing
                            "message": f"Invalid usage limit value: {row[usage_limit_key]}"
                        })
                
                # Add preferred zone if present
                preferred_zone_key = next((k for k in row.keys() if "preferred" in k.lower() and "zone" in k.lower()), None)
                if preferred_zone_key and not pd.isna(row[preferred_zone_key]):
                    item_data["preferred_zone"] = row[preferred_zone_key]
                
                # Print for debugging
                print(f"Importing item: {item_data}")
                
                # Create item in data store
                item = data_store.create_item(item_data)
                imported_items.append(item.to_dict())
            except Exception as e:
                print(f"Error importing row {index + 2}: {str(e)}")
                errors.append({
                    "row": index + 2,  # +2 for header and 0-indexing
                    "message": str(e)
                })
        
        # Log the import
        data_store.create_log({
            "action_type": "IMPORT_ITEMS",
            "description": f"Imported {len(imported_items)} items from CSV"
        })
        
        return {
            "success": True,
            "itemsImported": len(imported_items),
            "errors": errors
        }
    
    except Exception as e:
        print(f"Error in import_items: {str(e)}")
        return {"success": False, "message": str(e)}
