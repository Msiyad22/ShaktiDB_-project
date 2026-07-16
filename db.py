import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
		port=5433,
        database="attendease",
        user="postgres",
        password="shaktidb"
    )

    return conn
