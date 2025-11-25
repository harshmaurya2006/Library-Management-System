import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",        # change if your MySQL user is different
        password="Maurya@2006",        # put your MySQL password here
        database="library_db",
        cursorclass=pymysql.cursors.DictCursor
    )
