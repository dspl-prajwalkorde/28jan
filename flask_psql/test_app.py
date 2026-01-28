import unittest
import json
from app import app, db, Book

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        """
        Runs before EACH test case.
        Sets up the app context and creates the tables in the test database.
        """
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        
        # Connect to the TEST database
        # Ensure 'testdb_test' is created in PostgreSQL before running this!
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/testdb_test'
        
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """
        Runs after EACH test case.
        Cleans up the database so tests don't interfere with each other.
        """
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # --- POSITIVE TEST CASES ---

    def test_create_book(self):
        """Test creating a valid book (201 Created)"""
        payload = {"title": "Test Book", "author": "Test Author"}
        response = self.app.post('/books', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Book created', str(response.data))

    def test_get_books(self):
        """Test retrieving list of books (200 OK)"""
        # Add a book first so we have something to get
        self.app.post('/books', json={"title": "B1", "author": "A1"})
        
        response = self.app.get('/books')
        self.assertEqual(response.status_code, 200)
        # Check that the list is not empty
        self.assertTrue(len(response.get_json()) > 0)

    def test_get_book_by_id(self):
        """Test retrieving a single book by ID (200 OK)"""
        # 1. Create book
        res = self.app.post('/books', json={"title": "Specific", "author": "Author"})
        book_id = res.get_json()['book']['id']
        
        # 2. Get book
        response = self.app.get(f'/books/{book_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['title'], "Specific")

    def test_update_book(self):
        """Test updating a book (200 OK)"""
        # 1. Create
        res = self.app.post('/books', json={"title": "Old", "author": "Old"})
        book_id = res.get_json()['book']['id']
        
        # 2. Update
        response = self.app.put(f'/books/{book_id}', json={"title": "New Title"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['book']['title'], "New Title")

    def test_delete_book(self):
        """Test deleting a book (200 OK)"""
        # 1. Create
        res = self.app.post('/books', json={"title": "Del", "author": "Del"})
        book_id = res.get_json()['book']['id']
        
        # 2. Delete
        response = self.app.delete(f'/books/{book_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Book deleted', str(response.data))

    # --- NEGATIVE TEST CASES ---

    def test_create_duplicate_book(self):
        """Test creating the same book twice (409 Conflict)"""
        payload = {"title": "Unique Book", "author": "Unique Author"}
        
        # 1. First add (Should succeed)
        response1 = self.app.post('/books', json=payload)
        self.assertEqual(response1.status_code, 201)
        
        # 2. Second add (Should fail)
        response2 = self.app.post('/books', json=payload)
        self.assertEqual(response2.status_code, 409)
        self.assertIn('Conflict', str(response2.data))

    def test_create_book_missing_data(self):
        """Test creating book with missing fields (400 Bad Request)"""
        response = self.app.post('/books', json={"title": "Only Title"})
        self.assertEqual(response.status_code, 400)

    def test_get_invalid_id(self):
        """Test getting a non-existent ID (404 Not Found)"""
        response = self.app.get('/books/999')
        self.assertEqual(response.status_code, 404)

    def test_update_invalid_id(self):
        """Test updating a non-existent ID (404 Not Found)"""
        response = self.app.put('/books/999', json={"title": "New"})
        self.assertEqual(response.status_code, 404)

    def test_delete_invalid_id(self):
        """Test deleting a non-existent ID (404 Not Found)"""
        response = self.app.delete('/books/999')
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()