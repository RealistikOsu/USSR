from __future__ import annotations

import logging
from typing import Any

import botocore.exceptions

import config
from app.state import services


async def upload(
    body: bytes,
    file_name: str,
    folder: str,
    content_type: str | None = None,
    acl: str | None = None,
) -> None:
    params: dict[str, Any] = {
        "Bucket": config.AWS_BUCKET_NAME,
        "Key": f"{folder}/{file_name}",
        "Body": body,
    }
    if content_type is not None:
        params["ContentType"] = content_type
    if acl is not None:
        params["ACL"] = acl

    try:
        await services.s3_client.put_object(**params)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as exc:
        logging.error("Failed to upload file to S3", exc_info=exc)
        return None

    return None


async def download(file_name: str, folder: str) -> bytes | None:
    try:
        response = await services.s3_client.get_object(
            Bucket=config.AWS_BUCKET_NAME,
            Key=f"{folder}/{file_name}",
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as exc:
        logging.error("Failed to download file from S3", exc_info=exc)
        return None

    return await response["Body"].read()
