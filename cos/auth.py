"""Authentication and credential management for COS CLI"""

import json
import os
import ssl
import time
import urllib3
from typing import Dict, Optional

# Disable SSL verification BEFORE importing SDK
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# Monkey patch requests module before SDK imports
import requests
original_request = requests.Session.request

def patched_request(self, method, url, **kwargs):
    kwargs['verify'] = False
    return original_request(self, method, url, **kwargs)

requests.Session.request = patched_request

# Now import SDK
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.sts.v20180813 import models as sts_models
from tencentcloud.sts.v20180813 import sts_client
from qcloud_cos import CosConfig, CosS3Client

from .config import ConfigManager
from .constants import DEFAULT_SCHEME, STS_DURATION, STS_ENDPOINT
from .exceptions import AuthenticationError


class STSTokenManager:
    """Manages STS temporary credentials"""
    
    def __init__(self, secret_id: str, secret_key: str, assume_role: Optional[str] = None):
        """
        Initialize STS token manager.
        
        Args:
            secret_id: Secret ID
            secret_key: Secret key
            assume_role: Role ARN to assume
        """
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.assume_role = assume_role
        self.sts_duration = STS_DURATION  # Allow overriding default duration
        self._cached_credentials: Optional[Dict[str, str]] = None
        self._expiration: Optional[float] = None
    
    def get_temp_credentials(
        self, 
        region: str = "ap-shanghai",
        policy: Optional[Dict] = None,
        policy_str: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get temporary credentials via STS.
        
        Args:
            region: Region for STS endpoint
            policy: Policy document as dict (for prefix restrictions)
            policy_str: Policy document as JSON string
            
        Returns:
            Dictionary containing temporary credentials
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Return cached credentials if still valid and policy matches
        # Note: We don't cache when policy is provided to ensure fresh scoped credentials
        if self._cached_credentials and self._expiration and not policy and not policy_str:
            if time.time() < self._expiration - 300:  # 5 min buffer
                return self._cached_credentials
        
        try:
            # Create credential object
            cred = credential.Credential(self.secret_id, self.secret_key)
            
            # Configure HTTP profile
            http_profile = HttpProfile()
            http_profile.endpoint = STS_ENDPOINT
            http_profile.reqTimeout = 60
            
            # Create client profile
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            client_profile.signMethod = "TC3-HMAC-SHA256"
            
            # Create STS client
            client = sts_client.StsClient(cred, region, client_profile)
            
            # Create request
            req = sts_models.AssumeRoleRequest()
            params = {
                "RoleArn": self.assume_role,
                "RoleSessionName": "tencent-cos-cli-session",
                "DurationSeconds": self.sts_duration,
            }
            
            # Add policy if provided
            if policy:
                params["Policy"] = json.dumps(policy)
            elif policy_str:
                params["Policy"] = policy_str
            
            req.from_json_string(json.dumps(params))
            
            # Get response
            resp = client.AssumeRole(req)
            result = json.loads(str(resp))
            
            # Extract credentials
            credentials = result["Credentials"]
            self._cached_credentials = {
                "tmp_secret_id": credentials["TmpSecretId"],
                "tmp_secret_key": credentials["TmpSecretKey"],
                "token": credentials["Token"],
            }
            
            # Set expiration
            self._expiration = time.time() + self.sts_duration
            
            return self._cached_credentials
            
        except TencentCloudSDKException as e:
            raise AuthenticationError(f"STS authentication failed: {e}")
        except Exception as e:
            raise AuthenticationError(f"Unexpected error during authentication: {e}")


class COSAuthenticator:
    """Handles COS authentication and client creation"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize COS authenticator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self._client: Optional[CosS3Client] = None
        self.sts_manager: Optional[STSTokenManager] = None
    
    def authenticate(self, region: Optional[str] = None, verify_ssl: bool = True) -> CosS3Client:
        """
        Authenticate and create COS client.
        
        Credential Sources (in precedence order):
        1. Environment temp credentials (COS_TOKEN + COS_SECRET_ID + COS_SECRET_KEY)
        2. Config file temp token (from 'cos configure import-token')
        3. STS via assume_role (config file)
        4. Permanent credentials (config file or env)
        
        Args:
            region: Region (overrides config)
            verify_ssl: Whether to verify SSL certificates
            
        Returns:
            Authenticated COS client
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Get credentials (with precedence rules applied)
            credentials = self.config_manager.get_credentials()
            secret_id = credentials["secret_id"]
            secret_key = credentials["secret_key"]
            assume_role = credentials.get("assume_role")
            temp_token = credentials.get("token")
            cred_source = credentials.get("_source", "unknown")
            
            # Get region
            if region is None:
                region = self.config_manager.get_region()
            
            # Branch based on credential source
            if temp_token:
                # Mode 1 or 2a: Using temporary token (from env or config file)
                # This takes precedence over assume_role
                config = CosConfig(
                    Region=region,
                    SecretId=secret_id,
                    SecretKey=secret_key,
                    Token=temp_token,
                    Scheme=DEFAULT_SCHEME,
                )
            elif assume_role:
                # Mode 2b: Use STS with assume_role
                if not self.sts_manager:
                    self.sts_manager = STSTokenManager(secret_id, secret_key, assume_role)
                
                temp_creds = self.sts_manager.get_temp_credentials(region)
                
                # Create COS config with temporary credentials
                config = CosConfig(
                    Region=region,
                    SecretId=temp_creds["tmp_secret_id"],
                    SecretKey=temp_creds["tmp_secret_key"],
                    Token=temp_creds["token"],
                    Scheme=DEFAULT_SCHEME,
                )
            else:
                # Mode 3: Use permanent credentials
                config = CosConfig(
                    Region=region,
                    SecretId=secret_id,
                    SecretKey=secret_key,
                    Scheme=DEFAULT_SCHEME,
                )
            
            # Create client
            self._client = CosS3Client(config)
            
            return self._client
            
        except Exception as e:
            raise AuthenticationError(f"Failed to authenticate: {e}")
    
    def get_client(self, region: Optional[str] = None) -> CosS3Client:
        """
        Get authenticated COS client (creates if not exists).
        
        Args:
            region: Region (overrides config)
            
        Returns:
            Authenticated COS client
        """
        if self._client is None:
            self._client = self.authenticate(region)
        return self._client
