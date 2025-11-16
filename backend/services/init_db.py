import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    # Connect to the default database
    conn = psycopg2.connect(
        dbname='postgres',
        user='smart_car_user',
        password='SecurePassword123!',
        host='localhost',
        port='5432'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Create the database if it doesn't exist
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'smart_car_surveillance'")
    exists = cur.fetchone()
    if not exists:
        cur.execute('CREATE DATABASE smart_car_surveillance')
        print("Created database smart_car_surveillance")
    
    # Connect to the new database
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    
    # Create the table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_job (
        job_id UUID PRIMARY KEY,
        car_id VARCHAR(50) NOT NULL,
        status VARCHAR(20) NOT NULL,
        s3_key TEXT,
        codec VARCHAR(10),
        sample_rate INTEGER,
        duration FLOAT,
        channels INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        checksum VARCHAR(64)
    );
    """)
    
    conn.commit()
    print("Created ingestion_job table")
    cur.close()
    conn.close()

if __name__ == '__main__':
    create_database()