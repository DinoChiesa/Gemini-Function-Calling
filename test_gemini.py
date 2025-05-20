import requests
import json
import random

BASE_API_URL = "https://generativelanguage.googleapis.com"
TEXT_MODEL_NAME = "gemini-2.5-flash-preview-05-20"

def get_api_key():
    """
    Reads the API key from the '.google-gemini-apikey' file.
    Returns the API key as a string, or None if an error occurs.
    """
    try:
        with open(".google-gemini-apikey", "r") as f:
            api_key = f.read().strip()
        return api_key
    except FileNotFoundError:
        print("Error: API key file '.google-gemini-apikey' not found.")
        return None
    except Exception as e:
        print(f"Error reading API key file: {e}")
        return None

def fetch_models(api_key):
    """
    Fetches models from the Google Generative Language API and prints the JSON response.
    """
    if not api_key:
        return

    url = f"{BASE_API_URL}/v1beta/models?key={api_key}"

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

def generate_content(api_key):
    """
    Generates content using the Google Generative Language API via a POST request
    and prints the JSON response.
    """
    if not api_key:
        return

    url = f"{BASE_API_URL}/v1beta/models/{TEXT_MODEL_NAME}:generateContent?key={api_key}"

    instruction_prompts = [
        {
            "instruction": "You are an expert travel advisor. You are helpful and polite.",
            "prompts": [
                "If someone said <<Expect cool weather when you visit>>, speaking of Seattle in May, what would the expected temperature range be?",
                "If I am visiting Seattle in May, should I rent a car, or would it be better to take public transit and uber/lyft?"
            ]
        },
        {
            "instruction": "You are a nutritionist. You provide matter-of-fact information, and are terse.",
            "prompts": [
                "For a given amount of protein consumption, is it better for me if I consume it earlier in the day, or later in the day? I Want to optimize for absorbtion and satiety.",
                "Should I consider an apple to be a good source of fiber? ",
                "About how many grams of carbohydrate does a medium sized <<Cosmic Crisp>> apple supply?"
            ]
        }
    ]

    selected_scenario = random.choice(instruction_prompts)
    selected_instruction = selected_scenario["instruction"]
    selected_prompt = random.choice(selected_scenario["prompts"])

    payload = {
      "system_instruction": {
        "parts": {
          "text": selected_instruction
        }
      },
      "contents": [
        {
          "role": "user",
          "parts": [
            {
              "text": selected_prompt
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
        print(f"\nGenerating content with model: {TEXT_MODEL_NAME}...")
        print(f"Instruction: {selected_instruction}")
        print(f"Prompt: {selected_prompt}")
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
    api_key_value = get_api_key()
    if api_key_value:
        fetch_models(api_key_value)
        generate_content(api_key_value)
