import requests
from requests.auth import HTTPBasicAuth

def LoginFunction(basic_oauth, jama_username, jama_password, jama_base_url_v2):
    # This function is used to authenticate/login to a specified Jama Connect instance with either Basic or oAuth credentials
    #   basic_oauth = string equal to basic or oauth, used to determine authentication type
    #   jama_username = string, username or client ID
    #   jama_password = string, password or client secret
    #   jama_base_url_v2 = string, i.e. https://yourjamainstance.com/rest/v2/

    # OAUTH NOT CURRENTLY WORKING FOR SOME REASON!

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

        except requests.exceptions.HTTPError as e:
            print(f"OAuth 2.0 authentication failed. Please check your client ID and secret.")
            print(f"Error: {e}")

        except Exception as e:
            print(f"An unexpected error occurred during OAuth authentication: {e}")

    else:
        print("Invalid 'basic_oauth' value. Please use 'basic' or 'oauth'.")

    json_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    multipart_headers = {
        "Accept": "application/json",
    }

    test_url = f"{jama_base_url_v2.rstrip('/')}/projects"
    try:
        response = session.get(test_url, headers=json_headers)
        response.raise_for_status()
        print("Authentication successful! 🎉")
    except requests.exceptions.HTTPError as e:
        print(f"Authentication failed. Please check your credentials.")
        print(f"Error: {e}")
        exit()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit()

    print("\nAuthentication complete. Ready to fetch attachments.")