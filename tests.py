import unittest
from pymongo import MongoClient
import app
from app import create_new_id

class TestApp(unittest.TestCase):

    def setUp(self):
        self.db = MongoClient("52.17.26.163")['testtest']
        app.set_db(self.db)

    def test_create_new_id(self):
        counter = self.db['counters'].find_one({"id":"testid"})
        self.assertEquals(counter['seq'], 1)

    def tearDown(self):
        self.db.drop_collection('counters')

if __name__ == '__main__':
    unittest.main()