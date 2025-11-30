"""
Google Cloud Platform Configuration
Handles GCP services setup

Author: Santosh Yadav
Date: November 2025
"""

import os
import logging
from typing import Optional

from google.cloud import storage
from google.cloud import logging as cloud_logging

logger = logging.getLogger(__name__)


class GCPConfig:
    """Google Cloud Platform configuration and client management"""

    def __init__(self):
        """Initialize GCP configuration"""
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "pdf-learning-pdfs")
        self.environment = os.getenv("ENVIRONMENT", "development")

        # Storage client
        self.storage_client: Optional[storage.Client] = None
        self.bucket: Optional[storage.Bucket] = None

        # Cloud Logging client
        self.logging_client: Optional[cloud_logging.Client] = None

        if self.environment == "production":
            self._initialize_gcp_services()

    def _initialize_gcp_services(self):
        """Initialize GCP services in production"""
        try:
            # Initialize Cloud Storage
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            logger.info(f"✅ GCS initialized: {self.bucket_name}")

            # Initialize Cloud Logging
            self.logging_client = cloud_logging.Client(project=self.project_id)
            self.logging_client.setup_logging()
            logger.info("✅ Cloud Logging initialized")

        except Exception as e:
            logger.error(f"Failed to initialize GCP services: {e}", exc_info=True)

    def upload_file_to_gcs(self, local_path: str, gcs_path: str) -> str:
        """
        Upload file to Google Cloud Storage

        Args:
            local_path: Local file path
            gcs_path: Destination path in GCS

        Returns:
            str: Public URL or signed URL
        """
        if self.environment != "production" or not self.bucket:
            return local_path

        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_path)
            logger.info(f"Uploaded {local_path} to gs://{self.bucket_name}/{gcs_path}")
            return f"gs://{self.bucket_name}/{gcs_path}"
        except Exception as e:
            logger.error(f"GCS upload failed: {e}", exc_info=True)
            return local_path

    def download_file_from_gcs(self, gcs_path: str, local_path: str) -> bool:
        """Download file from GCS"""
        if self.environment != "production" or not self.bucket:
            return False

        try:
            blob = self.bucket.blob(gcs_path)
            blob.download_to_filename(local_path)
            logger.info(f"Downloaded gs://{self.bucket_name}/{gcs_path} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"GCS download failed: {e}", exc_info=True)
            return False


# Singleton instance
_gcp_config_instance: Optional[GCPConfig] = None


def get_gcp_config() -> GCPConfig:
    """Get GCP configuration singleton"""
    global _gcp_config_instance

    if _gcp_config_instance is None:
        _gcp_config_instance = GCPConfig()

    return _gcp_config_instance

