import sqlite3


def initialize_database(db="db/database.db3", schema="db/schema.sql"):
    cx = sqlite3.connect(db)
    with open(schema) as f:
        cx.executescript(f.read())
    cx.commit()
    cx.close()

if __name__ == "__main__":
    initialize_database()