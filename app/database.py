import os
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME", "hackathon_db"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )

def update_video_status(video_id, status, s3_zip_key=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if s3_zip_key:
        cur.execute("UPDATE Videos SET status = %s, s3_zip_key = %s WHERE id = %s", (status, s3_zip_key, video_id))
    else:
        cur.execute("UPDATE Videos SET status = %s WHERE id = %s", (status, video_id))
    conn.commit()
    cur.close()
    conn.close()