from app.config import settings

def test_create_project(client, token_headers):
    response = client.post(
        f"{settings.API_V1_STR}/projects",
        json={"name": "Test Project", "description": "This is a test project description"},
        headers=token_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "This is a test project description"
    assert "id" in data

def test_list_projects(client, token_headers):
    client.post(
        f"{settings.API_V1_STR}/projects",
        json={"name": "Project 1"},
        headers=token_headers
    )
    client.post(
        f"{settings.API_V1_STR}/projects",
        json={"name": "Project 2"},
        headers=token_headers
    )
    response = client.get(
        f"{settings.API_V1_STR}/projects",
        headers=token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_get_project_by_id(client, token_headers):
    post_res = client.post(
        f"{settings.API_V1_STR}/projects",
        json={"name": "Unique Project"},
        headers=token_headers
    )
    project_id = post_res.json()["id"]

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project_id}",
        headers=token_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Unique Project"

def test_update_project(client, token_headers):
    post_res = client.post(
        f"{settings.API_V1_STR}/projects",
        json={"name": "Old Project Name"},
        headers=token_headers
    )
    project_id = post_res.json()["id"]

    response = client.put(
        f"{settings.API_V1_STR}/projects/{project_id}",
        json={"name": "New Project Name", "description": "Updated"},
        headers=token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Project Name"
    assert data["description"] == "Updated"

def test_delete_project(client, token_headers):
    post_res = client.post(
        f"{settings.API_V1_STR}/projects",
        json={"name": "Delete Me"},
        headers=token_headers
    )
    project_id = post_res.json()["id"]

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project_id}",
        headers=token_headers
    )
    assert response.status_code == 204

    # Verify project is gone
    get_res = client.get(
        f"{settings.API_V1_STR}/projects/{project_id}",
        headers=token_headers
    )
    assert get_res.status_code == 404
