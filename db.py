import pymongo


class Mongo:

    __client = pymongo.MongoClient("mongodb://localhost:27017/")

    def __init__(self, db_name="digitogame") -> None:
        self.db = self.__client[db_name]

    def change_db_name(self, db_name):
        self.db = self.__client[db_name]

    def set_collection(self, collection_name):
        return self.db[collection_name]

    def create_collection(self, collection_name):
        return self.db.create_collection(collection_name)

    def close(self):
        self.__client.close()
