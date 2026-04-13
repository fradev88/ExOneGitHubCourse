"""
FastAPI endpoints tests using AAA (Arrange-Act-Assert) pattern.

Tests for the High School Management System API covering:
- GET / (redirect to static)
- GET /activities (list all activities)
- POST /activities/{activity_name}/signup (student signup)
- DELETE /activities/{activity_name}/signup (remove student)
"""

from fastapi.testclient import TestClient
from src.app import app


# =============================================================================
# Fixtures and Setup
# =============================================================================

def get_test_client():
    """Create and return a TestClient instance for testing."""
    return TestClient(app)


# =============================================================================
# GET / - Root Redirect Endpoint
# =============================================================================

def test_root_redirects_to_static():
    """
    Arrange: Initialize TestClient
    Act: Make GET request to root endpoint
    Assert: Verify redirect response to /static/index.html
    """
    # Arrange
    client = get_test_client()

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in [307, 302]  # Redirect status codes
    assert "/static/index.html" in response.headers.get("location", "")


# =============================================================================
# GET /activities - List All Activities
# =============================================================================

def test_get_activities_returns_all_activities():
    """
    Arrange: Initialize TestClient
    Act: Make GET request to /activities
    Assert: Verify all 9 activities are returned with correct structure
    """
    # Arrange
    client = get_test_client()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 9
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Gym Class" in activities
    assert "Basketball Team" in activities
    assert "Soccer Club" in activities
    assert "Art Studio" in activities
    assert "Drama Club" in activities
    assert "Debate Team" in activities
    assert "Science Club" in activities


def test_get_activities_has_required_fields():
    """
    Arrange: Initialize TestClient
    Act: Make GET request to /activities
    Assert: Verify each activity has required fields
    """
    # Arrange
    client = get_test_client()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()

    for activity_name, activity_data in activities.items():
        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        assert isinstance(activity_data["participants"], list)


def test_get_activities_participants_are_emails():
    """
    Arrange: Initialize TestClient
    Act: Make GET request to /activities
    Assert: Verify participants are valid email addresses
    """
    # Arrange
    client = get_test_client()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()

    for activity_name, activity_data in activities.items():
        for participant in activity_data["participants"]:
            assert "@" in participant
            assert ".edu" in participant


# =============================================================================
# POST /activities/{activity_name}/signup - Sign Up for Activity
# =============================================================================

def test_signup_valid_activity_and_new_email():
    """
    Arrange: Initialize TestClient with a new email and valid activity
    Act: POST signup request for an available activity
    Assert: Verify successful signup (200) and email is added to participants
    """
    # Arrange
    client = get_test_client()
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    assert email in response.json()["message"]

    # Verify email was actually added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_email_returns_400():
    """
    Arrange: Initialize TestClient with an email already in an activity
    Act: Attempt to signup the same email again
    Assert: Verify 400 error and "already signed up" message
    """
    # Arrange
    client = get_test_client()
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already in Chess Club

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_nonexistent_activity_returns_404():
    """
    Arrange: Initialize TestClient with a non-existent activity name
    Act: POST signup request for activity that doesn't exist
    Assert: Verify 404 error and "Activity not found" message
    """
    # Arrange
    client = get_test_client()
    activity_name = "Nonexistent Activity"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_multiple_different_activities():
    """
    Arrange: Initialize TestClient with a new email
    Act: Sign up the email for multiple different activities
    Assert: Verify email appears in all activities after signup
    """
    # Arrange
    client = get_test_client()
    email = "multiactivity@mergington.edu"
    activities_to_join = ["Chess Club", "Drama Club", "Science Club"]

    # Act & Assert - Sign up for multiple activities
    for activity_name in activities_to_join:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200

    # Verify email is in all activities
    activities_response = client.get("/activities")
    activities = activities_response.json()
    for activity_name in activities_to_join:
        assert email in activities[activity_name]["participants"]


# =============================================================================
# DELETE /activities/{activity_name}/signup - Remove Student from Activity
# =============================================================================

def test_delete_remove_existing_participant():
    """
    Arrange: Initialize TestClient, add email to activity, then prepare to remove
    Act: DELETE request to remove the email from activity
    Assert: Verify successful removal (200) and email no longer in participants
    """
    # Arrange
    client = get_test_client()
    activity_name = "Chess Club"
    email = "tesdelete@mergington.edu"

    # First, add the email to the activity
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert "Removed" in response.json()["message"]

    # Verify email was actually removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity_name]["participants"]


def test_delete_nonexistent_participant_returns_404():
    """
    Arrange: Initialize TestClient with email not in activity
    Act: DELETE request for email that was never added to activity
    Assert: Verify 404 error and "Participant not found" message
    """
    # Arrange
    client = get_test_client()
    activity_name = "Chess Club"
    email = "nonexistent@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]


def test_delete_nonexistent_activity_returns_404():
    """
    Arrange: Initialize TestClient with non-existent activity
    Act: DELETE request for activity that doesn't exist
    Assert: Verify 404 error and "Activity not found" message
    """
    # Arrange
    client = get_test_client()
    activity_name = "Nonexistent Activity"
    email = "anyemail@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_delete_then_signup_again():
    """
    Arrange: Initialize TestClient, add and remove email from activity
    Act: Sign up the same email again to the same activity
    Assert: Verify email can be re-added successfully
    """
    # Arrange
    client = get_test_client()
    activity_name = "Drama Club"
    email = "testreaddsignup@mergington.edu"

    # Act & Assert - First signup
    response1 = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response1.status_code == 200

    # Act & Assert - Delete
    response2 = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response2.status_code == 200

    # Act & Assert - Re-signup
    response3 = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response3.status_code == 200

    # Verify email is back in the activity
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity_name]["participants"]


# =============================================================================
# Integration/Workflow Tests
# =============================================================================

def test_complete_signup_workflow():
    """
    Arrange: Initialize TestClient
    Act: Complete workflow - view activities, signup, verify, delete
    Assert: Verify each step works as expected
    """
    # Arrange
    client = get_test_client()
    activity_name = "Debate Team"
    email = "workflow@mergington.edu"

    # Act 1 - Get all activities
    response_get = client.get("/activities")
    assert response_get.status_code == 200

    # Act 2 - Sign up
    response_signup = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response_signup.status_code == 200

    # Act 3 - Verify signup by getting activities again
    response_verify = client.get("/activities")
    activities = response_verify.json()
    assert email in activities[activity_name]["participants"]

    # Act 4 - Remove from activity
    response_delete = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response_delete.status_code == 200

    # Act 5 - Verify removal
    response_final = client.get("/activities")
    activities = response_final.json()
    assert email not in activities[activity_name]["participants"]
