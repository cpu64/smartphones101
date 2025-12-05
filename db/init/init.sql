CREATE SCHEMA IF NOT EXISTS smartphonesioi;
ALTER DATABASE smartphonesioi
    SET search_path = smartphonesioi, public;
SET search_path TO smartphonesioi;


DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('admin', 'consultant', 'user');
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS users (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(30) UNIQUE NOT NULL,
    email VARCHAR(60) UNIQUE NOT NULL,
    password VARCHAR(60) NOT NULL,
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
VALUES
    ('admin', 'admin@t.com', '$2b$12$VEUlGiag6gJv.S6i51/i3Ov00lICVZsK37xVwA/1wC5KBVvJItgUK', 'admin', 0),
    ('aaa', 'aaa@t.com', '$2b$12$o9GVcvT8VfmBN6BA.PVWb.zudArlfr5T6AL2V03uAYLKXmr/ez6aS', 'user', 2000),
    ('bbb', 'bbb@t.com', '$2b$12$gZWy1JhHy.SaMjVBlgs0zOz2AT.h8AI8ekaYyVlu1OVGZ.j28ZMA2', 'consultant', 0),
    ('ggg', 'ggg@t.com', '$2b$12$gZWy1JhHy.SaMjVBlgs0zOz2AT.h8AI8ekaYyVlu1OVGZ.j28ZMA2', 'consultant', 0);

INSERT INTO requests (user_id, amount)
VALUES (2, 50);

UPDATE users
SET timetable[2][3] = 1
WHERE id = 3 AND role = 'consultant';

-- INSERT INTO reviews (review_text, rating, user_id, consultant_id)
-- VALUES ('Great consultant, very helpful!', 5, 2, 3);

INSERT INTO chat (user_id, consultant_id)
VALUES (2, 3);

INSERT INTO faqs (question, answer)
VALUES
('How do I reset my password?', 'Go to settings -> password -> reset.'),
('How can I contact a consultant?', 'Use the chat feature to message a consultant directly.'),
('Can I increase my credits?', 'Yes, go to your profile and purchase additional credits.'),
('What is the refund policy?', 'Refunds are possible within 14 days of purchase.');
