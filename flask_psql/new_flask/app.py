from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
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
        # --- STRIP WHITESPACE & EMPTY CHECK ---
        title = data['title'].strip()
        author = data['author'].strip()

        if not title or not author:
            return make_response(jsonify({'message': 'Title and Author cannot be empty or whitespace only'}), 400)
        
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
    
#*************************************
@app.route('/books/page', methods=['GET'])
def books_page():
    try:
        # --- GET QUERY PARAMETERS ---
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        sort_field = request.args.get('sort', 'title')
        sort_order = request.args.get('order', 'asc')
        filter_title = request.args.get('title', '')
        filter_author = request.args.get('author', '')

        # --- BUILD QUERY ---
        query = Book.query

        if filter_title:
            query = query.filter(Book.title.ilike(f'%{filter_title}%'))
        if filter_author:
            query = query.filter(Book.author.ilike(f'%{filter_author}%'))

        # Sorting
        if sort_order == 'asc':
            query = query.order_by(getattr(Book, sort_field).asc())
        else:
            query = query.order_by(getattr(Book, sort_field).desc())

        # Pagination
        total = query.count()
        books = query.offset((page - 1) * limit).limit(limit).all()

        return render_template(
            'books.html',
            books=books,
            page=page,
            limit=limit,
            total=total,
            sort_field=sort_field,
            sort_order=sort_order,
            filter_title=filter_title,
            filter_author=filter_author
        )
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)
#*************************************

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
        if not data:
            return make_response(jsonify({'message': 'No data provided'}), 400)

        # --- STRIP WHITESPACE & CHECK EMPTY ---
        if 'title' in data:
            new_title = data['title'].strip()  # Remove leading/trailing spaces
            if not new_title:  # Check if empty after stripping
                return make_response(jsonify({'message': 'Title cannot be empty or whitespace only'}), 400)
            book.title = new_title

        if 'author' in data:
            new_author = data['author'].strip()  # Remove leading/trailing spaces
            if not new_author:  # Check if empty after stripping
                return make_response(jsonify({'message': 'Author cannot be empty or whitespace only'}), 400)
            book.author = new_author
            
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