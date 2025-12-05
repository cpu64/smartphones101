# models/db.py
import psycopg2
import os
import sys

db_params = {
    'dbname': os.getenv('PGDATABASE', 'smartphonesioi'),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', 'secure'),
    'host': os.getenv('PGHOST', 'localhost'),
    'port': os.getenv('PGPORT', 5432)
}

def get_db_connection():
    return psycopg2.connect(**db_params)

def execute(query, values=()):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, values)
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_one(query, values=()):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, values)
        data = cur.fetchone()
        conn.commit()
        if data:
            columns = [desc[0] for desc in cur.description]
            data_dict = dict(zip(columns, data))
            return data_dict
        return None
    except Exception as e:
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_all(query, values=()):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, values)
        data = cur.fetchall()
        conn.commit()
        if data:
            columns = [desc[0] for desc in cur.description]
            data_dict = [dict(zip(columns, i)) for i in data]
            return data_dict
        return []

    except Exception as e:
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def init_db():
    conn = None
    cur = None
    try:
        from .users import USER_COLUMN_LENGTHS

        conn = get_db_connection()
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("""
            CREATE SCHEMA IF NOT EXISTS smartphonesioi;
            ALTER DATABASE smartphonesioi
                SET search_path = smartphonesioi, public;
            SET search_path TO smartphonesioi;
        """)

        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                    CREATE TYPE user_role AS ENUM ('admin', 'consultant', 'user');
                END IF;
            END
            $$;
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            username VARCHAR(%(username_length)s) UNIQUE NOT NULL,
            email VARCHAR(30) UNIQUE NOT NULL,
            password VARCHAR(%(password_length)s) NOT NULL,
            role user_role NOT NULL DEFAULT 'user',
            created_at TIMESTAMPTZ DEFAULT now(),
            timetable INT[3][8] DEFAULT '{{NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL},
                                        {NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL},
                                        {NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL}}',
            credits INT DEFAULT 0 CHECK (credits >= 0)
        );

        CREATE OR REPLACE FUNCTION shift_consultant_timetables()
        RETURNS void AS $$
        BEGIN
            UPDATE users
            SET timetable = ARRAY[
                (SELECT array_agg(x) FROM unnest(timetable[2:2]) AS x),
                (SELECT array_agg(x) FROM unnest(timetable[3:3]) AS x),
                array_fill(NULL::int, ARRAY[8])
            ]
            WHERE role = 'consultant';
        END;
        $$ LANGUAGE plpgsql;

        CREATE EXTENSION IF NOT EXISTS pg_cron;

        SELECT cron.schedule(
            'shift_timetables_midnight',
            '0 0 * * *',
            $$ SELECT shift_consultant_timetables(); $$
        );


        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

        CREATE TABLE IF NOT EXISTS requests (
            id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            amount INT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);

        CREATE TABLE IF NOT EXISTS reviews (
            id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            review_text TEXT,
            rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
            created_at TIMESTAMPTZ DEFAULT now(),
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            consultant_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chat (
            id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            consultant_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE (user_id, consultant_id)
        );

        CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_consultant_id ON chat(consultant_id);

        CREATE TABLE IF NOT EXISTS messages (
            id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            sender_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL CHECK (length(trim(message)) > 0),
            sent_at TIMESTAMPTZ DEFAULT now(),
            chat_id INT NOT NULL REFERENCES chat(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
        CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at DESC);

        CREATE TABLE IF NOT EXISTS can_review (
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            consultant_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, consultant_id)
        );

        CREATE TABLE IF NOT EXISTS faqs (
            id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            question TEXT NOT NULL CHECK (length(trim(question)) > 0),
            answer TEXT NOT NULL CHECK (length(trim(answer)) > 0),
            created_at TIMESTAMPTZ DEFAULT now()
        );

        INSERT INTO users (username, email, password, role, credits)
        VALUES ('admin', 'admin@t.com', '$2b$12$VEUlGiag6gJv.S6i51/i3Ov00lICVZsK37xVwA/1wC5KBVvJItgUK', 'admin', 0)
        ON CONFLICT (username) DO NOTHING;
        """, {
            'username_length': USER_COLUMN_LENGTHS['username'][1],
            'password_length': USER_COLUMN_LENGTHS['password'][1],
        })

        print("Database initialized successfully!")

    except Exception as e:
        print(f"Error occurred: {e}")
        if conn:
            conn.close()
        sys.exit(1)

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
