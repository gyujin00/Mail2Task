from __future__ import annotations

from pymongo import DESCENDING, MongoClient

from core import config


_client = None


def _get_client():
    """Share one Mongo client across CLI and web requests."""
    global _client
    if _client is None:
        _client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_mail_collection():
    """Return the `mails` collection and ensure its lookup index exists."""
    client = _get_client()
    collection = client[config.MONGODB_DB][config.MONGODB_MAILS_COLLECTION]
    collection.create_index("mail_id", unique=True)
    return collection


def get_task_collection():
    """Return the `tasks` collection used by the list, detail, and stats views."""
    client = _get_client()
    collection = client[config.MONGODB_DB][config.MONGODB_TASKS_COLLECTION]
    collection.create_index("task_id", unique=True)
    collection.create_index("id", unique=True)
    return collection


def get_pdf_collection():
    """Return the `pdf_documents` collection used for related-PDF lookups."""
    client = _get_client()
    collection = client[config.MONGODB_DB][config.MONGODB_PDFS_COLLECTION]
    collection.create_index("pdf_id", unique=True)
    collection.create_index("mail_id")
    return collection


def upsert_mail(mail_id, document):
    """Insert or replace a mail document by `mail_id`."""
    get_mail_collection().replace_one({"mail_id": mail_id}, document, upsert=True)


def upsert_task(task_id, document):
    """Insert or replace a task document by `task_id`."""
    get_task_collection().replace_one({"task_id": task_id}, document, upsert=True)


def upsert_pdf(pdf_id, document):
    """Insert or replace a PDF document by `pdf_id`."""
    get_pdf_collection().replace_one({"pdf_id": pdf_id}, document, upsert=True)


def fetch_tasks():
    """Return tasks sorted by most recent receipt time."""
    return list(get_task_collection().find({}, {"_id": 0}).sort("received_at", DESCENDING))


def fetch_task(task_id: str):
    """Fetch a single task by either the legacy or current identifier."""
    return get_task_collection().find_one(_task_lookup_filter(task_id), {"_id": 0})


def fetch_mail(mail_id: str):
    """Fetch a single source mail document for the detail page."""
    return get_mail_collection().find_one({"mail_id": mail_id}, {"_id": 0})


def fetch_pdf(pdf_id: str):
    """Fetch a single stored PDF document."""
    return get_pdf_collection().find_one({"pdf_id": pdf_id}, {"_id": 0})


def fetch_pdfs_by_mail(mail_id: str):
    """Fetch all stored PDF documents that belong to one mail."""
    return list(get_pdf_collection().find({"mail_id": mail_id}, {"_id": 0}))


def fetch_pdfs(exclude_pdf_ids=None, limit: int = 200):
    """Fetch stored PDF documents, optionally excluding a subset by id."""
    query = {}
    if exclude_pdf_ids:
        query["pdf_id"] = {"$nin": list(exclude_pdf_ids)}
    return list(get_pdf_collection().find(query, {"_id": 0}).limit(limit))


def update_task(task_id, updates):
    """Apply partial updates to a task document."""
    get_task_collection().update_one(
        _task_lookup_filter(task_id),
        {"$set": updates},
    )


def mail_exists(mail_id):
    """Check whether a mail document already exists by `mail_id`."""
    return get_mail_collection().count_documents({"mail_id": mail_id}, limit=1) > 0


def _task_lookup_filter(task_id: str) -> dict:
    """Keep task lookups consistent for both `task_id` and legacy `id`."""
    return {"$or": [{"task_id": task_id}, {"id": task_id}]}
