import io
import os
import socket
import logging

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

_minio_host = os.environ.get("MINIO_HOST", "localhost")
# MINIO_HOST is a Docker container name (e.g. "workspace__minio-dev")
# Docker hostnames with "__" are invalid per HTTP RFC, causing MinIO server
# to reject the Host header. Resolve to IP to avoid this.
try:
    _resolved = socket.gethostbyname(_minio_host)
except socket.gaierror:
    _resolved = _minio_host
MINIO_ENDPOINT = f"{_resolved}:9000" if ":" not in _resolved else _resolved
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin")
GALLERY_BUCKET = "gallery"


def _get_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )


async def ensure_bucket():
    client = _get_client()
    if not client.bucket_exists(GALLERY_BUCKET):
        client.make_bucket(GALLERY_BUCKET)
        logger.info("Created bucket: %s", GALLERY_BUCKET)


async def preseed_logo():
    """Upload the bitswan logo to the gallery if it doesn't already exist."""
    client = _get_client()
    key = "bitswan-logo.svg"
    try:
        client.stat_object(GALLERY_BUCKET, key)
        logger.info("Logo already exists in gallery, skipping preseed")
        return
    except S3Error:
        pass

    logo_svg = b"""\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="48" height="48" viewBox="0 0 12.7 12.7" version="1.1"
     xmlns="http://www.w3.org/2000/svg">
  <g id="layer1">
    <path d="M 1.8973129,8.434312 V 1.3690289 L 6.1506839,4.9194224 2.6286945,7.6035199 C 2.3233601,7.8307451 2.074833,8.1147768 1.8973129,8.434312 Z M 8.3377281,6.737224 6.8252585,8.0153652 C 6.3211029,8.4556149 6.0512722,9.0449798 6.0512722,9.7195546 c 0,0.6106674 0.2414286,1.1858324 0.667476,1.6189794 0.4331482,0.433147 1.0083108,0.674575 1.6189799,0.674575 0.6106656,0 1.1858308,-0.241428 1.618979,-0.674575 0.4331489,-0.433147 0.6674729,-1.008312 0.6674729,-1.6189794 0,-0.6106678 -0.234324,-1.1858312 -0.6674729,-1.6118784 z M 10.311745,2.1359139 8.5365493,3.5205675 v 0 L 2.8275157,7.8733501 C 2.245252,8.2993973 1.8973129,8.9881737 1.8973129,9.7124541 c 0,0.6106679 0.2414259,1.1858309 0.6674731,1.6189799 0.4331485,0.433147 1.0083136,0.674574 1.6189796,0.674574 H 7.0524845 C 6.8465623,11.892396 6.6548399,11.743279 6.4773198,11.57286 5.9802652,11.075805 5.7104344,10.415432 5.7104344,9.7195546 c 0,-0.7597844 0.3124356,-1.4556617 0.8876008,-1.9598171 L 9.8643969,5.0117324 c 0.4828541,-0.4118452 0.7668841,-1.058017 0.7668841,-1.7041886 0,-0.4189465 -0.106512,-0.8165907 -0.319536,-1.1716299 z M 5.9802652,1.0139894 8.5436498,3.0945202 10.112924,1.8660839 C 10.07742,1.8234791 10.020613,1.7595721 9.9496056,1.6743626 9.4951567,1.1276019 8.8205792,1.0139894 8.3448287,1.0139894 Z"
          style="stroke-width:0.071008" />
  </g>
</svg>"""
    client.put_object(
        GALLERY_BUCKET,
        key,
        io.BytesIO(logo_svg),
        length=len(logo_svg),
        content_type="image/svg+xml",
    )
    logger.info("Preseeded bitswan logo into gallery")


async def upload_file(key: str, data: bytes, content_type: str):
    client = _get_client()
    client.put_object(
        GALLERY_BUCKET,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


async def get_file(key: str) -> tuple[bytes, str]:
    client = _get_client()
    response = client.get_object(GALLERY_BUCKET, key)
    try:
        data = response.read()
        content_type = response.headers.get("Content-Type", "application/octet-stream")
    finally:
        response.close()
        response.release_conn()
    return data, content_type


async def delete_file(key: str):
    client = _get_client()
    client.remove_object(GALLERY_BUCKET, key)
