import unittest
import os
import sqlite3
from flask import Flask
from app import init_db


class TestDatabaseInit(unittest.TestCase):

    def setUp(self):
        self.db_path = './db/webtoons_test.db'

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        init_db()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comics';")
        table_exists = cursor.fetchone() is not None
        conn.close()
        self.assertTrue(table_exists)


if __name__ == '__main__':
    unittest.main()
