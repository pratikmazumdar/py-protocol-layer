import json
from pymongo import MongoClient, GEOSPHERE, TEXT

from main.config import get_config_by_name
from main.logger.custom_logging import log

mongo_client = None
mongo_db = None


class JsonObject:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


def initialize_before_calls(app):
    from flask import request, g

    @app.before_request
    def set_page(page=1):
        page = int(request.args.get('page', 1))
        g.page = page


def init_database():
    global mongo_client, mongo_db
    if mongo_client is not None and mongo_db is not None:
        return
    database_host = get_config_by_name('MONGO_DATABASE_HOST')
    database_port = get_config_by_name('MONGO_DATABASE_PORT')
    database_name = get_config_by_name('MONGO_DATABASE_NAME')
    mongo_client = MongoClient(database_host, database_port, maxPoolSize=10)
    mongo_db = mongo_client[database_name]
    log(f"Connection to mongodb://{database_host}:{database_port} is successful!")
    create_all_indexes()
    log(f"Created indexes if not already present!")


def create_all_indexes():
    [create_ttl_index(c) for c in ["on_select", "on_init", "on_confirm", "on_cancel", "on_status", "on_support",
                                   "on_track", "on_update", "on_rating"]]
    [create_ttl_index(c, ttl_in_seconds=24*60*60) for c in ["on_search_dump", "request_dump", "on_search_items",
                                                            "provider", "custom_menu", "location", "product",
                                                            "product_attribute", "product_attribute_value",
                                                            "variant_group", "customisation_group"
                                                            ]]
    get_mongo_collection("on_search_items").create_index([('id', TEXT)], name='id_index')
    get_mongo_collection("location").create_index([("gps", GEOSPHERE)])


def create_ttl_index(collection_name, ttl_in_seconds=None):
    # check if index already exists
    if "created_at_ttl" in get_mongo_collection(collection_name).index_information():
        return
    ttl_in_seconds = ttl_in_seconds if ttl_in_seconds else get_config_by_name('TTL_IN_SECONDS')
    get_mongo_collection(collection_name).create_index("created_at", name="created_at_ttl",
                                                       expireAfterSeconds=ttl_in_seconds)


def get_mongo_collection(collection_name):
    # check if database is initialized
    global mongo_client, mongo_db
    if mongo_client is None or mongo_db is None:
        init_database()
    return mongo_db[collection_name]
