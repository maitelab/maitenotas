"""
Application: Maitenotas
Made by Taksan Tong
https://github.com/maitelab/maitenotas

Functions related to read/write data """
import sqlite3
from typing import Optional
from cryptography.fernet import Fernet
from crypto import encrypt_text_to_data, decrypt_data_to_text
import text_labels

# ***************** SQL
SQL_CREATE_BOOK_TABLE = """
CREATE TABLE IF NOT EXISTS book (
    id integer PRIMARY KEY AUTOINCREMENT,
    book_name blob NOT NULL
); """

SQL_CREATE_JOURNAL_TABLE = """
CREATE TABLE IF NOT EXISTS journal (
    book_id integer,
    parent_id integer,
    id integer PRIMARY KEY AUTOINCREMENT,
    journal_name blob NOT NULL,
    journal_text blob NOT NULL
); """

SQL_INSERT_BOOK = """
INSERT INTO book(book_name)
VALUES(?)"""

SQL_INSERT_JOURNAL = """
INSERT INTO journal(book_id,parent_id,journal_name,journal_text)
VALUES(?,?,?,?)"""

SQL_READ_ALL_JOURNAL = """
select parent_id,id,journal_name 
from journal
where book_id=?
order by parent_id,id
"""

SQL_READ_BOOK_NAME = """
select book_name
from book
where id=?
"""

SQL_READ_JOURNAL_TEXT = """
select journal_text
from journal
where id=?
"""

SQL_UPDATE_JOURNAL_TEXT = """
update journal
set journal_text=?
where id=?
"""

# ****************** DATABASE NAME and main operations
DATABASE_NAME = r"maitenotas.data"

