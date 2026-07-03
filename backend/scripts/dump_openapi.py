import json
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

def dump_openapi():
    openapi_schema = app.openapi()
    
    # Ensure docs directory exists
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    output_path = os.path.join(docs_dir, "openapi.json")
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"OpenAPI spec successfully written to {output_path}")

if __name__ == "__main__":
    dump_openapi()
