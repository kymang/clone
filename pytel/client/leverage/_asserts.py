# pytel < https://t.me/kastaid >
# Copyright (C) 2023-present kastaid
#
# This file is a part of < https://github.com/kastaid/pytel/ >
# Please read the GNU Affero General Public License in
# < https://github.com/kastaid/pytel/blob/main/LICENSE/ >.

from asyncio import sleep
from contextlib import suppress
from inspect import getfullargspec
from re import findall
from typing import Optional, Union
from pyrogram.enums import (
    MessageEntityType,)
from pyrogram.types import Message


async def _try_purged(
    message,
    timer: Union[int, float] = None,
):
    with suppress(BaseException):
        if timer:
            await sleep(timer)
            await message.delete()
        else:
            await message.delete()


async def eor(
    message: Message,
    **kwargs,
) -> Message:
    functions = (
        (
            message.edit_text
            if message.from_user.is_self
            else message.reply
        )
        if message.from_user
        else message.reply
    )
    insc = getfullargspec(
        functions.__wrapped__
    ).args
    return await functions(
        **{
            _: value
            for _, value in kwargs.items()
            if _ in insc
        }
    )


def get_text(
    message: Message,
    save_link: Optional[bool] = None,
) -> Optional[str]:
    text_ = (
        message.text.split(None, 1)[1]
        if len(
            message.command,
        )
        != 1
        else None
    )
    if message.reply_to_message:
        text_ = (
            message.reply_to_message.text
            or message.reply_to_message.caption
            or message.reply_to_message.caption_entities
        )

    if text_ is None:
        return False
    else:
        if save_link:
            # find link
            link = findall(
                "http[s]?://(?:[ a-zA-Z]|[0-9]|[$-_@.&+]|(?: %[0-9a-fA-F][0-9a-fA-F]))+",
                text_,
            )
            for x in link:
                return str(x)
        else:
            return str(text_.lower())


def replied(
    message: Message,
):
    reply_id = None

    if message.reply_to_message:
        reply_id = (
            message.reply_to_message.id
        )

    elif not message.from_user.is_self:
        reply_id = message.id

    return reply_id


def attr_file(
    message: Message,
):
    if message.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "contact",
            "dice",
            "poll",
            "location",
            "venue",
            "sticker",
        ):
            obj = getattr(
                message,
                message_type,
            )
            if obj:
                setattr(
                    obj,
                    "message_type",
                    message_type,
                )
                return obj


async def extract_userid(
    client, message, text: str
):
    def is_int(text: str):
        try:
            int(text)
        except ValueError:
            return False
        return True

    text = text.strip()

    if is_int(text):
        return int(text)

    entities = message.entities
    if len(entities) < 2:
        return (
            await client.get_users(text)
        ).id
    entity = entities[1]
    if (
        entity.type
        == MessageEntityType.MENTION
    ):
        return (
            await client.get_users(text)
        ).id
    if (
        entity.type
        == MessageEntityType.TEXT_MENTION
    ):
        return entity.user.id
    return None


async def user_and_reason(
    client, message, sender_chat=False
):
    args, text = (
        message.text.strip().split(),
        message.text,
    )
    user, reason = None, None
    if message.reply_to_message:
        reply = message.reply_to_message
        # reply to a message and no reason
        if not reply.from_user:
            if (
                reply.sender_chat
                and reply.sender_chat
                != message.chat.id
                and sender_chat
            ):
                id_ = (
                    reply.sender_chat.id
                )
            else:
                return None, None
        else:
            id_ = reply.from_user.id

        if len(args) < 2:
            reason = None
        else:
            reason = text.split(
                None, 1
            )[1]
        return id_, reason

    # not reply and not reason
    if len(args) == 2:
        user = text.split(None, 1)[1]
        return (
            await extract_userid(
                client, message, user
            ),
            None,
        )

    # not reply and reason
    if len(args) > 2:
        user, reason = text.split(
            None, 2
        )[1:]
        return (
            await extract_userid(
                client, message, user
            ),
            reason,
        )

    return user, reason


async def extract_user(client, message):
    return (
        await user_and_reason(
            client, message
        )
    )[0]