def create_connection(dbfile) -> Optional[sqlite3.Connection]:
    """ create a database connection to the SQLite database
        specified by dbfile
    :param dbfile: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(dbfile)
        return conn
    except Exception as exception:
        print(str(exception))
    return conn

def create_table(conn: sqlite3.Connection, create_tablesql: str) -> None:
    """ create a table from the create_tablesql statement"""
    try:
        cursor = conn.cursor()
        cursor.execute(create_tablesql)
    except Exception as exception:
        print(str(exception))

# **************** entity operations
def update_journal_text(user_key: Fernet, journal_id: int, new_journal_text: str) -> None:
    """update journal table"""
    try:
        conn = create_connection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data = encrypt_text_to_data(new_journal_text, user_key)
            datas=(encrypted_data, journal_id,)
            cur.execute(SQL_UPDATE_JOURNAL_TEXT, datas)
            conn.commit()
    except Exception as exception:
        print(str(exception))
    finally:
        if conn:
            conn.close()

def update_journal_name(user_key: Fernet, journal_id: int, new_journal_name: str) -> None:
    """update journal name"""
    sql = """
    update journal
    set journal_name=?
    where id=?
    """
    try:
        conn = create_connection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data = encrypt_text_to_data(new_journal_name, user_key)
            data_forsql=(encrypted_data, journal_id)
            cur.execute(sql, data_forsql)
            conn.commit()
    except Exception as exception:
        print(str(exception))
    finally:
        if conn:
            conn.close()

def delete_journal(journal_id: int) -> None:
    """delete journal"""
    try:
        conn = create_connection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute("delete from journal where id=?", (journal_id,))
            conn.commit()
    except Exception as exception:
        print(str(exception))
    finally:
        if conn:
            conn.close()

def get_book_name(user_key: Fernet, book_id: int) -> str:
    """read book name, it will become the tree name in the user interface"""
    book_name = text_labels.BOOK_NAME
    try:
        conn = create_connection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(SQL_READ_BOOK_NAME, (book_id,))
            record = cur.fetchall()
            for row in record:
                # read columns
                book_name = decrypt_data_to_text(row[0], user_key)
    except Exception as exception:
        print(str(exception))
    finally:
        if conn:
            conn.close()
    return book_name

def get_journal_text(user_key: Fernet, journal_id) -> str:
    """get journal text"""
    journal_text = ""
    try:
        conn = create_connection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(SQL_READ_JOURNAL_TEXT, (journal_id,))
            record = cur.fetchall()
            for row in record:
                # read columns
                journal_text = decrypt_data_to_text(row[0], user_key)
    except Exception as exception:
        print(str(exception))
    finally:
        if conn:
            conn.close()
    return journal_text

def get_tree_leafs(user_key: Fernet) -> list:
    """read tree of book + journals from database
    for this first version the book id is always 2 (book id 1 is reserved)"""
    leaf_list = []
    try:
        conn = create_connection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            cur.execute(SQL_READ_ALL_JOURNAL, (2,))
            record = cur.fetchall()
            for row in record:
                # read columns
                parent_id = row[0]
                l_id = row[1]
                journal_name = decrypt_data_to_text(row[2], user_key)
                leaf_element = parent_id, l_id, journal_name
                leaf_list.append(leaf_element)
    except Exception as exception:
        print(str(exception))
    finally:
        if conn:
            conn.close()
    return leaf_list

def create_book(user_key: Fernet, book_name: str) -> int:
    """create book"""
    try:
        conn = create_connection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data = encrypt_text_to_data(book_name, user_key)
            data_tobe_inserted=(encrypted_data,)
            cur.execute(SQL_INSERT_BOOK, data_tobe_inserted)
            conn.commit()
            last_row_id = cur.lastrowid
            return last_row_id
    except Exception as exception:
        print(str(exception))
    finally:
        if conn:
            conn.close()
    return 0

def create_journal(user_key: Fernet, book_id: int, parent_leaf_id: int,
                  journal_name: str, journal_text: str) -> int:
    """create journal"""
    try:
        conn = create_connection(DATABASE_NAME)
        if conn is not None:
            cur = conn.cursor()
            encrypted_data_journal_name = encrypt_text_to_data(journal_name, user_key)
            encrypted_data_journal_text = encrypt_text_to_data(journal_text, user_key)
            data_tobe_inserted=(book_id, parent_leaf_id, encrypted_data_journal_name,
                              encrypted_data_journal_text,)
            cur.execute(SQL_INSERT_JOURNAL, data_tobe_inserted)
            conn.commit()
            last_row_id = cur.lastrowid
            return last_row_id
    except Exception as exception:
        print(str(exception))
    finally:
        if conn:
            conn.close()
    return 0

def create_database(user_key: Fernet, user_password: str) -> bool:
    """create databaase"""
    try:
        # create a database connection
        conn = create_connection(DATABASE_NAME)
        # create tables
        if conn is not None:
            # create tables
            create_table(conn, SQL_CREATE_BOOK_TABLE)
            create_table(conn, SQL_CREATE_JOURNAL_TABLE)
            # insert first book (this is a special book not for the user)
            cur = conn.cursor()
            encrypted_data = encrypt_text_to_data(user_password, user_key)
            data_tobe_inserted=(encrypted_data,)
            cur.execute(SQL_INSERT_BOOK, data_tobe_inserted)
            conn.commit()
        else:
            return False
    except Exception as exception:
        print(str(exception))
        return False
    finally:
        if conn:
            conn.close()
    return True

def verify_database_password(user_key: Fernet, user_password: str) -> bool:
    """verify db pass"""
    try:
        # create a database connection
        conn = create_connection(DATABASE_NAME)
        # create tables
        if conn is not None:
            # read book name from the first record
            cur = conn.cursor()
            cur.execute("SELECT book_name from book where id = ?", (1,))
            record = cur.fetchall()
            for row in record:
                # get encrypted blob
                encrypted_data = row[0]
                # do decrypt and validate
                decrypted_text = decrypt_data_to_text(encrypted_data, user_key)
                if decrypted_text != user_password:
                    print ("stored password does not match with provided pass")
                    return False
        else:
            return False
    except Exception as exception:
        print(str(exception))
        return False
    finally:
        if conn:
            conn.close()
    return True
