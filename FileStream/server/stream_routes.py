# ---------------------------------------------------
# File Name: Stream_Routes.py
# Author: NeonAnurag
# GitHub: https://github.com/MyselfNeon/
# Telegram: https://t.me/MyelfNeon
# Created: 2025-11-21
# Last Modified: 2025-11-22
# Version: Latest
# License: MIT License
# ---------------------------------------------------

import time
import math
import logging
import mimetypes
import traceback
import jinja2
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from FileStream.bot import multi_clients, work_loads, FileStream
from FileStream.config import Telegram, Server
from FileStream.server.exceptions import FIleNotFound, InvalidHash
from FileStream import utils, StartTime, __version__
from FileStream.utils.database import Database
from FileStream.utils.render_template import render_page

# Routes
routes = web.RouteTableDef()
db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)

VERIFY_ERROR_LINK_USED = "link_used"
VERIFY_ERROR_WRONG_STEP = "wrong_step"
VERIFY_ERROR_INVALID_TOKEN = "invalid_token"


def _render_verify_template(state, message, redirect_url=None, delay_seconds=5):
    with open("FileStream/template/verify.html") as template_file:
        template = jinja2.Template(template_file.read())

    return web.Response(
        text=template.render(
            state=state,
            message=message,
            redirect_url=redirect_url,
            delay_seconds=delay_seconds,
        ),
        content_type="text/html",
    )


def _build_callback_url(request, code):
    return str(request.url.with_path(f"/verify/complete/{code}").with_query({}))


def _build_shortner_url(session, _callback_url):
    return (
        session.get("shortner_url")
        or session.get("shortener_url")
        or session.get("short_url")
        or session.get("url")
    )


async def _verify_session_error(session, request):
    if not session:
        return VERIFY_ERROR_INVALID_TOKEN

    now = int(time.time())
    if session.get("used"):
        return VERIFY_ERROR_LINK_USED

    if int(session.get("expires_at", 0) or 0) <= now:
        return VERIFY_ERROR_INVALID_TOKEN

    required_uid = int(session.get("user_id", 0) or 0)
    provided_uid = request.query.get("uid")
    if required_uid:
        if not provided_uid:
            return VERIFY_ERROR_INVALID_TOKEN

        try:
            if int(provided_uid) != required_uid:
                return VERIFY_ERROR_INVALID_TOKEN
        except ValueError:
            return VERIFY_ERROR_INVALID_TOKEN

    current_step = int(session.get("step", 1) or 1)
    previous_code = session.get("previous_code")
    if current_step > 1 and previous_code:
        previous_session = await db.get_verification_session(previous_code)
        if not previous_session or not previous_session.get("used"):
            return VERIFY_ERROR_WRONG_STEP

    return None


# Status Route
@routes.get("/", allow_head=True)
@routes.get("/status", allow_head=True)
async def root_route_handler(_):
    return web.json_response(
        {
            "server_status": "running",
            "uptime": utils.get_readable_time(time.time() - StartTime),
            "telegram_bot": "@" + FileStream.username,
            "connected_bots": len(multi_clients),
            "loads": dict(
                ("bot" + str(c + 1), l)
                for c, (_, l) in enumerate(
                    sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
                )
            ),
            "version": __version__,
        }
    )


@routes.get("/verify/{code}", allow_head=True)
async def verify_route_handler(request: web.Request):
    code = request.match_info["code"]
    session = await db.get_verification_session(code)
    error_state = await _verify_session_error(session, request)

    if error_state == VERIFY_ERROR_LINK_USED:
        return _render_verify_template("error", "This verification link has already been used.")

    if error_state == VERIFY_ERROR_WRONG_STEP:
        return _render_verify_template("error", "Wrong step order. Please complete the previous step first.")

    if error_state == VERIFY_ERROR_INVALID_TOKEN:
        return _render_verify_template("error", "This verification token is invalid or has expired.")

    callback_url = _build_callback_url(request, code)
    shortner_url = _build_shortner_url(session, callback_url)

    if not shortner_url:
        return _render_verify_template("error", "This verification token is invalid or has expired.")

    return _render_verify_template(
        state="loading",
        message="Verification accepted. Redirecting to shortner in 5 seconds...",
        redirect_url=shortner_url,
        delay_seconds=5,
    )


@routes.get("/verify/complete/{code}", allow_head=True)
async def verify_complete_route_handler(request: web.Request):
    code = request.match_info["code"]
    session = await db.get_verification_session(code)

    if not session:
        return _render_verify_template("error", "This verification token is invalid or has expired.")

    if session.get("used"):
        return _render_verify_template("success", "Verification already completed. Reward was not duplicated.")

    completed_session = await db.complete_verification_by_code(code)
    if completed_session:
        reward_type = completed_session.get("reward_type")
        reward_value = completed_session.get("reward_value")

        if reward_type == "tokens":
            await db.grant_50_tokens(completed_session.get("user_id"))
        elif reward_type == "free_access_hours":
            await db.grant_24h_access(completed_session.get("user_id"), access_type="free")

        return _render_verify_template("success", "Verification completed successfully. Reward granted once.")

    refreshed_session = await db.get_verification_session(code)
    if refreshed_session and refreshed_session.get("used"):
        return _render_verify_template("success", "Verification already completed. Reward was not duplicated.")

    return _render_verify_template("error", "This verification token is invalid or has expired.")

# Watch Route
@routes.get("/watch/{path}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        return web.Response(text=await render_page(path), content_type='text/html')
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass

# Download Route
@routes.get("/dl/{path}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        return await media_streamer(request, path)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        pass
    except Exception as e:
        traceback.print_exc()
        logging.critical(e.with_traceback(None))
        logging.debug(traceback.format_exc())
        raise web.HTTPInternalServerError(text=str(e))

# Cache
class_cache = {}

# Media Streamer
async def media_streamer(request: web.Request, db_id: str):
    range_header = request.headers.get("Range", 0)

    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    if Telegram.MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.headers.get('X-FORWARDED-FOR', request.remote)}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logging.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logging.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = utils.ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect

    logging.debug("before calling get_file_properties")
    file_id = await tg_connect.get_file_properties(db_id, multi_clients)
    logging.debug("after calling get_file_properties")

    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)

    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )

    mime_type = file_id.mime_type
    file_name = utils.get_name(file_id)
    disposition = "attachment"

    if not mime_type:
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    # if "video/" in mime_type or "audio/" in mime_type:
    #     disposition = "inline"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            "Content-Disposition": f'{disposition}; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        },
        )


# MyselfNeon
# Don't Remove Credit 🥺
# Telegram Channel @NeonFiles
