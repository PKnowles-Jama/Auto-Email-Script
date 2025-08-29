import requests
from requests.auth import HTTPBasicAuth

# Global variables to store the active session and CSRF token
# This is a less ideal pattern but required for the original GUI structure.
# Returning the values is the preferred method as implemented below.
_active_session = None
_active_csrf_token = None

def LoginFunction(basic_oauth, jama_username, jama_password, jama_base_url_v1):
    """
    Authenticates with a Jama Connect instance and returns a requests.Session object
    and a CSRF token for making subsequent API calls.
    
    Args:
        basic_oauth (str): 'basic' or 'oauth'
        jama_username (str): username or client ID
        jama_password (str): password or client secret
        jama_base_url_v1 (str): e.g. https://yourjamainstance.com/rest/v1/
    
    Returns:
        tuple: (requests.Session, str) for success, (None, None) otherwise.
    """
    print(f"\nAttempting to authenticate with Jama Connect using {basic_oauth.upper()}...")
    session = requests.Session()
    
    if basic_oauth == 'basic':
        auth = HTTPBasicAuth(jama_username, jama_password)
        session.auth = auth
    elif basic_oauth == 'oauth':
        client_id = jama_username
        client_secret = jama_password
        token_url = f"{jama_base_url_v1.rstrip('v1/')}/rest/oauth/token"
        
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
        except requests.exceptions.HTTPError as e:
            print(f"OAuth 2.0 authentication failed. Please check your client ID and secret.")
            print(f"Error: {e}")
            return None, None
        except Exception as e:
            print(f"An unexpected error occurred during OAuth authentication: {e}")
            return None, None
    else:
        print("Invalid 'basic_oauth' value. Please use 'basic' or 'oauth'.")
        return None, None

    json_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Final check: test the session with a call to the /projects endpoint
    test_url = f"{jama_base_url_v1.rstrip('/')}/projects"
    try:
        response = session.get(test_url, headers=json_headers)
        response.raise_for_status()
        
        # Extract CSRF token from the response header
        csrf_token = response.cookies.get('JSESSIONID')
        if not csrf_token:
            print("Warning: No CSRF token found in session cookies. API calls may fail.")

        print("Authentication successful! 🎉")
        print("Authentication complete. Ready to fetch attachments.")
        return session, csrf_token
    except requests.exceptions.HTTPError as e:
        print(f"Authentication failed. Please check your credentials.")
        print(f"Error: {e}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None