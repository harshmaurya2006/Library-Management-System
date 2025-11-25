import random
from db_config import get_connection

titles = [
    "Python Basics", "Data Structures in C", "Java Fundamentals", "AI Revolution",
    "Machine Learning 101", "Operating Systems", "Discrete Maths", "Computer Networks",
    "Blockchain Explained", "Database Management", "Cyber Security Essentials",
    "Frontend Web Dev", "React in Action", "Flask Web Apps", "Android Development"
]

authors = [
    "John Watson", "Mark Lewis", "Albert Simon", "Richa Mehta", "Priya Sharma",
    "David Miller", "Neha Verma", "Vikram Rao", "Alex Carter", "Sam Wilson"
]

try:
    conn = get_connection()
    with conn.cursor() as cur:
        for _ in range(15):   # 15 random books
            title = random.choice(titles)
            author = random.choice(authors)
            isbn = random.randint(1000000000, 9999999999)
            quantity = random.randint(1, 10)

            cur.execute(
                "INSERT INTO books (title, author, isbn, quantity) VALUES (%s, %s, %s, %s)",
                (title, author, isbn, quantity)
            )

        conn.commit()
        print("✔ 15 Random Books Added Successfully!")
except Exception as e:
    print("Error:", str(e))
finally:
    conn.close()
