# ---------------------------------------------------
# File Name: Database.py
# Author: NeonAnurag
# GitHub: https://github.com/MyselfNeon/
# Telegram: https://t.me/MyelfNeon
# Created: 2025-11-21
# Last Modified: 2025-11-22
# Version: Latest
# License: MIT License
# ---------------------------------------------------

import pymongo
import secrets
import time
import motor.motor_asyncio
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from FileStream.server.exceptions import FIleNotFound

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.black = self.db.blacklist
        self.file = self.db.file
        self.user_access = self.db.user_access
        self.verify_sessions = self.db.verify_sessions
        self.referrals = self.db.referrals
        self.coupons = self.db.coupons
        self.coupon_redemptions = self.db.coupon_redemptions
        self.video_submissions = self.db.video_submissions
        self.catalog_cache = self.db.catalog_cache
        self.user_states = self.db.user_states
        self._indexes_initialized = False

    async def ensure_indexes(self):
        if self._indexes_initialized:
            return

        await self.coupons.create_index("code", unique=True)
        await self.verify_sessions.create_index("one_time_code", unique=True)
        await self.coupon_redemptions.create_index(
            [("code", pymongo.ASCENDING), ("user_id", pymongo.ASCENDING)],
            unique=True,
        )
        await self.referrals.create_index("invited_id", unique=True)
        await self.catalog_cache.create_index("channel_id", unique=True)
        await self.video_submissions.create_index("submission_id", unique=True)
        await self.user_states.create_index("user_id", unique=True)
        self._indexes_initialized = True

    # Accepts name and username
    def new_user(self, id, name, username):
        return dict(
            id=id,
            name=name,
            username=username,
            join_date=time.time(),
            Links=0
        )

    # Passes name and username to creation
    async def add_user(self, id, name, username):
        user = self.new_user(id, name, username)
        await self.col.insert_one(user)

    # Essential for bot_utils to check existence
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return True if user else False

    # Updates name/username if the user already exists (Self-Healing)
    async def update_user_info(self, id, name, username):
        await self.col.update_one(
            {'id': int(id)},
            {'$set': {'name': name, 'username': username}}
        )

    async def get_user(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    def black_user(self, id):
        return dict(
            id=id,
            ban_date=time.time()
        )

    async def ban_user(self, id):
        user = self.black_user(id)
        await self.black.insert_one(user)

    async def unban_user(self, id):
        await self.black.delete_one({'id': int(id)})

    async def is_user_banned(self, id):
        user = await self.black.find_one({'id': int(id)})
        return True if user else False

    async def total_banned_users_count(self):
        count = await self.black.count_documents({})
        return count

    async def add_file(self, file_info):
        file_info["time"] = time.time()
        fetch_old = await self.get_file_by_fileuniqueid(file_info["user_id"], file_info["file_unique_id"])
        if fetch_old:
            return fetch_old["_id"]
        await self.count_links(file_info["user_id"], "+")
        return (await self.file.insert_one(file_info)).inserted_id

    async def find_files(self, user_id, range):
        user_files = self.file.find({"user_id": user_id})
        user_files.skip(range[0] - 1)
        user_files.limit(range[1] - range[0] + 1)
        user_files.sort('_id', pymongo.DESCENDING)
        total_files = await self.file.count_documents({"user_id": user_id})
        return user_files, total_files

    async def get_file(self, _id):
        try:
            file_info = await self.file.find_one({"_id": ObjectId(_id)})
            if not file_info:
                raise FIleNotFound
            return file_info
        except InvalidId:
            raise FIleNotFound

    async def get_file_by_fileuniqueid(self, id, file_unique_id, many=False):
        if many:
            return self.file.find({"file_unique_id": file_unique_id})
        else:
            file_info = await self.file.find_one({"user_id": id, "file_unique_id": file_unique_id})
        if file_info:
            return file_info
        return False

    async def total_files(self, id=None):
        if id:
            return await self.file.count_documents({"user_id": id})
        return await self.file.count_documents({})

    async def delete_one_file(self, _id):
        await self.file.delete_one({'_id': ObjectId(_id)})

    async def update_file_ids(self, _id, file_ids: dict):
        await self.file.update_one({"_id": ObjectId(_id)}, {"$set": {"file_ids": file_ids}})

    async def count_links(self, id, operation: str):
        if operation == "-":
            await self.col.update_one({"id": id}, {"$inc": {"Links": -1}})
        elif operation == "+":
            await self.col.update_one({"id": id}, {"$inc": {"Links": 1}})



    async def get_catalog_file_ids(self, channel_id, max_age_seconds=900):
        await self.ensure_indexes()
        cached = await self.catalog_cache.find_one({"channel_id": int(channel_id)})
        if not cached:
            return []

        updated_at = int(cached.get("updated_at", 0))
        now = int(time.time())
        if updated_at + int(max_age_seconds) < now:
            return []

        return list(cached.get("file_ids", []))

    async def set_catalog_file_ids(self, channel_id, file_ids):
        await self.ensure_indexes()
        now = int(time.time())
        await self.catalog_cache.update_one(
            {"channel_id": int(channel_id)},
            {
                "$set": {
                    "file_ids": list(file_ids),
                    "updated_at": now,
                }
            },
            upsert=True,
        )

    async def get_random_video_files(self, limit=5):
        pipeline = [
            {
                "$match": {
                    "mime_type": {
                        "$regex": "^video/",
                        "$options": "i",
                    }
                }
            },
            {"$sample": {"size": int(limit)}},
            {
                "$project": {
                    "_id": 1,
                    "file_id": 1,
                    "file_name": 1,
                }
            },
        ]
        cursor = self.file.aggregate(pipeline)
        items = []
        async for row in cursor:
            items.append(row)
        return items

    async def consume_token(self, user_id, amount=1):
        await self.ensure_indexes()
        updated_access = await self.user_access.find_one_and_update(
            {"user_id": int(user_id), "tokens": {"$gte": amount}},
            {"$inc": {"tokens": -amount}},
            return_document=ReturnDocument.AFTER,
        )
        return updated_access

    async def grant_50_tokens(self, user_id):
        await self.ensure_indexes()
        return await self.user_access.find_one_and_update(
            {"user_id": int(user_id)},
            {
                "$setOnInsert": {
                    "free_access_until": 0,
                    "premium_until": 0,
                },
                "$inc": {"tokens": 50},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def grant_24h_access(self, user_id, access_type="free"):
        await self.ensure_indexes()
        field = "premium_until" if access_type == "premium" else "free_access_until"
        now = int(time.time())
        return await self.user_access.find_one_and_update(
            {"user_id": int(user_id)},
            [
                {
                    "$set": {
                        "tokens": {"$ifNull": ["$tokens", 0]},
                        "free_access_until": {"$ifNull": ["$free_access_until", 0]},
                        "premium_until": {"$ifNull": ["$premium_until", 0]},
                    }
                },
                {
                    "$set": {
                        field: {
                            "$add": [
                                {"$max": [f"${field}", now]},
                                24 * 60 * 60,
                            ]
                        }
                    }
                },
            ],
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )


    async def create_verification_session(
        self,
        user_id,
        shortener_url,
        *,
        step=1,
        previous_code=None,
        reward_type="tokens",
        reward_value=50,
        expires_in=3600,
    ):
        await self.ensure_indexes()
        now = int(time.time())
        one_time_code = secrets.token_urlsafe(8)
        session = {
            "one_time_code": one_time_code,
            "user_id": int(user_id),
            "shortner_url": shortener_url,
            "step": int(step),
            "used": False,
            "previous_code": previous_code,
            "reward_type": reward_type,
            "reward_value": reward_value,
            "created_at": now,
            "expires_at": now + int(expires_in),
        }
        await self.verify_sessions.insert_one(session)
        return session

    async def get_access_state(self, user_id):
        return await self.user_access.find_one({"user_id": int(user_id)})

    async def mark_verification_step_complete(self, user_id, step):
        await self.ensure_indexes()
        now = int(time.time())
        return await self.verify_sessions.find_one_and_update(
            {
                "user_id": int(user_id),
                "step": step,
                "used": {"$ne": True},
                "expires_at": {"$gt": now},
            },
            {
                "$set": {
                    "used": True,
                }
            },
            return_document=ReturnDocument.AFTER,
        )

    async def get_verification_session(self, one_time_code):
        await self.ensure_indexes()
        return await self.verify_sessions.find_one({"one_time_code": str(one_time_code)})

    async def complete_verification_by_code(self, one_time_code):
        await self.ensure_indexes()
        now = int(time.time())
        return await self.verify_sessions.find_one_and_update(
            {
                "one_time_code": str(one_time_code),
                "used": {"$ne": True},
                "expires_at": {"$gt": now},
            },
            {
                "$set": {
                    "used": True,
                    "completed_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )

    async def redeem_coupon_once_per_user(self, code, user_id):
        await self.ensure_indexes()
        now = int(time.time())
        coupon = await self.coupons.find_one(
            {
                "code": code,
                "active": True,
                "$or": [
                    {"expiry": {"$exists": False}},
                    {"expiry": None},
                    {"expiry": {"$gt": now}},
                ],
            }
        )
        if not coupon:
            return None

        try:
            await self.coupon_redemptions.insert_one(
                {
                    "code": code,
                    "user_id": int(user_id),
                    "redeemed_at": now,
                }
            )
        except DuplicateKeyError:
            return False

        reward_type = coupon.get("reward_type")
        reward_value = coupon.get("reward_value", 0)

        if reward_type == "tokens":
            await self.user_access.update_one(
                {"user_id": int(user_id)},
                {
                    "$setOnInsert": {
                        "free_access_until": 0,
                        "premium_until": 0,
                    },
                    "$inc": {"tokens": int(reward_value)},
                },
                upsert=True,
            )
        elif reward_type in {"free_access_hours", "premium_hours"}:
            access_type = "premium" if reward_type == "premium_hours" else "free"
            field = "premium_until" if access_type == "premium" else "free_access_until"
            await self.user_access.update_one(
                {"user_id": int(user_id)},
                [
                    {
                        "$set": {
                            "tokens": {"$ifNull": ["$tokens", 0]},
                            "free_access_until": {"$ifNull": ["$free_access_until", 0]},
                            "premium_until": {"$ifNull": ["$premium_until", 0]},
                        }
                    },
                    {
                        "$set": {
                            field: {
                                "$add": [
                                    {"$max": [f"${field}", now]},
                                    int(reward_value) * 60 * 60,
                                ]
                            }
                        }
                    },
                ],
                upsert=True,
            )

        return coupon


    async def set_user_state(self, user_id, state, payload=None):
        await self.ensure_indexes()
        document = {
            "user_id": int(user_id),
            "state": str(state),
            "payload": payload or {},
            "updated_at": int(time.time()),
        }
        await self.user_states.update_one(
            {"user_id": int(user_id)},
            {"$set": document},
            upsert=True,
        )

    async def get_user_state(self, user_id):
        await self.ensure_indexes()
        return await self.user_states.find_one({"user_id": int(user_id)})

    async def clear_user_state(self, user_id):
        await self.ensure_indexes()
        await self.user_states.delete_one({"user_id": int(user_id)})

    async def create_video_submission(self, user_id, media_message, note=None):
        await self.ensure_indexes()
        now = int(time.time())
        submission_id = secrets.token_hex(6)
        document = {
            "submission_id": submission_id,
            "user_id": int(user_id),
            "chat_id": int(media_message.chat.id),
            "message_id": int(media_message.id),
            "status": "pending",
            "note": note or "",
            "created_at": now,
            "reviewed_at": None,
            "reviewed_by": None,
        }
        await self.video_submissions.insert_one(document)
        return document

    async def get_video_submission(self, submission_id):
        await self.ensure_indexes()
        return await self.video_submissions.find_one({"submission_id": str(submission_id)})

    async def approve_video_submission(self, submission_id, admin_id):
        await self.ensure_indexes()
        return await self.video_submissions.find_one_and_update(
            {"submission_id": str(submission_id), "status": "pending"},
            {"$set": {"status": "approved", "reviewed_by": int(admin_id), "reviewed_at": int(time.time())}},
            return_document=ReturnDocument.AFTER,
        )

    async def create_coupon(self, code, reward_type, reward_value, expiry=None):
        await self.ensure_indexes()
        now = int(time.time())
        document = {
            "code": str(code).upper(),
            "reward_type": str(reward_type),
            "reward_value": int(reward_value),
            "active": True,
            "expiry": int(expiry) if expiry else None,
            "created_at": now,
        }
        await self.coupons.update_one({"code": document["code"]}, {"$set": document}, upsert=True)
        return document

    async def deactivate_coupon(self, code):
        await self.ensure_indexes()
        return await self.coupons.find_one_and_update(
            {"code": str(code).upper(), "active": True},
            {"$set": {"active": False, "deactivated_at": int(time.time())}},
            return_document=ReturnDocument.AFTER,
        )

    async def get_coupon(self, code):
        await self.ensure_indexes()
        return await self.coupons.find_one({"code": str(code).upper()})

    async def ensure_referral_reward(self, inviter_id, invited_id, reward_tokens):
        await self.ensure_indexes()
        now = int(time.time())
        ref = await self.referrals.find_one({"invited_id": int(invited_id)})
        if ref:
            return None

        try:
            await self.referrals.insert_one({
                "inviter_id": int(inviter_id),
                "invited_id": int(invited_id),
                "reward_tokens": int(reward_tokens),
                "rewarded_at": now,
            })
        except DuplicateKeyError:
            return None

        access = await self.user_access.find_one_and_update(
            {"user_id": int(inviter_id)},
            {
                "$setOnInsert": {"free_access_until": 0, "premium_until": 0},
                "$inc": {"tokens": int(reward_tokens)},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return access

    async def grant_premium_hours(self, user_id, hours):
        await self.ensure_indexes()
        now = int(time.time())
        return await self.user_access.find_one_and_update(
            {"user_id": int(user_id)},
            [
                {"$set": {"tokens": {"$ifNull": ["$tokens", 0]}, "free_access_until": {"$ifNull": ["$free_access_until", 0]}, "premium_until": {"$ifNull": ["$premium_until", 0]}}},
                {"$set": {"premium_until": {"$add": [{"$max": ["$premium_until", now]}, int(hours) * 60 * 60]}}},
            ],
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def revoke_premium(self, user_id):
        await self.ensure_indexes()
        return await self.user_access.find_one_and_update(
            {"user_id": int(user_id)},
            {"$set": {"premium_until": 0}, "$setOnInsert": {"tokens": 0, "free_access_until": 0}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )


# MyselfNeon
# Don't Remove Credit 🥺
# Telegram Channel @NeonFiles
