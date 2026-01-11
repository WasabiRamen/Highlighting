# secrets_manager/tools/mk.py
# master key utilities

import json
from dataclasses import dataclass

import aiofiles


@dataclass(frozen=True)
class MasterKey:
    version: int
    key: bytes

    @classmethod
    async def load(cls, file_path: str) -> "MasterKey":
        async with aiofiles.open(file_path, mode="r") as f:
            content = await f.read()

        data = json.loads(content)
        return cls(version=int(data["version"]), key=bytes.fromhex(data["key"]))


async def read_master_key(file_path: str) -> bytes:
    """Read the master key from a JSON file asynchronously and convert hex to bytes."""
    async with aiofiles.open(file_path, mode='r') as f:
        content = await f.read()
    
    data = json.loads(content)
    key_hex = data["key"]
    
    # hex 문자열을 bytes로 변환
    return bytes.fromhex(key_hex)