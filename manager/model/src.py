"""
Создание пустой базы данных
"""

import sqlite3

def create_empty_db(db_path):
    """
    Создание пустой базы данных
    """
    connection = sqlite3.connect(db_path)
    connection.close() # закрываем соединение
    print('Создана пустая база данных')

def create_empty_db_crossbar(db_path,
                             serial = "ННГУ-1_для_отладки",
                             comment = "Кроссбар 32х8 1T1R",
                             bl_num = 32,
                             wl_num = 8,
                             cb_type = 'simulator'):
    """
    Cоздание таблиц и их заполнение
    """
    status = False
    crossbar_id = 0
    try:
        connection = sqlite3.connect(db_path) # выполняется подключение к базе данных
        cursor = connection.cursor() # позволяет выполнять SQLite-запросы
        print("База данных создана и успешно подключена к SQLite")

        ##############################################################################

        # создание таблицы кроссбары
        CREATE_TABLE_QUERY = '''CREATE TABLE IF NOT EXISTS Crossbars (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    serial TEXT NOT NULL UNIQUE,
                                    comment TEXT NOT NULL,
                                    bl INTEGER NOT NULL,
                                    wl INTEGER NOT NULL,
                                    cb_type TEXT NOT NULL
                                    );'''

        cursor.execute(CREATE_TABLE_QUERY) # выполнить запрос в базу данных
        connection.commit() # сохранить изменение
        print("Таблица Crossbars создана")

        INSERT_QUERY = "INSERT INTO Crossbars (serial, comment, bl, wl, cb_type) VALUES (?,?,?,?,?);"
        cursor.execute(INSERT_QUERY, (serial, comment, bl_num, wl_num, cb_type))
        connection.commit() # сохранить изменение
        print("Таблица Crossbars заполнена")

        QUERY = """SELECT last_insert_rowid();"""
        cursor.execute(QUERY)
        crossbar_id = cursor.fetchone()[0]

        ##############################################################################

        # создание таблицы мемристор
        CREATE_TABLE_QUERY = '''CREATE TABLE IF NOT EXISTS Memristors (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    bl INTEGER NOT NULL,
                                    wl INTEGER NOT NULL,
                                    last_resistance INTEGER NOT NULL,
                                    crossbar_id INTEGER NOT NULL,
                                    FOREIGN KEY (crossbar_id) REFERENCES Crossbars(id) 
                                    ON DELETE CASCADE
                                    );'''

        cursor.execute(CREATE_TABLE_QUERY) # выполнить запрос в базу данных
        connection.commit() # сохранить изменение
        print("Таблица Memristors создана")

        # заполнение таблицы мемристоры
        for i in range(bl_num):
            for j in range(wl_num):
                bl = i
                wl = j
                last_resistance = 0
                INSERT_QUERY = """INSERT INTO Memristors (bl, wl, last_resistance, crossbar_id) VALUES (?,?,?,?);"""
                cursor.execute(INSERT_QUERY, (bl, wl, last_resistance, crossbar_id))
                connection.commit() # сохранить изменение
        print("Таблица Memristors заполнена")

        ##############################################################################

        # создание таблицы эксперименты
        CREATE_TABLE_QUERY = '''CREATE TABLE IF NOT EXISTS Experiments (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    datestamp TEXT NOT NULL,
                                    name TEXT NOT NULL,
                                    image BLOB,
                                    status INTEGER NOT NULL,
                                    memristor_id INTEGER NOT NULL,
                                    last_resistance INTEGER,
                                    FOREIGN KEY (memristor_id) REFERENCES Memristors(id) 
                                    ON DELETE CASCADE
                                    );'''

        cursor.execute(CREATE_TABLE_QUERY) # выполнить запрос в базу данных
        connection.commit() # сохранить изменение
        print("Таблица Experiments создана")

        ##############################################################################

        # создание таблицы тикеты
        CREATE_TABLE_QUERY = '''CREATE TABLE IF NOT EXISTS Tickets (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    datestamp TEXT NOT NULL,
                                    ticket_name TEXT NOT NULL,
                                    ticket BLOB NOT NULL,
                                    result TEXT,
                                    status INTEGER NOT NULL,
                                    experiment_id INTEGER NOT NULL,
                                    FOREIGN KEY (experiment_id) REFERENCES Experiments(id) 
                                    ON DELETE CASCADE
                                    );'''

        cursor.execute(CREATE_TABLE_QUERY) # выполнить запрос в базу данных
        connection.commit() # сохранить изменение
        print("Таблица Tickets создана")

        status = True
    except sqlite3.Error as error: # можно обработать любую ошибку и исключение
        print("Ошибка при подключении к sqlite", error)
    finally:
        if connection:
            connection.close() # закрываем соединение
            print("Соединение с SQLite закрыто")

    return status, crossbar_id
