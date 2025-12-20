"""Web UI wrapper for COS CLI client.

This module provides a simplified interface for the web UI to interact with
the COS CLI client, with proper error handling and progress callbacks.
"""

from typing import Dict, List, Optional, Callable, BinaryIO
from pathlib import Path
from datetime import datetime
import io

from cos.config import ConfigManager
from cos.auth import COSAuthenticator
from cos.client import COSClient
from cos.exceptions import (
    BucketNotFoundError,
    ObjectNotFoundError,
    PermissionDeniedError,
    COSError,
)


class WebCOSClient:
    """Web UI wrapper around COS CLI client with additional UI-friendly features."""
    
    def __init__(self, profile: str = "default"):
        """
        Initialize Web COS client.
        
        Args:
            profile: Configuration profile name
            
        Raises:
            COSError: If client initialization fails
        """
        self.profile = profile
        self.config_manager = ConfigManager(profile)
        self.authenticator = COSAuthenticator(self.config_manager)
        
        try:
            # Authenticate and get base client
            self.base_client = self.authenticator.authenticate()
            self.cos_client = COSClient(self.base_client)
        except Exception as e:
            raise COSError(f"Failed to initialize COS client: {str(e)}")
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test COS connection by listing buckets.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            buckets = self.list_buckets()
            return True, f"Connected successfully. Found {len(buckets)} bucket(s)."
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def list_buckets(self) -> List[Dict[str, str]]:
        """
        List all accessible buckets.
        
        Returns:
            List of bucket dictionaries with Name, Location, CreationDate
            
        Raises:
            COSError: If listing fails
        """
        try:
            return self.cos_client.list_buckets()
        except Exception as e:
            raise COSError(f"Failed to list buckets: {str(e)}")
    
    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        delimiter: str = "",
        max_keys: int = 1000,
        marker: str = "",
    ) -> Dict:
        """
        List objects in a bucket.
        
        Args:
            bucket: Bucket name
            prefix: Filter by prefix (folder path)
            delimiter: Group by delimiter (use '/' for folders)
            max_keys: Maximum number of objects to return
            marker: Pagination marker
            
        Returns:
            Dictionary with:
                - Contents: List of objects
                - CommonPrefixes: List of folder prefixes (if delimiter used)
                - IsTruncated: Whether more results exist
                - NextMarker: Marker for next page
                
        Raises:
            BucketNotFoundError: If bucket doesn't exist
            COSError: If listing fails
        """
        try:
            response = self.cos_client.list_objects(
                bucket=bucket,
                prefix=prefix,
                delimiter=delimiter,
                max_keys=max_keys,
            )
            return response
        except BucketNotFoundError:
            raise
        except Exception as e:
            raise COSError(f"Failed to list objects: {str(e)}")
    
    def list_files_paginated(
        self,
        bucket: str,
        prefix: str = "",
        page_size: int = 100,
    ) -> tuple[List[Dict], List[str]]:
        """
        List files with pagination support, separating files and folders.
        
        Args:
            bucket: Bucket name
            prefix: Folder prefix
            page_size: Number of items per page
            
        Returns:
            Tuple of (files_list, folders_list)
            - files_list: List of file dictionaries
            - folders_list: List of folder path strings
        """
        try:
            response = self.list_objects(
                bucket=bucket,
                prefix=prefix,
                delimiter="/",
                max_keys=page_size,
            )
            
            # Parse files
            files = []
            for obj in response.get('Contents', []):
                # Skip the prefix itself if it's a directory marker
                if obj['Key'] == prefix or obj['Key'].endswith('/'):
                    continue
                    
                files.append({
                    'key': obj['Key'],
                    'name': Path(obj['Key']).name,
                    'size': obj.get('Size', 0),
                    'last_modified': obj.get('LastModified'),
                    'etag': obj.get('ETag', '').strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD'),
                })
            
            # Parse folders (common prefixes)
            folders = []
            for prefix_obj in response.get('CommonPrefixes', []):
                folder_prefix = prefix_obj.get('Prefix', '')
                if folder_prefix:
                    folders.append(folder_prefix)
            
            return files, folders
            
        except Exception as e:
            raise COSError(f"Failed to list files: {str(e)}")
    
    def upload_file(
        self,
        bucket: str,
        key: str,
        file_obj: BinaryIO,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict:
        """
        Upload a file to COS.
        
        Args:
            bucket: Bucket name
            key: Object key (path in bucket)
            file_obj: File-like object to upload
            progress_callback: Optional callback(bytes_uploaded, total_bytes)
            
        Returns:
            Upload response dictionary with ETag
            
        Raises:
            COSError: If upload fails
        """
        try:
            # Read file content
            file_obj.seek(0)
            file_content = file_obj.read()
            total_size = len(file_content)
            
            # Create wrapper for progress tracking
            if progress_callback:
                class ProgressWrapper(io.BytesIO):
                    def __init__(self, content):
                        super().__init__(content)
                        self.bytes_read = 0
                    
                    def read(self, size=-1):
                        data = super().read(size)
                        self.bytes_read += len(data)
                        progress_callback(self.bytes_read, total_size)
                        return data
                
                file_obj = ProgressWrapper(file_content)
            else:
                file_obj = io.BytesIO(file_content)
            
            # Upload using base client
            response = self.cos_client.upload_file(
                bucket=bucket,
                key=key,
                file_obj=file_obj,
            )
            
            return response
            
        except Exception as e:
            raise COSError(f"Failed to upload file: {str(e)}")
    
    def download_file(
        self,
        bucket: str,
        key: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Download a file from COS.
        
        Args:
            bucket: Bucket name
            key: Object key
            progress_callback: Optional callback(bytes_downloaded, total_bytes)
            
        Returns:
            File content as bytes
            
        Raises:
            ObjectNotFoundError: If object doesn't exist
            COSError: If download fails
        """
        try:
            # Get object using base client
            response = self.base_client.get_object(
                Bucket=bucket,
                Key=key,
            )
            
            # Read content with progress tracking
            content = response['Body'].read()
            
            if progress_callback:
                total_size = len(content)
                progress_callback(total_size, total_size)
            
            return content
            
        except ObjectNotFoundError:
            raise
        except Exception as e:
            raise COSError(f"Failed to download file: {str(e)}")
    
    def delete_object(
        self,
        bucket: str,
        key: str,
    ) -> bool:
        """
        Delete an object from COS.
        
        Args:
            bucket: Bucket name
            key: Object key
            
        Returns:
            True if successful
            
        Raises:
            COSError: If deletion fails
        """
        try:
            self.cos_client.delete_object(bucket=bucket, key=key)
            return True
        except Exception as e:
            raise COSError(f"Failed to delete object: {str(e)}")
    
    def delete_objects(
        self,
        bucket: str,
        keys: List[str],
    ) -> Dict[str, List[str]]:
        """
        Delete multiple objects from COS.
        
        Args:
            bucket: Bucket name
            keys: List of object keys
            
        Returns:
            Dictionary with 'deleted' and 'errors' lists
        """
        deleted = []
        errors = []
        
        for key in keys:
            try:
                self.delete_object(bucket, key)
                deleted.append(key)
            except Exception as e:
                errors.append(f"{key}: {str(e)}")
        
        return {
            'deleted': deleted,
            'errors': errors,
        }
    
    def get_object_metadata(
        self,
        bucket: str,
        key: str,
    ) -> Dict:
        """
        Get object metadata without downloading content.
        
        Args:
            bucket: Bucket name
            key: Object key
            
        Returns:
            Metadata dictionary
            
        Raises:
            ObjectNotFoundError: If object doesn't exist
            COSError: If operation fails
        """
        try:
            response = self.cos_client.head_object(bucket=bucket, key=key)
            return {
                'content_length': response.get('Content-Length', 0),
                'content_type': response.get('Content-Type', ''),
                'last_modified': response.get('Last-Modified', ''),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {}),
            }
        except ObjectNotFoundError:
            raise
        except Exception as e:
            raise COSError(f"Failed to get metadata: {str(e)}")
    
    def create_folder(
        self,
        bucket: str,
        folder_path: str,
    ) -> bool:
        """
        Create a folder (empty object ending with /).
        
        Args:
            bucket: Bucket name
            folder_path: Folder path (will append / if missing)
            
        Returns:
            True if successful
        """
        if not folder_path.endswith('/'):
            folder_path += '/'
        
        try:
            # Upload empty object with / suffix
            self.cos_client.put_object(
                bucket=bucket,
                key=folder_path,
                body=b'',
            )
            return True
        except Exception as e:
            raise COSError(f"Failed to create folder: {str(e)}")
    
    def get_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        method: str = 'GET',
    ) -> str:
        """
        Generate a presigned URL for object access.
        
        Args:
            bucket: Bucket name
            key: Object key
            expires_in: Expiration time in seconds (default 1 hour)
            method: HTTP method (GET, PUT, DELETE)
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.base_client.get_presigned_url(
                Method=method,
                Bucket=bucket,
                Key=key,
                Expired=expires_in,
            )
            return url
        except Exception as e:
            raise COSError(f"Failed to generate presigned URL: {str(e)}")
    
    def get_bucket_info(self, bucket: str) -> Dict:
        """
        Get bucket information.
        
        Args:
            bucket: Bucket name
            
        Returns:
            Dictionary with bucket metadata
        """
        try:
            # Get bucket location
            location_response = self.base_client.get_bucket_location(Bucket=bucket)
            location = location_response.get('LocationConstraint', 'Unknown')
            
            # Get bucket statistics (requires listing)
            response = self.list_objects(bucket=bucket, max_keys=1)
            
            return {
                'name': bucket,
                'region': location,
                'exists': True,
            }
        except BucketNotFoundError:
            return {
                'name': bucket,
                'exists': False,
            }
        except Exception as e:
            raise COSError(f"Failed to get bucket info: {str(e)}")
