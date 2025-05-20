import requests
import json

def fetch_models():
    """
    Fetches models from the Google Generative Language API and prints the JSON response.
    The API key is read from the '.google-gemini-apikey' file.
    """
    try:
        with open(".google-gemini-apikey", "r") as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print("Error: API key file '.google-gemini-apikey' not found.")
        return
    except Exception as e:
        print(f"Error reading API key file: {e}")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Assuming the response is JSON, parse it and print
        models_data = response.json()
        print(json.dumps(models_data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except json.JSONDecodeError:
        print("Failed to decode JSON from response.")

if __name__ == "__main__":
    fetch_models()
