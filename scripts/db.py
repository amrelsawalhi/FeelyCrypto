import os
import psycopg2


def db_connection():
    try:
        conn = psycopg2.connect(
                user=os.environ["SUPABASE_DB_USER"],
                password=os.environ["SUPABASE_DB_PASSWORD"],
                host=os.environ["SUPABASE_DB_HOST"],
                port=os.environ["SUPABASE_DB_PORT"],
                dbname=os.environ["SUPABASE_DB_NAME"],
                sslmode="require"
        )
        return conn
    except Exception as e:
        raise ConnectionError(f"❌ Failed to connect to DB: {e}")