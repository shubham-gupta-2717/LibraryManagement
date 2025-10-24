from flask import Flask, render_template, request, redirect
from db_config import get_connection

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/books')
def view_books():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Book")
    books = cursor.fetchall()
    conn.close()
    return render_template('books.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        publisher = request.form['publisher']
        year = request.form['year']
        genre = request.form['genre']
        copies = request.form['copies']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Book (Title, Author, Publisher, Year, Genre, CopiesAvailable)
            VALUES (:1, :2, :3, :4, :5, :6)
        """, (title, author, publisher, year, genre, copies))
        conn.commit()
        conn.close()
        return redirect('/books')

    return render_template('add_book.html')

# ====== Members ======
@app.route('/members')
def view_members():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Member")
    members = cursor.fetchall()
    conn.close()
    return render_template('members.html', members=members)

@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Member (Name, Email, Phone)
            VALUES (:1, :2, :3)
        """, (name, email, phone))
        conn.commit()
        conn.close()
        return redirect('/members')
    return render_template('add_member.html')

@app.route('/borrow', methods=['GET', 'POST'])
def borrow_book():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get available books
    cursor.execute("SELECT BookID, Title, CopiesAvailable FROM Book WHERE CopiesAvailable > 0")
    books = cursor.fetchall()
    
    # Get members
    cursor.execute("SELECT MemberID, Name FROM Member")
    members = cursor.fetchall()
    
    if request.method == 'POST':
        book_id = request.form['book_id']
        member_id = request.form['member_id']
        
        # Insert into Borrow table
        cursor.execute("""
            INSERT INTO Borrow (MemberID, BookID, BorrowDate, DueDate)
            VALUES (:1, :2, SYSDATE, SYSDATE + 14)
        """, (member_id, book_id))
        
        # Decrease available copies
        cursor.execute("UPDATE Book SET CopiesAvailable = CopiesAvailable - 1 WHERE BookID = :1", (book_id,))
        
        conn.commit()
        conn.close()
        return redirect('/borrow')
    
    conn.close()
    return render_template('borrow.html', books=books, members=members)

@app.route('/return', methods=['GET', 'POST'])
def return_book():
    conn = get_connection()
    cursor = conn.cursor()

    # Get borrowed books that are not returned yet
    cursor.execute("""
        SELECT b.BorrowID, m.Name, bk.Title
        FROM Borrow b
        JOIN Member m ON b.MemberID = m.MemberID
        JOIN Book bk ON b.BookID = bk.BookID
        WHERE b.ReturnDate IS NULL
    """)
    borrowed_books = cursor.fetchall()

    if request.method == 'POST':
        borrow_id = request.form['borrow_id']

        # Get the BookID for the borrowed record
        cursor.execute("SELECT BookID FROM Borrow WHERE BorrowID = :1", (borrow_id,))
        book_id = cursor.fetchone()[0]

        # Update ReturnDate
        cursor.execute("UPDATE Borrow SET ReturnDate = SYSDATE WHERE BorrowID = :1", (borrow_id,))
        
        # Increase available copies
        cursor.execute("UPDATE Book SET CopiesAvailable = CopiesAvailable + 1 WHERE BookID = :1", (book_id,))

        conn.commit()
        conn.close()
        return redirect('/return')

    conn.close()
    return render_template('return.html', borrowed_books=borrowed_books)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Optional: Prevent deleting borrowed books
    cursor.execute("SELECT COUNT(*) FROM Borrow WHERE BookID = :1 AND ReturnDate IS NULL", (book_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return "Cannot delete: Book is currently borrowed."
    
    cursor.execute("DELETE FROM Book WHERE BookID = :1", (book_id,))
    conn.commit()
    conn.close()
    return redirect('/books')

@app.route('/delete_borrow/<int:borrow_id>', methods=['POST'])
def delete_borrow(borrow_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Borrow WHERE BorrowID = :1", (borrow_id,))
    conn.commit()
    conn.close()
    return redirect('/return')  # or redirect somewhere else


if __name__ == '__main__':
    app.run(debug=True)