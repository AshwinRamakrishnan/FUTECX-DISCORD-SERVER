import requests

API_URL = "http://localhost:8000"

def test_api():
    print("Testing API...")
    
    # 1. Health check
    res = requests.get(f"{API_URL}/health")
    print(f"Health: {res.status_code}")
    
    # We can't fully test projects without admin JWT since we protected /api/projects/{id}/tasks etc
    # Let's just test that it returns 401 Unauthorized for unauthenticated requests
    res = requests.get(f"{API_URL}/api/projects/1/tasks")
    print(f"Tasks without auth: {res.status_code} (Expected: 401)")

if __name__ == "__main__":
    test_api()
