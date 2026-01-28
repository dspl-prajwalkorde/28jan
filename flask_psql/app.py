from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://postgres:password@localhost:5432/testdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODEL ---
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)

    def json(self):
        return {'id': self.id, 'title': self.title, 'author': self.author}

# Create tables automatically (Requires database 'testdb' to exist)
with app.app_context():
    db.create_all()

@app.route('/books', methods=['POST'])
def create_book():
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'author' not in data:
            return make_response(jsonify({'message': 'Bad Request: Title and Author are required'}), 400)
        
        # --- NEW VALIDATION START ---
        # Check if a book with the same title AND author already exists
        existing_book = Book.query.filter_by(title=data['title'], author=data['author']).first()
        
        if existing_book:
            return make_response(jsonify({'message': 'Conflict: This book already exists in the database'}), 409)
        # --- NEW VALIDATION END ---

        new_book = Book(title=data['title'], author=data['author'])
        db.session.add(new_book)
        db.session.commit()
        return make_response(jsonify({'message': 'Book created', 'book': new_book.json()}), 201)
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/books', methods=['GET'])
def get_books():
    try:
        books = Book.query.all()
        return make_response(jsonify([book.json() for book in books]), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/books/<int:id>', methods=['GET'])
def get_book(id):
    try:
        book = Book.query.get(id)
        if book:
            return make_response(jsonify(book.json()), 200)
        return make_response(jsonify({'message': 'Book not found'}), 404)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/books/<int:id>', methods=['PUT'])
def update_book(id):
    try:
        book = Book.query.get(id)
        if not book:
            return make_response(jsonify({'message': 'Book not found'}), 404)
        
        data = request.get_json()
        if 'title' in data: book.title = data['title']
        if 'author' in data: book.author = data['author']
            
        db.session.commit()
        return make_response(jsonify({'message': 'Book updated', 'book': book.json()}), 200)
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    try:
        book = Book.query.get(id)
        if not book:
            return make_response(jsonify({'message': 'Book not found'}), 404)
        
        db.session.delete(book)
        db.session.commit()
        return make_response(jsonify({'message': 'Book deleted'}), 200)
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({'error': str(e)}), 500)

if __name__ == '__main__':
    app.run(debug=True)