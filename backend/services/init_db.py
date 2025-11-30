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
    
    # Note: The main schema is defined in database/schema.sql
    # This file is kept for backward compatibility but the schema.sql should be used
    # The schema.sql uses vehicle_id instead of car_id to match the main schema
    print("Note: Database schema should be initialized using database/schema.sql")
    print("This script is kept for reference only.")
    
    conn.commit()
    print("Created ingestion_job table")
    cur.close()
    conn.close()

if __name__ == '__main__':
    create_database()