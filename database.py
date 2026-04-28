from pymongo import DESCENDING, MongoClient
import config

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client

def get_mail_collection():
    client = _get_client()
    col = client[config.MONGODB_DB][config.MONGODB_MAILS_COLLECTION]
    col.create_index("mail_id", unique=True)
    return col

def get_task_collection():
    client = _get_client()
    col = client[config.MONGODB_DB][config.MONGODB_TASKS_COLLECTION]
    col.create_index("task_id", unique=True)
    col.create_index("id", unique=True)
    return col

def upsert_mail(mail_id, document):
    col = get_mail_collection()
    col.replace_one({"mail_id": mail_id}, document, upsert=True)

def upsert_task(task_id, document):
    col = get_task_collection()
    col.replace_one({"task_id": task_id}, document, upsert=True)

def fetch_tasks():
    col = get_task_collection()
    return list(col.find({}, {"_id": 0}).sort("received_at", DESCENDING))

def update_task(task_id, updates):
    col = get_task_collection()
    col.update_one(
        {"$or": [{"task_id": task_id}, {"id": task_id}]},
        {"$set": updates}
    )

def mail_exists(mail_id):
    col = get_mail_collection()
    return col.count_documents({"mail_id": mail_id}, limit=1) > 0