import hashlib
import logging
import os
import random
from typing import Any, IO, Literal, overload

import discord.ext.commands
import aiohttp
from discord.ext.commands import Context
import vt  # type: ignore[import-untyped]

from command_utils.vt_utils import ZipVTClient

logger = logging.getLogger('discord')


def bytes_to_human_readable(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 ** 2:
        return f"{size / 1024:.1f} KiB"
    if size < 1024 ** 3:
        return f"{size / 1024 ** 2:.1f} MiB"
    
    return f"{size / 1024 ** 3:.2f} GiB"


class VTInfo:
    def __init__(self, data: dict[str, Any]):
        attributes: dict[str, Any] = data['attributes']
        last_analysis_stats: dict[str, Any] = attributes['last_analysis_stats']
        self.sha256_hash: str = data['id']
        self.meaningful_name: str = attributes['meaningful_name']
        self.first_submission_date: int = attributes['first_submission_date']
        self.last_analysis_date: int = attributes['last_analysis_date']
        self.reputation: int = attributes['reputation']
        self.size: str = bytes_to_human_readable(attributes['size'])
        self.type_description: str = attributes['type_description']
        self.link: str = f"https://www.virustotal.com/gui/file/{data['id']}"
        self.malicious_detections: int = last_analysis_stats['malicious']
        self.suspicious_detections: int = last_analysis_stats['suspicious']
        self.maybe_detections: int = self.malicious_detections + self.suspicious_detections
        self.no_detections: int = last_analysis_stats['undetected'] + last_analysis_stats['harmless']
        self.total_AVs_run: int = self.malicious_detections + self.suspicious_detections + self.no_detections
        self.tags: list[str] = attributes['tags']
        
        self.low_reputation: bool = self.reputation < 0
        self.likely_malicious: bool = ((self.malicious_detections + self.suspicious_detections) >= 5)
        self.likely_malicious = self.likely_malicious or self.low_reputation
        
        self.threat_classification: str = 'Unknown'
        self.threat_label: str = 'Unknown'
        
        if attributes.get('popular_threat_classification', None) is not None:
            categories: list[dict] = attributes['popular_threat_classification']['popular_threat_category']
            categories = sorted(categories, key=lambda x: x['count'], reverse=True)
            self.threat_classification = categories[0]['value']
            self.threat_label = attributes['popular_threat_classification']['suggested_threat_label']


_session = aiohttp.ClientSession()


async def fetch_json(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[Any, Any]]:
    async with _session.get(url, headers=headers) as response:
        return response.status, await response.json()


def _get_vt_client() -> ZipVTClient:
    logger.debug('Creating new VT client.')
    api_key = os.getenv('VT_API_KEY')
    if api_key is None:
        raise ValueError('VT_API_KEY environment variable not set')
    
    return ZipVTClient(api_key)


async def get_nasa_apod() -> dict[str, str]:
    api_key = os.getenv('NASA_API_KEY')
    
    url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch data from NASA API: {status}')
    
    return data


async def get_dog_pic(ctx: Context) -> None:
    url = 'https://dog.ceo/api/breeds/image/random'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch dog picture: {status}')
    
    if 'message' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from dog API')
    
    await ctx.send(data['message'])


async def get_fox_pic(ctx: Context) -> None:
    urls = ['https://randomfox.ca/floof/', 'https://api.sefinek.net/api/v2/random/animal/fox']
    url = random.choice(urls)
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch fox picture: {status}')
    
    if 'image' in data:
        await ctx.send(data['image'])
        return
    
    if 'message' in data:
        await ctx.send(data['message'])
        return
    
    raise discord.ext.commands.CommandError('Unexpected response format from fox API')


async def get_cat_pic(ctx: Context) -> None:
    url = 'https://api.thecatapi.com/v1/images/search'
    
    api_key = os.getenv('CAT_API_KEY')
    if api_key is None:
        raise discord.ext.commands.CommandError('CAT_API_KEY environment variable not set')
    
    header: dict[str, str] = {'x-api-key': api_key, 'Content-Type': 'application/json'}
    status, data = await fetch_json(url, headers=header)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch cat picture: {status}')
    
    if not data or 'url' not in data[0]:
        raise discord.ext.commands.CommandError('Unexpected response format from cat API')
    
    await ctx.send(data[0]['url'])


async def get_insult(ctx: Context) -> None:
    url = 'https://evilinsult.com/generate_insult.php?lang=en&type=json'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch insult: {status}')
    
    if 'insult' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from insult API')
    
    await ctx.send(data['insult'])


async def get_advice(ctx: Context) -> None:
    url = 'https://api.adviceslip.com/advice'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch advice: {status}')
    
    if 'slip' not in data or 'advice' not in data['slip']:
        raise discord.ext.commands.CommandError('Unexpected response format from advice API')
    
    await ctx.send(data['slip']['advice'])


async def get_joke(ctx: Context) -> None:
    url = 'https://v2.jokeapi.dev/joke/Any?blacklistFlags=racist,sexist'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch joke: {status}')
    
    if 'joke' not in data and ('setup' not in data or 'delivery' not in data):
        raise discord.ext.commands.CommandError('Unexpected response format from joke API')
    
    # Two-part joke format
    if 'setup' in data and 'delivery' in data:
        to_send = f'{data['setup']}\n{data['delivery']}'
    
    elif 'joke' in data:
        # Single joke format
        to_send = data['joke']
    else:
        raise discord.ext.commands.CommandError('Unexpected joke format from joke API')
    
    await ctx.send(to_send)


async def get_wyr(ctx: Context) -> None:
    url = 'https://api.truthordarebot.xyz/api/wyr'
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch Would You Rather question: {status}')
    
    if 'question' not in data:
        raise discord.ext.commands.CommandError('Unexpected response format from Would You Rather API')
    
    await ctx.send(data['question'])


async def get_no(ctx: Context) -> None:
    url = "https://naas.isalman.dev/no"
    status, data = await fetch_json(url)
    
    if status != 200:
        raise discord.ext.commands.CommandError(f'Failed to fetch no: {status}')
    
    if "reason" not in data:
        raise discord.ext.commands.CommandError(f'Unexpected reason format from no API: {data}')
    
    await ctx.send(data["reason"])


def create_vt_embed(vt_info: VTInfo) -> discord.Embed:
    av_num = vt_info.total_AVs_run
    description: str = ''
    if vt_info.likely_malicious:
        colour = discord.Colour.red()
        title = 'This file is likely malicious'
        description += f'Generic malware category: {vt_info.threat_classification.title()}\n'
        description += f'Specific type: {vt_info.threat_label.capitalize()}\n'
    else:
        colour = discord.Colour.green()
        title = 'This file is likely not malicious'
    
    description += f'File type: {vt_info.type_description}\n'
    description += f'Reputation: {vt_info.reputation}\n'
    description += f'Meaningful name: {vt_info.meaningful_name}\n'
    description += f'Size: {vt_info.size}\n'
    description += f'First submission date: <t:{vt_info.first_submission_date}>\n'
    description += f'Last analysis date: <t:{vt_info.last_analysis_date}>\n'
    description += f'[Full VirusTotal report]({vt_info.link})'
    
    embed = discord.Embed(title=title, colour=colour, description=description)
    embed.add_field(name='Detections', value=f'{vt_info.malicious_detections}/{av_num} Security vendors flagged the file as malicious\n'
                                             f'{vt_info.suspicious_detections}/{av_num} Security vendors flagged the file as suspicious',
                    )
    embed.add_field(name='Tags', value=", ".join(vt_info.tags))
    return embed


def handle_vt_error(response: dict[str, Any], err: str) -> str:
    error = response.get("error")
    if error is None:
        logger.error(f'Error getting VT info, no error. Error: {err}, response: {response}')
        return "An unknown error has occurred."
    
    if error.get("code") == "NotFoundError":
        return "File has not been scanned yet"
    if error.get("code") == "QuotaExceededError":
        return "API usage quota exceeded. Please try again later."
    
    logger.error(f'Error getting VT info, unknown. Error: {err}, response: {response}')
    return error.get("message", "An unknown error has occurred.")


@overload
async def get_vt_hash_info(given_hash: str, return_err: Literal[False] = False, client: Any = None) -> VTInfo | str:
    ...


@overload
async def get_vt_hash_info(given_hash: str, return_err: Literal[True], client: Any = None) -> VTInfo | dict[str, Any]:
    ...


async def get_vt_hash_info(
        given_hash: str,
        return_err: bool = False,
        client: vt.Client | None = None,
        ) -> VTInfo | str | dict[str, Any]:
    
    logger.debug(f'Getting VT info for hash: {given_hash}')
    if client is None:
        async with _get_vt_client() as client:
            response: dict[str, Any] = await (await client.get_async('/files/' + given_hash)).json_async()
            
    else:
        logger.debug('Using existing VT client for hash_info')
        response = await (await client.get_async('/files/' + given_hash)).json_async()
        
    logger.debug(f'VT response for hash_info: {response}')
    try:
        return VTInfo(response['data'])
    except KeyError as e:
        if return_err:
            return response
        return handle_vt_error(response, f'{e}')


async def upload_file_vt(f: IO[bytes], zip_password: str | None = None) -> VTInfo | str:
    hasher = hashlib.sha256()
    logger.debug(f'Uploading file to VT: {f.name}')
    while chunk := f.read(65535):
        hasher.update(chunk)
    
    sha256_hash = hasher.hexdigest()
    logger.debug(f'SHA256 hash of file: {sha256_hash}')
    async with _get_vt_client() as client:
        resp = await get_vt_hash_info(sha256_hash, return_err=True, client=client)
        if isinstance(resp, VTInfo):
            return resp
        
        if resp.get("error", {}).get("code") == "QuotaExceededError":
            return "API usage quota exceeded. Please try again later."
        
        if not resp.get("error", {}).get("code") == "NotFoundError":
            return "An unknown error has occurred."
        
        await client.scan_file_async(f, wait_for_completion=True, zip_password=zip_password)
        
        return await get_vt_hash_info(sha256_hash, client=client)
