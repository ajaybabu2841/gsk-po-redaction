from azure.storage.blob import BlobServiceClient
import os
from azure.storage.blob import ContentSettings

def upload_bytes_to_blob(
    *,
    container_name: str,
    blob_name: str,
    data: bytes,
    content_type: str = "application/pdf"
):
    blob_service_client = BlobServiceClient.from_connection_string(
        os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    )

    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name
    )

    blob_client.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(
            content_type="application/pdf"
        )
    )

    return blob_name  # acts as URL/reference
 