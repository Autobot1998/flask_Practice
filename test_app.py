import pytest
from app import app, mongo
from bson.objectid import ObjectId


@pytest.fixture
def client():
    app.config["TESTING"] = True

    # Use a separate test database from the application's normal database.
    # Replace the database name at the end if your Atlas URI already
    # contains a specific database name.
    original_uri = app.config["MONGO_URI"]

    if "/" in original_uri.rsplit("@", 1)[-1]:
        base_uri = original_uri.rsplit("/", 1)[0]
        test_uri = base_uri + "/test_student_db"
    else:
        test_uri = original_uri.rstrip("/") + "/test_student_db"

    app.config["MONGO_URI"] = test_uri

    # Re-initialize PyMongo with the test URI.
    mongo.init_app(app, tlsCAFile=__import__("certifi").where())

    client = app.test_client()

    # Setup: clear and create test data
    with app.app_context():
        mongo.db.students.delete_many({})
        mongo.db.students.insert_one({
            "_id": ObjectId("66fddff25f4b5f6a0a123456"),
            "name": "Test Student",
            "email": "test@student.com",
            "course": "Flask"
        })

    yield client

    # Teardown: clean up the test database
    with app.app_context():
        mongo.cx.drop_database("test_student_db")

    # Restore original application configuration
    app.config["MONGO_URI"] = original_uri


def test_home_page(client):
    """Test if home page loads correctly"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Test Student" in response.data


def test_add_student(client):
    """Test adding a new student"""
    data = {
        "name": "New User",
        "email": "new@user.com",
        "course": "Python"
    }

    response = client.post("/add", data=data, follow_redirects=True)

    assert response.status_code == 200
    assert b"New User" in response.data


def test_update_student(client):
    """Test updating a student"""
    student_id = "66fddff25f4b5f6a0a123456"

    data = {
        "name": "Updated Name",
        "email": "updated@student.com",
        "course": "Updated Course"
    }

    response = client.post(
        f"/update/{student_id}",
        data=data,
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Updated Name" in response.data


def test_delete_student(client):
    """Test deleting a student"""

    with app.app_context():
        student_id = mongo.db.students.insert_one({
            "name": "Temp User",
            "email": "temp@user.com",
            "course": "Temp Course"
        }).inserted_id

    response = client.get(
        f"/delete/{student_id}",
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Temp User" not in response.data

def test_health(client):
    """Test health endpoint and MongoDB connectivity"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"