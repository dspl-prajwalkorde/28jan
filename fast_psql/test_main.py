import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base, Employee

# --- TEST DATABASE CONFIGURATION ---
# Ensure 'testdb_test' exists in your PostgreSQL server
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/testdb_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class FastAPITestCase(unittest.TestCase):

    def setUp(self):
        """
        Runs before EACH test.
        1. Creates the tables in the test database.
        2. Overrides the database dependency to use the test database.
        """
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Define the override function
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        # Apply the override
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        """
        Runs after EACH test.
        Drops all tables to ensure a clean state for the next test.
        """
        Base.metadata.drop_all(bind=engine)
        # Clear overrides
        app.dependency_overrides.clear()

    # --- POSITIVE TEST CASES ---

    def test_create_employee(self):
        payload = {"name": "Alice", "role": "Developer"}
        response = self.client.post("/employees", json=payload)
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Alice")
        self.assertIn("id", data)

    def test_read_employees(self):
        # Create one first
        self.client.post("/employees", json={"name": "Bob", "role": "Manager"})
        
        response = self.client.get("/employees")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)

    def test_read_one_employee(self):
        # Create
        res = self.client.post("/employees", json={"name": "Charlie", "role": "Tester"})
        emp_id = res.json()["id"]
        
        # Read
        response = self.client.get(f"/employees/{emp_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Charlie")

    def test_update_employee(self):
        # Create
        res = self.client.post("/employees", json={"name": "Dave", "role": "Intern"})
        emp_id = res.json()["id"]
        
        # Update
        payload = {"name": "David", "role": "Junior Dev"}
        response = self.client.put(f"/employees/{emp_id}", json=payload)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "David")
        self.assertEqual(response.json()["role"], "Junior Dev")

    def test_delete_employee(self):
        # Create
        res = self.client.post("/employees", json={"name": "Eve", "role": "HR"})
        emp_id = res.json()["id"]
        
        # Delete
        response = self.client.delete(f"/employees/{emp_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Employee deleted")

    # --- NEGATIVE TEST CASES ---

    def test_create_duplicate_employee(self):
        payload = {"name": "Frank", "role": "CEO"}
        # First creation - Success
        self.client.post("/employees", json=payload)
        
        # Second creation - Should Fail
        response = self.client.post("/employees", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "Employee with this name and role already exists")

    def test_create_employee_missing_data(self):
        # Missing 'role'
        payload = {"name": "Ghost"}
        response = self.client.post("/employees", json=payload)
        # FastAPI returns 422 Unprocessable Entity for schema validation errors
        self.assertEqual(response.status_code, 422)

    def test_read_nonexistent_employee(self):
        response = self.client.get("/employees/9999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Employee not found")

    def test_update_nonexistent_employee(self):
        payload = {"name": "New", "role": "Role"}
        response = self.client.put("/employees/9999", json=payload)
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_employee(self):
        response = self.client.delete("/employees/9999")
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
