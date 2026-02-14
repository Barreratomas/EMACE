import json
from app.api.main import app

def generate_openapi():
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=4)

if __name__ == "__main__":
    generate_openapi()
