"""
Import sample data from the samples folder into the in-memory data store.
This script loads containers and items from the sample CSV files.
"""
import os
import pandas as pd
from . import data_store

def import_sample_containers(file_path):
    """
    Import containers from a CSV file into the in-memory data store.
    
    Args:
        file_path: Path to the CSV file containing container data
    
    Returns:
        Number of containers imported
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Process containers
        count = 0
        for _, row in df.iterrows():
            # Create container data dictionary
            container_data = {
                "id": row["container_id"],
                "zone": row["zone"],
                "width": float(row["width_cm"]),
                "depth": float(row["depth_cm"]),
                "height": float(row["height_cm"])
            }
            
            # Create container in data store
            data_store.create_container(container_data)
            count += 1
        
        # Log the import
        data_store.create_log({
            "action_type": "IMPORT_CONTAINERS",
            "description": f"Imported {count} containers from sample file"
        })
        
        return count
    
    except Exception as e:
        print(f"Error importing containers: {str(e)}")
        return 0

def import_sample_items(file_path, limit=100):
    """
    Import items from a CSV file into the in-memory data store.
    
    Args:
        file_path: Path to the CSV file containing item data
        limit: Maximum number of items to import (default: 100)
    
    Returns:
        Number of items imported
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Limit the number of items if needed
        if limit > 0:
            df = df.head(limit)
        
        # Process items
        count = 0
        for _, row in df.iterrows():
            # Create item data dictionary
            item_data = {
                "id": row["item_id"],
                "name": row["name"],
                "width": float(row["width_cm"]),
                "depth": float(row["depth_cm"]),
                "height": float(row["height_cm"]),
                "mass": float(row["mass_kg"]),
                "priority": int(row["priority"])
            }
            
            # Add optional fields if present
            if "expiry_date" in row and row["expiry_date"] != "N/A":
                item_data["expiry_date"] = row["expiry_date"]
            
            if "usage_limit" in row and not pd.isna(row["usage_limit"]):
                item_data["usage_limit"] = int(row["usage_limit"])
            
            # Create item in data store
            data_store.create_item(item_data)
            count += 1
        
        # Log the import
        data_store.create_log({
            "action_type": "IMPORT_ITEMS",
            "description": f"Imported {count} items from sample file"
        })
        
        return count
    
    except Exception as e:
        print(f"Error importing items: {str(e)}")
        return 0

def import_all_samples(containers_path, items_path, items_limit=100):
    """
    Import all sample data into the in-memory data store.
    
    Args:
        containers_path: Path to the containers CSV file
        items_path: Path to the items CSV file
        items_limit: Maximum number of items to import (default: 100)
    
    Returns:
        Tuple of (containers_count, items_count)
    """
    # Import containers
    containers_count = import_sample_containers(containers_path)
    print(f"Imported {containers_count} containers")
    
    # Import items
    items_count = import_sample_items(items_path, items_limit)
    print(f"Imported {items_count} items")
    
    return containers_count, items_count

if __name__ == "__main__":
    # Sample file paths
    samples_dir = r"c:\Users\Admin\Downloads\samples-20250407T034157Z-001\samples"
    containers_file = os.path.join(samples_dir, "containers.csv")
    items_file = os.path.join(samples_dir, "input_items.csv")
    
    # Import samples
    containers_count, items_count = import_all_samples(containers_file, items_file, items_limit=200)
    
    print(f"Successfully imported {containers_count} containers and {items_count} items from sample files")
