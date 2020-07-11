""" 
Application: Maitenotas
Made by Taksan Tong
https://github.com/maitelab/maitenotas

Functions related to read/write data """
import sys

import sqlite3
from sqlite3 import Error

from crypto import encryptTextToData
from crypto import decryptDataToText

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

# ****************** DATABASE NAME and main operations
DATABASE_NAME = r"maitenotas.data"

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

# **************** entity operations
def updateJournalText(userKey, journalId, newJournalText):
    SQL_UPDATE_JOURNAL_TEXT = """
    update journal
    set journal_text=?
    where id=?
    """
    try:
        conn = create_connection(DATABASE_NAME)
    
        if conn is not None:
            cur = conn.cursor()
            
            encryptedData = encryptTextToData(newJournalText, userKey)
            
            dataForSQL=(encryptedData, journalId,)
            cur.execute(SQL_UPDATE_JOURNAL_TEXT, dataForSQL)
            
            conn.commit()
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
    finally:
        if conn:
            conn.close()
            
def updateJournalName(userKey, journalId, newJournalName):
    SQL_UPDATE_JOURNAL_NAME = """
    update journal
    set journal_name=?
    where id=?
    """
    try:
        conn = create_connection(DATABASE_NAME)
    
        if conn is not None:
            cur = conn.cursor()
            
            encryptedData = encryptTextToData(newJournalName, userKey)
            
            dataForSQL=(encryptedData, journalId)
            cur.execute(SQL_UPDATE_JOURNAL_NAME, dataForSQL)
            
            conn.commit()
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
    finally:
        if conn:
            conn.close()
            
def deleteJournal(journalId):
    SQL_DELETE_JOURNAL = """
    delete from journal
    where id=?
    """
    try:
        conn = create_connection(DATABASE_NAME)
    
        if conn is not None:
            cur = conn.cursor()
            
            print ("about to execute sql")
            cur.execute(SQL_DELETE_JOURNAL, (journalId,))
            print ("sql executed")
            conn.commit()
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
    finally:
        if conn:
            conn.close()

def getBookName(userKey, bookId):
    """
    SQL_READ_BOOK_NAME =  
    select book_name
    from book
    where id=?
    """
    # read book name, it will become the tree name in the user interface
    bookName = "Arbol"
    
    try:
        conn = create_connection(DATABASE_NAME)
    
        if conn is not None:
            cur = conn.cursor()
            
            cur.execute(SQL_READ_BOOK_NAME, (bookId,))
            record = cur.fetchall()
            for row in record:
                # read columns
                bookName = decryptDataToText(row[0], userKey)
            
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
    finally:
        if conn:
            conn.close()

    return bookName

def getJournalText(userKey, journalId):
    """ SQL_READ_JOURNAL_TEXT =
    select journal_text
    from journal
    where id=?
    """
    journalText = ""
    
    try:
        conn = create_connection(DATABASE_NAME)
    
        if conn is not None:
            cur = conn.cursor()
            
            cur.execute(SQL_READ_JOURNAL_TEXT, (journalId,))
            record = cur.fetchall()
            for row in record:
                # read columns
                journalText = decryptDataToText(row[0], userKey)
            
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
    finally:
        if conn:
            conn.close()

    return journalText

def getTreeLeafs(userKey):
    """
    element1 = 0 , 1 , "leaf 1"
    element2 = 0 , 2 , "leaf 2"
    element1_1 = 1 , 3 , "leaf 1_1"
    element2_1 = 2 , 4 , "leaf 2_1"
    element2_2 = 2 , 5 , "leaf 2_2"
    
    elementList = element1, element2, element1_1, element2_1, element2_2
    return elementList
    
    SQL_READ_ALL_JOURNAL
    select parent_id,id,journal_name,journal_text 
    from journal
    where book_id=?
    order by parent_id,id
    
    """
    # read tree of book + journals from database
    # for this first version the book id is always 2 (book id 1 is reserved)
    leafList = []
    
    try:
        conn = create_connection(DATABASE_NAME)
    
        if conn is not None:
            cur = conn.cursor()
            
            cur.execute(SQL_READ_ALL_JOURNAL, (2,))
            record = cur.fetchall()
            for row in record:
                # read columns
                parentId=row[0]
                id = row[1]
                journalName = decryptDataToText(row[2], userKey)
                leafElement = parentId, id, journalName
                leafList.append(leafElement)
            
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
    finally:
        if conn:
            conn.close()

    return leafList 

def createBook(userKey, bookName):
    try:
        conn = create_connection(DATABASE_NAME)
    
        if conn is not None:
            cur = conn.cursor()
            
            encryptedData = encryptTextToData(bookName, userKey)
            
            dataTobeInserted=(encryptedData,)
            cur.execute(SQL_INSERT_BOOK, dataTobeInserted)
            
            conn.commit()
            
            lastRowId = cur.lastrowid
            return lastRowId
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
    finally:
        if conn:
            conn.close()
            
def createJournal(userKey, bookId, parentLeafId, journalName, journalText):
    try:
        conn = create_connection(DATABASE_NAME)
    
        if conn is not None:
            cur = conn.cursor()
            
            encryptedDataJournalName = encryptTextToData(journalName, userKey)
            encryptedDataJournalText = encryptTextToData(journalText, userKey)
            
            # INSERT INTO journal(book_id,parent_id,journal_name,journal_text)
            dataTobeInserted=(bookId, parentLeafId, encryptedDataJournalName,encryptedDataJournalText,)
            cur.execute(SQL_INSERT_JOURNAL, dataTobeInserted)
            
            conn.commit()
            
            lastRowId = cur.lastrowid
            return lastRowId            
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
    finally:
        if conn:
            conn.close()

def createDatabase(userKey, userPassword):
    try:
        # create a database connection
        conn = create_connection(DATABASE_NAME)
        
        # create tables
        if conn is not None:
            # create tables
            create_table(conn, SQL_CREATE_BOOK_TABLE)
            create_table(conn, SQL_CREATE_JOURNAL_TABLE)
            
            # insert first book (this is a special book not for the user)
            sqlInsertBook = """
            INSERT INTO book(book_name)
            VALUES(?)"""
            cur = conn.cursor()
            
            encryptedData = encryptTextToData(userPassword, userKey)
            
            dataTobeInserted=(encryptedData,)
            cur.execute(SQL_INSERT_BOOK, dataTobeInserted)
            
            conn.commit()
        else:
            return False
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
        return False
    finally:
        if conn:
            conn.close()
            
    return True
    
def verifyDatabasePassword(userKey, userPassword):
    try:
        # create a database connection
        conn = create_connection(DATABASE_NAME)
    
        sql_fetch_blob_query = """SELECT book_name from book where id = ?"""
        
        # create tables
        if conn is not None:
            # read book name from the first record
            cur = conn.cursor()
            cur.execute(sql_fetch_blob_query, (1,))
            
            record = cur.fetchall()
            for row in record:
                # get encrypted blob
                encryptedData = row[0]
                # do decrypt
                decryptedText = decryptDataToText(encryptedData, userKey)
                
                if decryptedText != userPassword:
                    print ("stored password does not match with provided pass")
                    return False
 
        else:
            return False
    except:
        print("Oops!", sys.exc_info()[0], "occurred.")
        return False
    finally:
        if conn:
            conn.close()
            
    return True