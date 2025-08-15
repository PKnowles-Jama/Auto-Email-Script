import requests
from requests.auth import HTTPBasicAuth

def LoginFunction(basic_oauth, jama_username, jama_password, jama_base_url_v2):
    """
    Authenticates with a Jama Connect instance and returns True for success or False for failure.
    
    Args:
        basic_oauth (str): 'basic' or 'oauth'
        jama_username (str): username or client ID
        jama_password (str): password or client secret
        jama_base_url_v2 (str): e.g. https://yourjamainstance.com/rest/v2/
    
    Returns:
        bool: True if authentication is successful, False otherwise.
    """
    print(f"\nAttempting to authenticate with Jama Connect using {basic_oauth.upper()}...")
    session = requests.Session()
    
    if basic_oauth == 'basic':
        auth = HTTPBasicAuth(jama_username, jama_password)
        session.auth = auth
    elif basic_oauth == 'oauth':
        client_id = jama_username
        client_secret = jama_password
        token_url = f"{jama_base_url_v2.rstrip('/')}/rest/oauth/token"
        
        try:
            # Get the access token
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            token = response.json().get('access_token')
            
            session.headers.update({"Authorization": f"Bearer {token}"})
            print("OAuth 2.0 authentication successful! 🎉")
            # Note: We don't exit here, we continue to the next check.

        except requests.exceptions.HTTPError as e:
            print(f"OAuth 2.0 authentication failed. Please check your client ID and secret.")
            print(f"Error: {e}")
            return False # Return False on failure
        except Exception as e:
            print(f"An unexpected error occurred during OAuth authentication: {e}")
            return False # Return False on failure
    else:
        print("Invalid 'basic_oauth' value. Please use 'basic' or 'oauth'.")
        return False # Return False for invalid input

    json_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # This multipart_headers is not used in the provided code, so it is commented out for clarity.
    # multipart_headers = {
    #     "Accept": "application/json",
    # }

    # Final check: test the session with a call to the /projects endpoint
    test_url = f"{jama_base_url_v2.rstrip('/')}/projects"
    try:
        response = session.get(test_url, headers=json_headers)
        response.raise_for_status()
        print("Authentication successful! 🎉")
        print("Authentication complete. Ready to fetch attachments.")
        return True # Return True on final success
    except requests.exceptions.HTTPError as e:
        print(f"Authentication failed. Please check your credentials.")
        print(f"Error: {e}")
        return False # Return False on failure
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False # Return False on failure