VALID = {
    "first_name": "Asha",
    "last_name": "Rao",
    "email": "asha@example.com",
    "phone": "+91 98765 43210",
    "department": "Engineering",
    "designation": "Developer",
    "date_of_joining": "2025-01-15",
    "salary": "85000",
}


def add(client, **overrides):
    return client.post("/add", data={**VALID, **overrides}, follow_redirects=True)


def test_empty_list(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"No employees found" in r.data


def test_add_and_list(client):
    r = add(client)
    assert b"Employee added successfully" in r.data
    assert b"Asha Rao" in r.data
    assert b"85,000.00" in r.data


def test_search_and_filter(client):
    add(client)
    add(client, first_name="Ravi", last_name="Kumar", email="ravi@example.com", department="HR")
    r = client.get("/?q=ravi")
    assert b"Ravi Kumar" in r.data and b"Asha Rao" not in r.data
    r = client.get("/?department=Engineering")
    assert b"Asha Rao" in r.data and b"Ravi Kumar" not in r.data


def test_duplicate_email_rejected(client):
    add(client)
    r = add(client, first_name="Other", email="ASHA@example.com")
    assert b"already exists" in r.data


def test_validation_errors(client):
    r = client.post("/add", data={**VALID, "first_name": "", "email": "bad", "salary": "-5"})
    assert b"First name is required" in r.data
    assert b"A valid email is required" in r.data
    assert b"Salary cannot be negative" in r.data
    assert b"No employees found" in client.get("/").data


def test_edit(client):
    add(client)
    r = client.post("/edit/1", data={**VALID, "department": "Finance", "salary": "90000"},
                    follow_redirects=True)
    assert b"Employee updated successfully" in r.data
    assert b"Finance" in r.data and b"90,000.00" in r.data


def test_edit_missing_employee(client):
    r = client.get("/edit/999", follow_redirects=True)
    assert b"Employee not found" in r.data


def test_delete(client):
    add(client)
    r = client.post("/delete/1", follow_redirects=True)
    assert b"Employee deleted" in r.data
    assert b"No employees found" in r.data
