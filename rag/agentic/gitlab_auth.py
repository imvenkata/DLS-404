"""
GitLab authentication module for Semantic Kernel integration.

This module provides secure authentication methods for GitLab:
1. Personal Access Token (PAT) authentication
2. OAuth authentication
3. Secure credential management
"""
import os
import logging
import json
import base64
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import urllib.parse
import requests
from pathlib import Path
import keyring

import semantic_kernel as sk
from semantic_kernel.functions.kernel_function_decorator import kernel_function

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitLabAuth:
    """
    GitLab authentication for Semantic Kernel integration.
    
    This class provides secure authentication methods for GitLab:
    1. Personal Access Token (PAT) authentication
    2. OAuth authentication
    3. Secure credential management
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize GitLab authentication.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file
        self.config = {}
        self.token_cache = {}
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded GitLab authentication configuration from {config_file}")
            except Exception as e:
                logger.error(f"Error loading GitLab authentication configuration: {str(e)}")
    
    @kernel_function(
        description="Configure GitLab authentication with a Personal Access Token",
        name="configure_pat_auth"
    )
    def configure_pat_auth(self, gitlab_url: str, token: str, store_securely: str = "true") -> str:
        """
        Configure GitLab authentication with a Personal Access Token.
        
        Args:
            gitlab_url: GitLab instance URL
            token: Personal Access Token
            store_securely: Whether to store the token securely in the system keyring (true/false)
            
        Returns:
            JSON string with configuration status
        """
        store_securely = store_securely.lower() == "true"
        
        logger.info(f"Configuring GitLab PAT authentication for {gitlab_url}")
        
        # Validate URL
        if not gitlab_url.startswith(("http://", "https://")):
            gitlab_url = f"https://{gitlab_url}"
        
        # Store configuration
        self.config["auth_type"] = "pat"
        self.config["gitlab_url"] = gitlab_url
        
        # Store token securely if requested
        if store_securely:
            try:
                service_name = f"gitlab-semantic-kernel-{urllib.parse.urlparse(gitlab_url).netloc}"
                keyring.set_password(service_name, "pat", token)
                self.config["token_storage"] = "keyring"
                self.config["keyring_service"] = service_name
                logger.info(f"Stored GitLab PAT securely in system keyring")
            except Exception as e:
                logger.error(f"Error storing GitLab PAT in keyring: {str(e)}")
                # Fall back to storing in config
                self.config["token"] = token
                self.config["token_storage"] = "config"
        else:
            # Store in config
            self.config["token"] = token
            self.config["token_storage"] = "config"
        
        # Save configuration if config file is specified
        if self.config_file:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                logger.info(f"Saved GitLab authentication configuration to {self.config_file}")
            except Exception as e:
                logger.error(f"Error saving GitLab authentication configuration: {str(e)}")
        
        # Test the token
        try:
            headers = {"PRIVATE-TOKEN": token}
            response = requests.get(f"{gitlab_url}/api/v4/user", headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"Successfully authenticated as {user_info.get('username', 'unknown user')}")
                return json.dumps({
                    "status": "success",
                    "message": f"Successfully configured PAT authentication for {gitlab_url}",
                    "user": user_info.get('username'),
                    "token_storage": self.config["token_storage"]
                }, indent=2)
            else:
                error_message = f"Failed to authenticate with GitLab: {response.status_code} {response.text}"
                logger.error(error_message)
                return json.dumps({
                    "status": "error",
                    "message": error_message
                }, indent=2)
        except Exception as e:
            error_message = f"Error testing GitLab authentication: {str(e)}"
            logger.error(error_message)
            return json.dumps({
                "status": "error",
                "message": error_message
            }, indent=2)
    
    @kernel_function(
        description="Configure GitLab OAuth authentication",
        name="configure_oauth_auth"
    )
    def configure_oauth_auth(self, gitlab_url: str, client_id: str, client_secret: str, redirect_uri: str) -> str:
        """
        Configure GitLab OAuth authentication.
        
        Args:
            gitlab_url: GitLab instance URL
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            
        Returns:
            JSON string with configuration status and authorization URL
        """
        
        logger.info(f"Configuring GitLab OAuth authentication for {gitlab_url}")
        
        # Validate URL
        if not gitlab_url.startswith(("http://", "https://")):
            gitlab_url = f"https://{gitlab_url}"
        
        # Store configuration
        self.config["auth_type"] = "oauth"
        self.config["gitlab_url"] = gitlab_url
        self.config["client_id"] = client_id
        self.config["client_secret"] = client_secret
        self.config["redirect_uri"] = redirect_uri
        
        # Save configuration if config file is specified
        if self.config_file:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                logger.info(f"Saved GitLab authentication configuration to {self.config_file}")
            except Exception as e:
                logger.error(f"Error saving GitLab authentication configuration: {str(e)}")
        
        # Generate authorization URL
        auth_url = (
            f"{gitlab_url}/oauth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
            f"&response_type=code"
            f"&scope=api"
        )
        
        return json.dumps({
            "status": "success",
            "message": "OAuth configuration saved. User must authorize access.",
            "auth_url": auth_url
        }, indent=2)
    
    @kernel_function(
        description="Complete OAuth authorization with code",
        name="complete_oauth_auth"
    )
    def complete_oauth_auth(self, code: str) -> str:
        """
        Complete OAuth authorization with code.
        
        Args:
            code: OAuth authorization code
            
        Returns:
            JSON string with authorization status
        """
        
        if self.config.get("auth_type") != "oauth":
            error_message = "OAuth authentication not configured. Call configure_oauth_auth first."
            logger.error(error_message)
            return json.dumps({
                "status": "error",
                "message": error_message
            }, indent=2)
        
        gitlab_url = self.config["gitlab_url"]
        client_id = self.config["client_id"]
        client_secret = self.config["client_secret"]
        redirect_uri = self.config["redirect_uri"]
        
        logger.info(f"Completing GitLab OAuth authorization for {gitlab_url}")
        
        try:
            # Exchange code for token
            token_url = f"{gitlab_url}/oauth/token"
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
            
            response = requests.post(token_url, data=payload)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 7200)
                
                # Store tokens
                self.token_cache = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                }
                
                # Store refresh token securely
                try:
                    service_name = f"gitlab-semantic-kernel-{urllib.parse.urlparse(gitlab_url).netloc}"
                    keyring.set_password(service_name, "refresh_token", refresh_token)
                    self.config["token_storage"] = "keyring"
                    self.config["keyring_service"] = service_name
                    logger.info(f"Stored GitLab refresh token securely in system keyring")
                except Exception as e:
                    logger.error(f"Error storing GitLab refresh token in keyring: {str(e)}")
                    # Fall back to storing in config
                    self.config["refresh_token"] = refresh_token
                    self.config["token_storage"] = "config"
                
                # Save configuration if config file is specified
                if self.config_file:
                    try:
                        with open(self.config_file, 'w') as f:
                            json.dump(self.config, f, indent=2)
                        logger.info(f"Updated GitLab authentication configuration in {self.config_file}")
                    except Exception as e:
                        logger.error(f"Error updating GitLab authentication configuration: {str(e)}")
                
                # Test the token
                headers = {"Authorization": f"Bearer {access_token}"}
                user_response = requests.get(f"{gitlab_url}/api/v4/user", headers=headers)
                
                if user_response.status_code == 200:
                    user_info = user_response.json()
                    logger.info(f"Successfully authenticated as {user_info.get('username', 'unknown user')}")
                    return json.dumps({
                        "status": "success",
                        "message": "OAuth authorization completed successfully",
                        "user": user_info.get('username'),
                        "token_storage": self.config["token_storage"]
                    }, indent=2)
                else:
                    error_message = f"Failed to validate access token: {user_response.status_code} {user_response.text}"
                    logger.error(error_message)
                    return json.dumps({
                        "status": "error",
                        "message": error_message
                    }, indent=2)
            else:
                error_message = f"Failed to exchange code for token: {response.status_code} {response.text}"
                logger.error(error_message)
                return json.dumps({
                    "status": "error",
                    "message": error_message
                }, indent=2)
        except Exception as e:
            error_message = f"Error completing OAuth authorization: {str(e)}"
            logger.error(error_message)
            return json.dumps({
                "status": "error",
                "message": error_message
            }, indent=2)
    
    @kernel_function(
        description="Get the current GitLab authentication token",
        name="get_auth_token"
    )
    def get_auth_token(self, context) -> str:
        """
        Get the current GitLab authentication token.
        
        Args:
            context: Semantic Kernel context
            
        Returns:
            JSON string with token information (token itself is not exposed)
        """
        logger.info("Getting current GitLab authentication token")
        
        if not self.config:
            error_message = "GitLab authentication not configured"
            logger.error(error_message)
            return json.dumps({
                "status": "error",
                "message": error_message
            }, indent=2)
        
        auth_type = self.config.get("auth_type")
        
        if auth_type == "pat":
            # For PAT, just check if we have a token
            if self.config.get("token_storage") == "keyring":
                try:
                    service_name = self.config.get("keyring_service")
                    token = keyring.get_password(service_name, "pat")
                    if token:
                        return json.dumps({
                            "status": "success",
                            "auth_type": "pat",
                            "storage": "keyring",
                            "gitlab_url": self.config.get("gitlab_url")
                        }, indent=2)
                    else:
                        error_message = "PAT not found in keyring"
                        logger.error(error_message)
                        return json.dumps({
                            "status": "error",
                            "message": error_message
                        }, indent=2)
                except Exception as e:
                    error_message = f"Error retrieving PAT from keyring: {str(e)}"
                    logger.error(error_message)
                    return json.dumps({
                        "status": "error",
                        "message": error_message
                    }, indent=2)
            elif "token" in self.config:
                return json.dumps({
                    "status": "success",
                    "auth_type": "pat",
                    "storage": "config",
                    "gitlab_url": self.config.get("gitlab_url")
                }, indent=2)
            else:
                error_message = "PAT not found in configuration"
                logger.error(error_message)
                return json.dumps({
                    "status": "error",
                    "message": error_message
                }, indent=2)
        elif auth_type == "oauth":
            # For OAuth, check if we have a valid access token or can refresh
            if self.token_cache.get("access_token"):
                # Check if token is expired
                expires_at = self.token_cache.get("expires_at")
                if expires_at and datetime.fromisoformat(expires_at) > datetime.now():
                    return json.dumps({
                        "status": "success",
                        "auth_type": "oauth",
                        "token_status": "valid",
                        "expires_at": expires_at,
                        "gitlab_url": self.config.get("gitlab_url")
                    }, indent=2)
            
            # Try to refresh the token
            refresh_token = None
            
            if self.config.get("token_storage") == "keyring":
                try:
                    service_name = self.config.get("keyring_service")
                    refresh_token = keyring.get_password(service_name, "refresh_token")
                except Exception as e:
                    logger.error(f"Error retrieving refresh token from keyring: {str(e)}")
            elif "refresh_token" in self.config:
                refresh_token = self.config.get("refresh_token")
            
            if refresh_token:
                return json.dumps({
                    "status": "success",
                    "auth_type": "oauth",
                    "token_status": "can_refresh",
                    "gitlab_url": self.config.get("gitlab_url")
                }, indent=2)
            else:
                error_message = "OAuth refresh token not found"
                logger.error(error_message)
                return json.dumps({
                    "status": "error",
                    "message": error_message
                }, indent=2)
        else:
            error_message = f"Unknown authentication type: {auth_type}"
            logger.error(error_message)
            return json.dumps({
                "status": "error",
                "message": error_message
            }, indent=2)
    
    def get_token_for_api_call(self) -> Optional[Dict[str, str]]:
        """
        Get the appropriate token and headers for an API call.
        
        Returns:
            Dictionary with headers for API call, or None if authentication fails
        """
        if not self.config:
            logger.error("GitLab authentication not configured")
            return None
        
        auth_type = self.config.get("auth_type")
        
        if auth_type == "pat":
            # Get PAT
            token = None
            
            if self.config.get("token_storage") == "keyring":
                try:
                    service_name = self.config.get("keyring_service")
                    token = keyring.get_password(service_name, "pat")
                except Exception as e:
                    logger.error(f"Error retrieving PAT from keyring: {str(e)}")
            elif "token" in self.config:
                token = self.config.get("token")
            
            if token:
                return {"PRIVATE-TOKEN": token}
            else:
                logger.error("PAT not found")
                return None
        elif auth_type == "oauth":
            # Check if we have a valid access token
            if self.token_cache.get("access_token"):
                expires_at = self.token_cache.get("expires_at")
                if expires_at and datetime.fromisoformat(expires_at) > datetime.now():
                    return {"Authorization": f"Bearer {self.token_cache['access_token']}"}
            
            # Try to refresh the token
            refresh_token = None
            
            if self.config.get("token_storage") == "keyring":
                try:
                    service_name = self.config.get("keyring_service")
                    refresh_token = keyring.get_password(service_name, "refresh_token")
                except Exception as e:
                    logger.error(f"Error retrieving refresh token from keyring: {str(e)}")
            elif "refresh_token" in self.config:
                refresh_token = self.config.get("refresh_token")
            
            if refresh_token:
                try:
                    # Refresh the token
                    gitlab_url = self.config.get("gitlab_url")
                    client_id = self.config.get("client_id")
                    client_secret = self.config.get("client_secret")
                    
                    token_url = f"{gitlab_url}/oauth/token"
                    payload = {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                    
                    response = requests.post(token_url, data=payload)
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        access_token = token_data.get("access_token")
                        new_refresh_token = token_data.get("refresh_token")
                        expires_in = token_data.get("expires_in", 7200)
                        
                        # Update tokens
                        self.token_cache = {
                            "access_token": access_token,
                            "refresh_token": new_refresh_token,
                            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat()
                        }
                        
                        # Update stored refresh token
                        if self.config.get("token_storage") == "keyring":
                            try:
                                service_name = self.config.get("keyring_service")
                                keyring.set_password(service_name, "refresh_token", new_refresh_token)
                            except Exception as e:
                                logger.error(f"Error storing new refresh token in keyring: {str(e)}")
                                # Fall back to storing in config
                                self.config["refresh_token"] = new_refresh_token
                                self.config["token_storage"] = "config"
                        else:
                            self.config["refresh_token"] = new_refresh_token
                        
                        # Save configuration if config file is specified
                        if self.config_file:
                            try:
                                with open(self.config_file, 'w') as f:
                                    json.dump(self.config, f, indent=2)
                            except Exception as e:
                                logger.error(f"Error updating GitLab authentication configuration: {str(e)}")
                        
                        return {"Authorization": f"Bearer {access_token}"}
                    else:
                        logger.error(f"Failed to refresh token: {response.status_code} {response.text}")
                        return None
                except Exception as e:
                    logger.error(f"Error refreshing OAuth token: {str(e)}")
                    return None
            else:
                logger.error("OAuth refresh token not found")
                return None
        else:
            logger.error(f"Unknown authentication type: {auth_type}")
            return None
