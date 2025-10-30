import os
import uuid
from datetime import datetime, timedelta

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    ContentSettings,
    generate_blob_sas,
)
from config import AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY, AZURE_STORAGE_CONTAINER, AZURE_STORAGE_ENDPOINT


_container_client = None


def _get_container_client():
    """한 번 생성한 컨테이너 클라이언트를 재사용한다."""
    global _container_client
    if _container_client is None:
        if not AZURE_STORAGE_ACCOUNT or not AZURE_STORAGE_KEY or not AZURE_STORAGE_CONTAINER:
            raise RuntimeError("Azure Storage 설정이 누락되었습니다.")

        account_url = AZURE_STORAGE_ENDPOINT or f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net"
        service_client = BlobServiceClient(account_url=account_url, credential=AZURE_STORAGE_KEY)
        _container_client = service_client.get_container_client(AZURE_STORAGE_CONTAINER)

    return _container_client


def upload_blob_and_get_url(
    data: bytes,
    suffix: str,
    content_type: str,
    expiry_minutes: int = 60,
) -> str:
    """
    데이터를 업로드하고 SAS URL을 반환한다.

    suffix: 확장자 (예: 'csv', 'docx')
    content_type: MIME 타입
    expiry_minutes: SAS 만료 시간(분)
    """
    if not data:
        raise ValueError("업로드할 데이터가 비어 있습니다.")

    container_client = _get_container_client()
    blob_name = f"{uuid.uuid4().hex}.{suffix.lstrip('.')}" if suffix else uuid.uuid4().hex

    blob_client = container_client.get_blob_client(blob_name)

    blob_client.upload_blob(
        data=data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )

    sas_token = generate_blob_sas(
        account_name=AZURE_STORAGE_ACCOUNT,
        container_name=AZURE_STORAGE_CONTAINER,
        blob_name=blob_name,
        account_key=AZURE_STORAGE_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )

    return f"{container_client.url}/{blob_name}?{sas_token}"
