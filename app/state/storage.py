from __future__ import annotations

import asyncio
import os
from abc import ABC
from abc import abstractmethod

from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from types_aiobotocore_s3 import S3Client

import logger


class AbstractStorage(ABC):
    @abstractmethod
    async def load(self, key: str) -> bytes | None:
        """Loads a binary file from long-term storage."""
        ...

    @abstractmethod
    async def save(self, key: str, data: bytes) -> None:
        """Saves a binary file to long-term storage. It is not guaranteed
        that the file will be available immediately after this method."""
        ...


class LocalStorage(AbstractStorage):
    def __init__(self, root: str) -> None:
        self._root = root

    def __ensure_subdirectories(self, key: str) -> None:
        if "/" not in key:
            return

        directory = os.path.dirname(f"{self._root}/{key}")
        os.makedirs(directory, exist_ok=True)

    async def load(self, key: str) -> bytes | None:
        location = f"{self._root}/{key}"
        if not os.path.exists(location):
            return None

        with open(location, "rb") as file:
            return file.read()

    async def save(self, key: str, data: bytes) -> None:
        self.__ensure_subdirectories(key)
        location = f"{self._root}/{key}"

        with open(location, "wb") as file:
            file.write(data)


class S3Storage(AbstractStorage):
    def __init__(
        self,
        region: str,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        timeout: int,
        retries: int,
    ) -> None:
        boto_config = AioConfig(
            timeout=timeout,
        )
        self._s3_creator = get_session().create_client(
            "s3",
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=boto_config,
        )
        self._s3 = None
        self._bucket = bucket
        self._retries = retries

    async def connect(self) -> None:
        self._s3 = await self._s3_creator.__aenter__()

    async def disconnect(self) -> None:
        await self._s3_creator.__aexit__(None, None, None)
        self._s3 = None

    async def __save_file(self, key: str, data: bytes) -> None:
        assert self._s3 is not None

        await self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
        )

    async def __save(self, key: str, data: bytes) -> None:
        for i in range(self._retries):
            try:
                await self.__save_file(key, data)
                return
            except Exception as e:
                sleep_time = i * 2
                logger.error(str(e))
                logger.warning(
                    f"Failed to save {key} to S3. Retrying in {sleep_time}s...",
                )
                await asyncio.sleep(sleep_time)

        logger.error(
            f"Failed to save {key} to S3 after  {self._retries} retries.",
        )

    async def save(self, key: str, data: bytes) -> None:
        if self._s3 is None:
            raise RuntimeError("The S3 client has not been connected!")

        asyncio.create_task(self.__save(key, data))

    async def load(self, key: str) -> bytes | None:
        if self._s3 is None:
            raise RuntimeError("The S3 client has not been connected!")

        try:
            response = await self._s3.get_object(
                Bucket=self._bucket,
                Key=key,
            )
        except self._s3.exceptions.NoSuchKey:
            return None

        return await response["Body"].read()