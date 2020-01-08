"""
Xero SDK connection base class
"""

import base64
import json

import requests

from .apis import *
from .exceptions import *


class XeroSDK:
    """
    Creates connection with Xero APIs using OAuth2 authentication

    Parameters:
        base_url (str): Base URL for Xero API
        client_id (str): Client ID for Xero API
        client_secret (str): Client Secret for Xero API
        refresh_token (str): Refresh token for Xero API
    """

    TOKEN_URL = "https://identity.xero.com/connect/token"
    AUTHORIZE_URL = "https://login.xero.com/identity/connect/authorize"
    CONNECTIONS_URL = "https://api.xero.com/connections"

    def __init__(self, base_url, client_id, client_secret, refresh_token):
        # Store the input parameters
        self.__base_url = base_url
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__refresh_token = refresh_token

        # Create an object for each API
        self.Invoices = Invoices()
        self.Accounts = Accounts()
        self.Contacts = Contacts()
        self.TrackingCategories = TrackingCategories()

        # Set the server url
        self.set_server_url()

        # Refresh access token
        self.refresh_access_token()

    def set_server_url(self):
        """
        Set server URL for all API objects
        """

        base_url = self.__base_url

        self.Invoices.set_server_url(base_url)
        self.Accounts.set_server_url(base_url)
        self.Contacts.set_server_url(base_url)
        self.TrackingCategories.set_server_url(base_url)

    def set_tenant_id(self, tenant_id):
        """
        Set tenant id for all API objects

        Parameters:
            tenant_id (str): Xero tenant ID
        """

        self.Invoices.set_tenant_id(tenant_id)
        self.Accounts.set_tenant_id(tenant_id)
        self.Contacts.set_tenant_id(tenant_id)
        self.TrackingCategories.set_tenant_id(tenant_id)

    def refresh_access_token(self):
        """
        Refresh access token for each API objects
        """

        access_token = self.__get_access_token()

        self.Invoices.change_access_token(access_token)
        self.Accounts.change_access_token(access_token)
        self.Contacts.change_access_token(access_token)
        self.TrackingCategories.change_access_token(access_token)

        # Get tenant ID
        self.__get_tenant_id(access_token)

    def __get_access_token(self):
        """
        Get access token from Xero TOKEN_URL

        Returns:
            A new access token
        """

        api_headers = {
            "authorization": "Basic " + str(
                base64.b64encode(
                    (self.__client_id + ":" + self.__client_secret).encode("utf-8")
                ), "utf-8"
            ),
        }
        api_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.__refresh_token
        }
        response = requests.post(XeroSDK.TOKEN_URL, headers=api_headers, data=api_data)

        if response.status_code == 200:
            token = json.loads(response.text)
            return token["access_token"]

        error_msg = json.loads(response.text)["error"]
        if response.status_code == 400:
            if error_msg == "invalid_client":
                raise InvalidClientError(
                    'Invalid client ID or client secret or refresh token'
                )

            if error_msg == "invalid_grant":
                raise InvalidGrant(
                    'Invalid refresh token'
                )

            if error_msg == "unsupported_grant_type":
                raise UnsupportedGrantType(
                    'Invalid or non-existing grant type in request body'
                )

            raise XeroSDKError(
                response.text, response.status_code
            )

        if response.status_code == 500:
            raise InternalServerError(
                'Internal server error'
            )

        raise XeroSDKError(
            response.text, response.status_code
        )

    def __get_tenant_id(self, access_token):
        """
        Get connected tenant ID from new access token

        Parameters:
            access_token (str): New access token
        """

        api_headers = {
            "authorization": "Bearer " + access_token,
        }
        response = requests.get(XeroSDK.CONNECTIONS_URL, headers=api_headers)

        if response.status_code == 200:
            connections = json.loads(response.text)
            tenant_id = connections[0]["tenantId"]

            # Set tenant ID
            self.set_tenant_id(tenant_id)

        elif response.status_code == 401:
            raise InvalidTokenError(
                'Invalid or non-existing access token'
            )
        elif response.status_code == 500:
            raise InternalServerError(
                'Internal server error'
            )
        else:
            raise XeroSDKError(
                response.text, response.status_code
            )
