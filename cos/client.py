"""COS client wrapper with high-level operations"""

from typing import Dict, List, Optional
from qcloud_cos import CosS3Client
from qcloud_cos.cos_exception import CosServiceError, CosClientError

from .exceptions import (
    BucketNotFoundError,
    ObjectNotFoundError,
    PermissionDeniedError,
    COSError,
)


class COSClient:
    """Wrapper for COS client with error handling"""
    
    def __init__(self, client: CosS3Client, bucket: Optional[str] = None):
        """
        Initialize COS client wrapper.
        
        Args:
            client: Authenticated CosS3Client
            bucket: Default bucket name
        """
        self.client = client
        self.bucket = bucket
    
    def _handle_error(self, error: Exception) -> None:
        """Handle COS errors and raise appropriate exceptions"""
        if isinstance(error, CosServiceError):
            code = error.get_error_code()
            if code == "NoSuchBucket":
                raise BucketNotFoundError(error.get_error_msg())
            elif code == "NoSuchKey":
                raise ObjectNotFoundError(error.get_error_msg())
            elif code in ["AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"]:
                raise PermissionDeniedError(error.get_error_msg())
            else:
                raise COSError(f"{code}: {error.get_error_msg()}")
        elif isinstance(error, CosClientError):
            raise COSError(str(error))
        else:
            raise COSError(str(error))
    
    def list_buckets(self) -> List[Dict[str, str]]:
        """
        List all buckets.
        
        Returns:
            List of bucket information dictionaries
        """
        try:
            response = self.client.list_buckets()
            buckets = []
            for bucket in response.get("Buckets", {}).get("Bucket", []):
                buckets.append({
                    "Name": bucket.get("Name", ""),
                    "Location": bucket.get("Location", ""),
                    "CreationDate": bucket.get("CreationDate", ""),
                })
            return buckets
        except Exception as e:
            self._handle_error(e)
    
    def list_objects(
        self,
        bucket: Optional[str] = None,
        prefix: str = "",
        delimiter: str = "",
        max_keys: int = 1000,
    ) -> Dict:
        """
        List objects in bucket.
        
        Args:
            bucket: Bucket name (uses default if not provided)
            prefix: Prefix to filter objects
            delimiter: Delimiter for grouping
            max_keys: Maximum number of keys to return
            
        Returns:
            Response dictionary with objects and common prefixes
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.list_objects(
                Bucket=bucket,
                Prefix=prefix,
                Delimiter=delimiter,
                MaxKeys=max_keys,
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def upload_file(
        self,
        local_path: str,
        key: str,
        bucket: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Upload file to COS.
        
        Args:
            local_path: Local file path
            key: Object key in COS
            bucket: Bucket name (uses default if not provided)
            **kwargs: Additional arguments for upload
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.upload_file(
                Bucket=bucket,
                LocalFilePath=local_path,
                Key=key,
                **kwargs
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def download_file(
        self,
        key: str,
        local_path: str,
        bucket: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Download file from COS.
        
        Args:
            key: Object key in COS
            local_path: Local file path to save
            bucket: Bucket name (uses default if not provided)
            **kwargs: Additional arguments for download
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.download_file(
                Bucket=bucket,
                Key=key,
                DestFilePath=local_path,
                **kwargs
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def delete_object(self, key: str, bucket: Optional[str] = None) -> Dict:
        """
        Delete object from COS.
        
        Args:
            key: Object key in COS
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.delete_object(
                Bucket=bucket,
                Key=key,
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def create_bucket(self, bucket: str, **kwargs) -> Dict:
        """
        Create bucket.
        
        Args:
            bucket: Bucket name
            **kwargs: Additional arguments
            
        Returns:
            Response dictionary
        """
        try:
            response = self.client.create_bucket(
                Bucket=bucket,
                **kwargs
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def delete_bucket(self, bucket: str) -> Dict:
        """
        Delete bucket.
        
        Args:
            bucket: Bucket name
            
        Returns:
            Response dictionary
        """
        try:
            response = self.client.delete_bucket(Bucket=bucket)
            return response
        except Exception as e:
            self._handle_error(e)
    
    def head_object(self, key: str, bucket: Optional[str] = None) -> Dict:
        """
        Get object metadata.
        
        Args:
            key: Object key in COS
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary with metadata
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.head_object(
                Bucket=bucket,
                Key=key,
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
        **kwargs
    ) -> Dict:
        """
        Copy object within COS.
        
        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key
            **kwargs: Additional arguments
            
        Returns:
            Response dictionary
        """
        try:
            copy_source = {
                "Bucket": source_bucket,
                "Key": source_key,
                "Region": self.client._conf._region,
            }
            response = self.client.copy_object(
                Bucket=dest_bucket,
                Key=dest_key,
                CopySource=copy_source,
                **kwargs
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def get_bucket_lifecycle(self, bucket: Optional[str] = None) -> Dict:
        """
        Get bucket lifecycle configuration.
        
        Args:
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary with lifecycle rules
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.get_bucket_lifecycle(Bucket=bucket)
            return response
        except Exception as e:
            self._handle_error(e)
    
    def put_bucket_lifecycle(self, lifecycle_config: Dict, bucket: Optional[str] = None) -> Dict:
        """
        Set bucket lifecycle configuration.
        
        Args:
            lifecycle_config: Lifecycle configuration dictionary
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.put_bucket_lifecycle(
                Bucket=bucket,
                LifecycleConfiguration=lifecycle_config
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def delete_bucket_lifecycle(self, bucket: Optional[str] = None) -> Dict:
        """
        Delete bucket lifecycle configuration.
        
        Args:
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.delete_bucket_lifecycle(Bucket=bucket)
            return response
        except Exception as e:
            self._handle_error(e)
    
    def get_bucket_policy(self, bucket: Optional[str] = None) -> Dict:
        """
        Get bucket policy.
        
        Args:
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary with policy
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.get_bucket_policy(Bucket=bucket)
            return response
        except Exception as e:
            self._handle_error(e)
    
    def put_bucket_policy(self, policy: str, bucket: Optional[str] = None) -> Dict:
        """
        Set bucket policy.
        
        Args:
            policy: Policy JSON string
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.put_bucket_policy(
                Bucket=bucket,
                Policy=policy
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def delete_bucket_policy(self, bucket: Optional[str] = None) -> Dict:
        """
        Delete bucket policy.
        
        Args:
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.delete_bucket_policy(Bucket=bucket)
            return response
        except Exception as e:
            self._handle_error(e)
    
    def get_bucket_cors(self, bucket: Optional[str] = None) -> Dict:
        """
        Get bucket CORS configuration.
        
        Args:
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary with CORS rules
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.get_bucket_cors(Bucket=bucket)
            return response
        except Exception as e:
            self._handle_error(e)
    
    def put_bucket_cors(self, cors_config: Dict, bucket: Optional[str] = None) -> Dict:
        """
        Set bucket CORS configuration.
        
        Args:
            cors_config: CORS configuration dictionary
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.put_bucket_cors(
                Bucket=bucket,
                CORSConfiguration=cors_config
            )
            return response
        except Exception as e:
            self._handle_error(e)
    
    def delete_bucket_cors(self, bucket: Optional[str] = None) -> Dict:
        """
        Delete bucket CORS configuration.
        
        Args:
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.delete_bucket_cors(Bucket=bucket)
            return response
        except Exception as e:
            self._handle_error(e)
    
    def get_bucket_versioning(self, bucket: Optional[str] = None) -> Dict:
        """
        Get bucket versioning status.
        
        Args:
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary with versioning status
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.get_bucket_versioning(Bucket=bucket)
            return response
        except Exception as e:
            self._handle_error(e)
    
    def put_bucket_versioning(self, status: str, bucket: Optional[str] = None) -> Dict:
        """
        Set bucket versioning status.
        
        Args:
            status: Versioning status ('Enabled' or 'Suspended')
            bucket: Bucket name (uses default if not provided)
            
        Returns:
            Response dictionary
        """
        bucket = bucket or self.bucket
        if not bucket:
            raise COSError("Bucket name is required")
        
        try:
            response = self.client.put_bucket_versioning(
                Bucket=bucket,
                Status=status
            )
            return response
        except Exception as e:
            self._handle_error(e)
