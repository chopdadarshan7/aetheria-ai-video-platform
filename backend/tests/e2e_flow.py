import time
import httpx

API_URL = "http://localhost:8000/api/v1"

def run_e2e():
    print("--- STARTING END-TO-END SYSTEM VALIDATION ---")
    
    # 1. Register User
    username = f"user_{int(time.time())}"
    print(f"Registering user: {username}")
    res = httpx.post(
        f"{API_URL}/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "password123"}
    )
    if res.status_code != 201:
        print(f"FAILED: Registration failed with {res.status_code}: {res.text}")
        return False
    print("SUCCESS: User registered.")

    # 2. Login User
    print("Logging in user...")
    res = httpx.post(
        f"{API_URL}/auth/token",
        data={"username": username, "password": "password123"}
    )
    if res.status_code != 200:
        print(f"FAILED: Login failed: {res.text}")
        return False
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("SUCCESS: Login token acquired.")

    # 3. Create Project
    print("Creating project...")
    res = httpx.post(
        f"{API_URL}/projects",
        json={"name": "E2E Cinematic Test", "description": "Verification plan"},
        headers=headers
    )
    if res.status_code != 200:
        print(f"FAILED: Create project failed: {res.text}")
        return False
    project = res.json()
    project_id = project["id"]
    print(f"SUCCESS: Project created with ID {project_id}.")

    # 4. Trigger Render Job
    print("Triggering render job...")
    res = httpx.post(
        f"{API_URL}/renders/trigger",
        json={
            "job_type": "text-to-video",
            "prompt": "A beautiful bird flying over mountains",
            "project_id": project_id
        },
        headers=headers
    )
    if res.status_code != 200:
        print(f"FAILED: Trigger render failed: {res.text}")
        return False
    job = res.json()
    job_id = job["id"]
    print(f"SUCCESS: Render job triggered with ID {job_id}. Status: {job['status']}")

    # 5. Check Render Job Status
    print(f"Checking render job {job_id} status...")
    res = httpx.get(f"{API_URL}/renders/{job_id}", headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Get render job failed: {res.text}")
        return False
    job_status = res.json()["status"]
    print(f"SUCCESS: Render job status checked: {job_status}.")

    print("--- E2E INTEGRATION FLOW PASSED ---")
    return True

if __name__ == "__main__":
    # We assume the server is running on localhost:8000
    try:
        run_e2e()
    except Exception as e:
        print(f"FAILED: Integration test error: {e}")
