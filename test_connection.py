import psycopg2
from scripts.api import fetch_fgi
def test_supabase_connection():
    try:
        conn = psycopg2.connect(
            user="postgres.czphxzerawrbpvlkslij", 
            password="Copyandpaste22_",
            host="aws-0-eu-west-1.pooler.supabase.com",
            port="5432",
            dbname="postgres",
            sslmode="require"
        )
        print("✅ Supabase connection successful")
        conn.close()
    except Exception as e:
        print("❌ Connection failed:", e)

if __name__ == "__main__":
    print(fetch_fgi())