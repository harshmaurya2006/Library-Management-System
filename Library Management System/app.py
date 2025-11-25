from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date
from db_config import get_connection

app = Flask(__name__)
app.secret_key = "supersecretkey"  # you can change this


# ---------- HOME ----------


@app.route("/")
def index():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Basic stats
            cur.execute("SELECT COUNT(*) AS total_books FROM books")
            total_books = cur.fetchone()["total_books"]

            cur.execute("SELECT COUNT(*) AS total_members FROM members")
            total_members = cur.fetchone()["total_members"]

            cur.execute(
                "SELECT COUNT(*) AS total_issued FROM issued_books WHERE return_date IS NULL"
            )
            total_issued = cur.fetchone()["total_issued"]

            # For chart: available vs issued
            cur.execute(
                "SELECT COALESCE(SUM(quantity), 0) AS available_copies FROM books"
            )
            available_copies = cur.fetchone()["available_copies"]

            issued_copies = total_issued  # assuming each issue record = 1 copy

            # Most issued book
            cur.execute(
                """
                SELECT b.title, COUNT(*) AS issue_count
                FROM issued_books ib
                JOIN books b ON ib.book_id = b.id
                GROUP BY ib.book_id
                ORDER BY issue_count DESC
                LIMIT 1
            """
            )
            most_issued = cur.fetchone()

            # Recent activity (issue/return list)
            cur.execute(
                """
                SELECT ib.id,
                       b.title,
                       m.name AS member_name,
                       ib.issue_date,
                       ib.return_date
                FROM issued_books ib
                JOIN books b ON ib.book_id = b.id
                JOIN members m ON ib.member_id = m.id
                ORDER BY COALESCE(ib.return_date, ib.issue_date) DESC
                LIMIT 7
            """
            )
            recent_activities = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        "index.html",
        total_books=total_books,
        total_members=total_members,
        total_issued=total_issued,
        available_copies=available_copies,
        issued_copies=issued_copies,
        most_issued=most_issued,
        recent_activities=recent_activities,
    )


# ---------- BOOKS CRUD ----------


@app.route("/books")
def books():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM books")
            books = cur.fetchall()
    finally:
        conn.close()

    return render_template("books.html", books=books)


@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        quantity = request.form["quantity"]

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO books (title, author, isbn, quantity) VALUES (%s, %s, %s, %s)",
                    (title, author, isbn, quantity),
                )
            conn.commit()
            flash("Book added successfully!", "success")
        finally:
            conn.close()

        return redirect(url_for("books"))

    return render_template("add_book.html")


@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    conn = get_connection()
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        quantity = request.form["quantity"]

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE books SET title=%s, author=%s, isbn=%s, quantity=%s WHERE id=%s",
                    (title, author, isbn, quantity, book_id),
                )
            conn.commit()
            flash("Book updated successfully!", "success")
        finally:
            conn.close()

        return redirect(url_for("books"))
    else:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM books WHERE id=%s", (book_id,))
                book = cur.fetchone()
        finally:
            conn.close()

        if not book:
            flash("Book not found!", "danger")
            return redirect(url_for("books"))

        return render_template("edit_book.html", book=book)


@app.route("/books/delete/<int:book_id>")
def delete_book(book_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM books WHERE id=%s", (book_id,))
        conn.commit()
        flash("Book deleted successfully!", "success")
    finally:
        conn.close()

    return redirect(url_for("books"))


# ---------- MEMBERS CRUD ----------


@app.route("/members")
def members():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM members")
            members = cur.fetchall()
    finally:
        conn.close()

    return render_template("members.html", members=members)


@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO members (name, email, phone) VALUES (%s, %s, %s)",
                    (name, email, phone),
                )
            conn.commit()
            flash("Member added successfully!", "success")
        finally:
            conn.close()

        return redirect(url_for("members"))

    return render_template("add_member.html")


# ---------- ISSUE / RETURN BOOKS ----------


@app.route("/issue", methods=["GET", "POST"])
def issue_book():
    conn = get_connection()
    if request.method == "POST":
        book_id = request.form["book_id"]
        member_id = request.form["member_id"]

        try:
            with conn.cursor() as cur:
                # Check quantity
                cur.execute("SELECT quantity FROM books WHERE id=%s", (book_id,))
                book = cur.fetchone()
                if not book or book["quantity"] <= 0:
                    flash("Book is not available to issue!", "danger")
                    return redirect(url_for("issue_book"))

                # Insert issue record
                cur.execute(
                    "INSERT INTO issued_books (book_id, member_id, issue_date) VALUES (%s, %s, %s)",
                    (book_id, member_id, date.today()),
                )

                # Decrease book quantity
                cur.execute(
                    "UPDATE books SET quantity = quantity - 1 WHERE id=%s", (book_id,)
                )

            conn.commit()
            flash("Book issued successfully!", "success")
        finally:
            conn.close()

        return redirect(url_for("issued_books"))
    else:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM books WHERE quantity > 0")
                books = cur.fetchall()

                cur.execute("SELECT * FROM members")
                members = cur.fetchall()
        finally:
            conn.close()

        return render_template("issue_book.html", books=books, members=members)


@app.route("/issued")
def issued_books():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ib.id, b.title, m.name AS member_name,
                ib.issue_date, ib.return_date
                FROM issued_books ib
                JOIN books b ON ib.book_id = b.id
                JOIN members m ON ib.member_id = m.id
                ORDER BY ib.issue_date DESC
            """
            )
            issued = cur.fetchall()
    finally:
        conn.close()

    return render_template("issued_books.html", issued=issued)


@app.route("/return/<int:issue_id>", methods=["POST"])
def return_book(issue_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Find the issue record
            cur.execute("SELECT * FROM issued_books WHERE id=%s", (issue_id,))
            issue = cur.fetchone()

            if not issue:
                flash("Issue record not found!", "danger")
                return redirect(url_for("issued_books"))

            if issue["return_date"] is not None:
                flash("This book is already returned!", "warning")
                return redirect(url_for("issued_books"))

            # Set return date
            cur.execute(
                "UPDATE issued_books SET return_date=%s WHERE id=%s",
                (date.today(), issue_id),
            )

            # Increase book quantity
            cur.execute(
                "UPDATE books SET quantity = quantity + 1 WHERE id=%s",
                (issue["book_id"],),
            )

        conn.commit()
        flash("Book returned successfully ✅", "success")
    finally:
        conn.close()

    return redirect(url_for("issued_books"))


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    books = []
    members = []

    if query:
        like = f"%{query}%"
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Search books
                cur.execute(
                    """
                    SELECT * FROM books
                    WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s
                """,
                    (like, like, like),
                )
                books = cur.fetchall()

                # Search members
                cur.execute(
                    """
                    SELECT * FROM members
                    WHERE name LIKE %s OR email LIKE %s OR phone LIKE %s
                """,
                    (like, like, like),
                )
                members = cur.fetchall()
        finally:
            conn.close()

    return render_template(
        "search_results.html", query=query, books=books, members=members
    )


if __name__ == "__main__":
    app.run(debug=True)
