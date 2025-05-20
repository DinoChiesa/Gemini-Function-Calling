import requests
import json
import random
import glob
import os

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
        response.raise_for_status()
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
                "If someone tells me <<Expect cool weather when you visit>>, speaking of Seattle in May, what would the expected temperature range be?",
                "If I am visiting Seattle in June (I will be flying in), should I rent a car, or would it be better to take public transit and uber/lyft?"
            ]
        },
        {
            "instruction": "You are a nutritionist. You provide matter-of-fact information, in your thorough, explanatory answers.",
            "prompts": [
                "For a given amount of protein consumption, is it better for me if I consume it earlier in the day, or later in the day? I Want to optimize for absorbtion and satiety.",
                "Should I consider an apple to be a good source of fiber? How much fiber should a healthy adult consume ddaily?",
                "About how many grams of carbohydrate does a medium sized <<Cosmic Crisp>> apple supply? About how many carbs would a normal 2500-calorie diet include?",
                "What are the macro ratios I should shoot for in my daily diet, if I'm a normal healty adult male?"
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
        response.raise_for_status()
        content_data = response.json()
        print(json.dumps(content_data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during content generation: {e}")
        if response is not None:
            print(f"Response content: {response.text}")
    except json.JSONDecodeError:
        print("Failed to decode JSON from content generation response.")

def get_random_function_calling_payload():
    """
    Selects a random function-candidate-*.json file from the current directory,
    loads its JSON content, and returns the payload and the selected file path.
    Returns (None, None) if an error occurs.
    """
    try:
        candidate_files = glob.glob("function-candidate-*.json")
        if not candidate_files:
            print("No 'function-candidate-*.json' files found in the current directory.")
            return None, None

        selected_file_path = random.choice(candidate_files)
        print(f"\nSelected function calling payload file: {selected_file_path}")

        with open(selected_file_path, "r") as f:
            payload = json.load(f)
        return payload, selected_file_path

    except FileNotFoundError:
        # This case should ideally not be reached if glob.glob worked and random.choice selected a valid file
        print(f"Error: File {selected_file_path} not found after selection.")
        return None, None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {selected_file_path}.")
        return None, None
    except Exception as e:
        print(f"An error occurred while selecting or loading the payload: {e}")
        return None, None

def extract_function_calls_from_response(response_data):
    """
    Extracts function call details from the Gemini API response.
    Returns a list of functionCall objects directly from the response.
    """
    extracted_function_calls = []
    if "candidates" in response_data:
        for candidate in response_data.get("candidates", []):
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"].get("parts", []):
                    if "functionCall" in part:
                        extracted_function_calls.append(part["functionCall"])
    return extracted_function_calls

def invoke_with_function_calling(api_key):
    """
    Gets a random function calling payload, sends its content to the
    Gemini API, and returns a list of extracted function calls.
    Each item in the list is a dictionary with "name" and "arguments".
    """
    if not api_key:
        return []

    payload, selected_file_path = get_random_function_calling_payload()
    if not payload:
        return []

    url = f"{BASE_API_URL}/v1beta/models/{TEXT_MODEL_NAME}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"Invoking model with function calling payload from: {selected_file_path}...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        content_data = response.json()
        # print(json.dumps(content_data, indent=2)) # Original print of full response

        return extract_function_calls_from_response(content_data)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during function calling invocation: {e}")
        if response is not None:
            print(f"Response content: {response.text}")
        return []
    except json.JSONDecodeError:
        print("Failed to decode JSON from function calling response.")
        return []

from callable_functions import KNOWN_FUNCTIONS

if __name__ == "__main__":
    api_key_value = get_api_key()
    if api_key_value:
        function_calls = invoke_with_function_calling(api_key_value)
        if function_calls:
            print("\nExtracted Function Calls:")
            for fc in function_calls:
                print(json.dumps(fc, indent=2))
                function_name = fc.get("name")

                if function_name in KNOWN_FUNCTIONS:
                    target_function = KNOWN_FUNCTIONS[function_name]
                    args = fc.get("args")

                    # AI! Modify this code to ignore the name of the argument.
                    # Just invoke the functions with the list of arguments provided in
                    # the fc item. 
                    if args and "candidate" in args: # Common argument key for both current functions
                        candidate_arg = args["candidate"]
                        try:
                            result = target_function(candidate_arg)
                            print(f"Result of {function_name}('{candidate_arg}'): {result}")
                        except Exception as e:
                            print(f"Error calling {function_name} with '{candidate_arg}': {e}")
                    else:
                        print(f"Could not call {function_name}, 'args' or 'candidate' key missing: {args}")
                # else:
                #     print(f"Function '{function_name}' is not a known invokable function.")
        else:
            print("\nNo function calls extracted or an error occurred.")
        # fetch_models(api_key_value)
        # for _ in range(3):
        #    generate_content(api_key_value)
