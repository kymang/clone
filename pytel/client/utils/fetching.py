# pytel < https://t.me/kastaid >
# Copyright (C) 2023-present kastaid
#
# This file is a part of < https://github.com/kastaid/pytel/ >
# PLease read the GNU Affero General Public License in
# < https://github.com/kastaid/pytel/blob/main/LICENSE/ >

import re
from asyncio import sleep
from base64 import b64decode
from io import BytesIO
from sys import version_info
from time import perf_counter
from typing import (
    Any,
    Optional,
    Set,
    Tuple,
    Union,
)
from uuid import uuid4
from aiofiles import open
from aiohttp import (
    ClientSession,
    __version__,
)
from asyncache import cached
from cachetools import TTLCache
from version import __version__ as versi


def get_random_hex(length: int = 12) -> str:
    return uuid4().hex[:length]


async def fetching(
    url: Optional[str],
    post: Optional[bool] = None,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
    ssl: Any = None,
    re_json: bool = False,
    re_content: bool = False,
    real: bool = False,
    statuses: Optional[Set[int]] = None,
    *args,
    **kwargs,
) -> Any:
    statuses = statuses or {}
    if not headers:
        headers = {
            "User-Agent": "Python/{}.{} aiohttp/{} pytel/{}".format(
                version_info[0],
                version_info[1],
                __version__,
                versi,
            )
        }
    async with ClientSession(
        headers=headers
    ) as session:
        try:
            if post:
                resp = await session.post(
                    url=url,
                    json=json,
                    data=data,
                    ssl=ssl,
                    raise_for_status=False,
                    *args,
                    **kwargs,
                )
            else:
                resp = await session.get(
                    url=url,
                    params=params,
                    ssl=ssl,
                    raise_for_status=False,
                    *args,
                    **kwargs,
                )
        except BaseException:
            return None
        if resp.status not in {
            *{200, 201},
            *statuses,
        }:
            return None
        if re_json:
            return await resp.json(
                content_type=None
            )
        if re_content:
            return await resp.read()
        if real:
            return resp
        return await resp.text()


@cached(
    TTLCache(
        maxsize=1024,
        ttl=(120 * 30),
        timer=perf_counter,
    )
)  # 1 hours
async def get_blacklisted(
    url: str,
    is_json: bool = False,
    attempts: int = 3,
    fallbacks: Optional[
        Tuple[Union[int, str]]
    ] = None,
) -> Set[Union[int, str]]:
    count = 0
    is_content = not is_json
    while count < attempts:
        res = await fetching(
            url,
            re_json=is_json,
            re_content=is_content,
        )
        count += 1
        if not res:
            if count != attempts:
                await sleep(1)
                continue
            ids = fallbacks or []
            break
        if is_content:
            reg = r"[^\s#,\[\]\{\}]+"
            data = re.findall(
                reg, res.decode("utf-8")
            )
            ids = [
                int(x)
                for x in data
                if x.isdecimal()
                or (
                    x.startswith("-")
                    and x[1:].isdecimal()
                )
            ]
        else:
            ids = list(res)
        break
    return set(ids)


async def screenshots(
    url: Optional[str],
    file_name: Optional[
        str
    ] = "web-screenshot",
    download: Optional[bool] = False,
) -> Any:
    payload = {
        "url": url,
        "width": 1920,
        "height": 1080,
        "scale": 1,
        "format": "jpeg",
    }
    response = await fetching(
        url="https://webscreenshot.vercel.app/api",
        post=True,
        data=payload,
        re_json=True,
    )
    if not response:
        return None
    getpic = response["image"].replace(
        "data:image/jpeg;base64,", ""
    )
    file_name = f"{file_name}.jpg"
    if not download:
        file = BytesIO(b64decode(getpic))
        file.name = file_name
    else:
        file = "cache/" + file_name
        async with open(
            file, mode="wb"
        ) as f:
            await f.write(response)

    return file


async def fetch_adzan(
    str_city: Optional[str],
) -> Optional[str]:
    url = f"https://muslimsalat.p.rapidapi.com/{str_city}.json"
    headers = {
        "X-RapidAPI-Key": "562b8598f6msh56e1ad721a549c9p125ff9jsn70e8572dc418",
        "X-RapidAPI-Host": "muslimsalat.p.rapidapi.com",
    }
    response = await fetching(
        url, re_json=True, headers=headers
    )
    if not response:
        text = "{}!".format(
            "Try again later.",
        )
        return text
    if response["status_code"] == 0:
        text = (
            "{}".format(
                "Cannot retrieve adhan data for",
            )
            + f"<u>{str_city}</u>, "
            + "{}".format(
                "please check again.",
            )
        )
    else:
        timefor = f"""
<u>{response['query']}, {response['country']}, {response['items'][0]['date_for']}.</u>
"""
        cordinates = f"{response['latitude'] or ''},{response['longitude'] or ''}"
        maps = f"https://www.google.com/maps?q={cordinates}"
        celci = (
            f"{response['today_weather']['temperature']}"
            if response["today_weather"][
                "temperature"
            ]
            else 0
        )
        temperature = (
            "N/A"
            if celci == 0
            else f"{str(celci)}°C | {str(fahrenheit(celci))}°F"
        )
        text = (
            "<b>"
            + "{}".format(
                "Islamic Prayer Times",
            )
            + "</b>\n"
        )
        text += f"{timefor}├ <b>Fajr :</b> <code>{response['items'][0]['fajr']}</code>\n"
        text += f"├ <b>Shurooq :</b> <code>{response['items'][0]['shurooq']}</code>\n"
        text += f"├ <b>Dhuhr :</b> <code>{response['items'][0]['dhuhr']}</code>\n"
        text += f"├ <b>Asr :</b> <code>{response['items'][0]['asr']}</code>\n"
        text += f"├ <b>Maghrib :</b> <code>{response['items'][0]['maghrib']}</code>\n"
        text += f"└ <b>Isha :</b> <code>{response['items'][0]['isha']}</code>\n\n"
        text += (
            "<u>"
            + "{}".format(
                "Additional",
            )
            + "</u>\n"
        )
        text += (
            "├ <b>"
            + "{}".format("Code Country")
            + f" :</b> <code>{response['country_code']}</code>\n"
        )
        text += (
            "├ <b>"
            + "{}".format(
                "Temperature",
            )
            + f" :</b> <code>{temperature}</code>\n"
        )
        text += (
            "├ <b>"
            + "{}".format(
                "Cordinates",
            )
            + f" :</b> <code>{cordinates}</code>\n"
        )
        text += f"└ <b>Maps :</b> <code>{maps}</code>"

    return str(text)


def fahrenheit(
    celci: Optional[int],
) -> Optional[str]:
    """Convert celcius to farenheit"""
    temperature = (
        int(celci) * float(1.8)
    ) + 32
    temperat: str = f"{temperature}"
    temp = temperat.split(".")
    return temp[0]


def celcius(
    farenh: Optional[int],
) -> Optional[str]:
    """Convert farenheit to celcius"""
    temperature = (
        int(farenh) - 32
    ) / float(1.8)
    temperat: str = f"{temperature}"
    temp = temperat.split(".")
    return temp[0]