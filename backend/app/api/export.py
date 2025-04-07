from fastapi import APIRouter, Response
from typing import Dict, Any, List
from .. import data_store
import csv
import io

router = APIRouter()

@router.get("/export/arrangement")
def export_arrangement():
    try:
        # Get all items with container assignments
        all_items = data_store.get_all_items()
        items_with_containers = [item for item in all_items if item.container_id]
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Item ID", "Container ID", "Coordinates (W1,D1,H1),(W2,D2,H2)"])
        
        # Write data rows
        for item in items_with_containers:
            # Create position data (simplified for in-memory implementation)
            start_coords = "(0,0,0)"
            end_coords = f"({item.width},{item.depth},{item.height})"
            
            writer.writerow([
                item.id,
                item.container_id,
                f"{start_coords},{end_coords}"
            ])
        
        # Get CSV content as string
        csv_content = output.getvalue()
        
        # Log the export
        data_store.create_log({
            "action_type": "EXPORT_ARRANGEMENT",
            "description": f"Exported arrangement of {len(items_with_containers)} items"
        })
        
        # Return CSV file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=arrangement.csv"
            }
        )
    
    except Exception as e:
        return {"success": False, "message": str(e)}
