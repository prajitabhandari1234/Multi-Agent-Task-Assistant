def test_root_endpoint(client):
    """
    Test the root API endpoint.
    """

    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Multi-Agent Task Assistant API"
    }


def test_create_task_endpoint(client):
    """
    Test creating a task through FastAPI.
    """

    response = client.post(
        "/tasks",
        json={
            "title": "Complete Assessment 3",
            "description": "Finish coding and testing",
            "priority": "high"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["title"] == "Complete Assessment 3"
    assert data["priority"] == "high"


def test_get_all_tasks_endpoint(client):
    """
    Test retrieving all tasks through FastAPI.
    """

    client.post(
        "/tasks",
        json={
            "title": "Task 1"
        }
    )

    client.post(
        "/tasks",
        json={
            "title": "Task 2"
        }
    )

    response = client.get(
        "/tasks"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_get_task_endpoint(client):
    """
    Test retrieving one existing task.
    """

    create_response = client.post(
        "/tasks",
        json={
            "title": "Existing task"
        }
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/tasks/{task_id}"
    )

    assert response.status_code == 200

    assert response.json()["title"] == "Existing task"


def test_get_missing_task_returns_404(client):
    """
    Test requesting a task that does not exist.
    """

    response = client.get(
        "/tasks/999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Task not found"


def test_update_task_endpoint(client):
    """
    Test updating a task through FastAPI.
    """

    create_response = client.post(
        "/tasks",
        json={
            "title": "Original task"
        }
    )

    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Updated task",
            "priority": "high"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task_id
    assert data["title"] == "Updated task"
    assert data["priority"] == "high"


def test_delete_task_endpoint(client):
    """
    Test deleting a task through FastAPI.
    """

    create_response = client.post(
        "/tasks",
        json={
            "title": "Delete task"
        }
    )

    task_id = create_response.json()["id"]

    response = client.delete(
        f"/tasks/{task_id}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Task deleted successfully"
    }