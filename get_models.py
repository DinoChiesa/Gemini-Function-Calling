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

def generate_content():
    """
    Generates content using the Google Generative Language API via a POST request
    and prints the JSON response.
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

    model_name = "gemini-2.5-flash-preview-05-20"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
      "system_instruction": {
        "parts": {
          "text": "You are an expert travel advisor. You are helpful and polite."
        }
      },
      "contents": [
        {
          "role": "user",
          "parts": [
            {
              "text": "If someone said <<Expect cool weather when you visit>>, speaking of Seattle in May, what would the expected temperature range be?"
            }
          ]
        }
      ],
      "generation_config": {
        "temperature": 1,
        "topP": 1
      }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"\nGenerating content with model: {model_name}...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Assuming the response is JSON, parse it and print
        content_data = response.json()
        print(json.dumps(content_data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during content generation: {e}")
        if response is not None:
            print(f"Response content: {response.text}")
    except json.JSONDecodeError:
        print("Failed to decode JSON from content generation response.")

if __name__ == "__main__":
    fetch_models()
    generate_content()
