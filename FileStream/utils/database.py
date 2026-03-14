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


# MyselfNeon
# Don't Remove Credit 🥺
# Telegram Channel @NeonFiles
