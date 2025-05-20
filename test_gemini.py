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
        content_data_first_response = response.json()
        # print(json.dumps(content_data_first_response, indent=2)) # Original print of full response

        original_payload_contents = payload.get("contents", [])
        model_content_from_first_response = None
        if content_data_first_response.get("candidates"):
            first_candidate = content_data_first_response["candidates"][0]
            if "content" in first_candidate:
                model_content_from_first_response = first_candidate["content"]

        extracted_api_calls = extract_function_calls_from_response(content_data_first_response)

        if extracted_api_calls:
            print("\nExtracted Function Calls from 1st response:")
            function_tool_response_parts = [] # For the "parts" array of the tool response

            for fc_from_api in extracted_api_calls:
                print(json.dumps(fc_from_api, indent=2))
                function_name = fc_from_api.get("name")

                if function_name in KNOWN_FUNCTIONS:
                    target_function = KNOWN_FUNCTIONS[function_name]
                    args_dict = fc_from_api.get("args")
                    arg_values = []

                    if args_dict is not None and isinstance(args_dict, dict):
                        arg_values = list(args_dict.values())
                    
                    try:
                        result = target_function(*arg_values)
                        args_repr = ", ".join(f"'{str(arg)}'" for arg in arg_values)
                        print(f"Result of local {function_name}({args_repr}): {result}")

                        # Construct the content for the functionResponse part
                        response_content_for_tool = args_dict.copy() if args_dict else {}
                        if function_name == "get_max_scrabble_word_score":
                            response_content_for_tool["score"] = result
                        elif function_name == "get_is_known_word":
                            response_content_for_tool["is_known"] = result
                        else: # Generic result key if not specifically handled
                            response_content_for_tool["result"] = result
                        
                        function_tool_response_parts.append({
                            "functionResponse": {
                                "name": function_name,
                                "response": {
                                    "content": response_content_for_tool
                                }
                            }
                        })
                    except TypeError as e:
                        print(f"TypeError calling local function {function_name} with arguments {arg_values}: {e}")
                    except Exception as e:
                        print(f"Error calling local function {function_name} with arguments {arg_values}: {e}")
                # else: (function_name not in KNOWN_FUNCTIONS)
                #     print(f"Function '{function_name}' is not a known invokable function.")
            
            # Proceed to 2nd API call if there were successful local function calls that generated parts
            if function_tool_response_parts:
                second_payload_contents = list(original_payload_contents) # Start with original user content

                if model_content_from_first_response: # Add model's response (that contained function calls)
                    second_payload_contents.append(model_content_from_first_response)
                
                # Add the tool execution results
                second_payload_contents.append({
                    "role": "tool",
                    "parts": function_tool_response_parts
                })

                second_api_payload = {}
                if "tools" in payload:
                    second_api_payload["tools"] = payload["tools"]
                if "generation_config" in payload:
                    second_api_payload["generation_config"] = payload["generation_config"]
                if "system_instruction" in payload:
                     second_api_payload["system_instruction"] = payload["system_instruction"]
                second_api_payload["contents"] = second_payload_contents
                
                print("\nMaking 2nd API call with augmented payload:")
                print(json.dumps(second_api_payload, indent=2,ensure_ascii=False))

                try:
                    response_second = requests.post(url, json=second_api_payload, headers=headers)
                    response_second.raise_for_status()
                    content_data_second = response_second.json()
                    print("\nResponse from 2nd API call:")
                    print(json.dumps(content_data_second, indent=2,ensure_ascii=False))
                except requests.exceptions.RequestException as e_second:
                    print(f"An error occurred during the 2nd API call: {e_second}")
                    if response_second is not None:
                        print(f"Response content: {response_second.text}")
                except json.JSONDecodeError as e_json_second:
                    print(f"Failed to decode JSON from the 2nd API call response: {e_json_second}")
            else:
                print("\nNo successful local function calls or results to form a 2nd API request.")
        else:
            print("\nNo function calls extracted from 1st response, skipping 2nd API call.")
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the 1st API call: {e}")
        if 'response' in locals() and response is not None: # check if response variable exists
            print(f"Response content: {response.text}")
        return [] # Return empty list as per original error handling
    except json.JSONDecodeError:
        print("Failed to decode JSON from the 1st API call response.")
        return [] # Return empty list as per original error handling

from callable_functions import KNOWN_FUNCTIONS

if __name__ == "__main__":
    api_key_value = get_api_key()
    if api_key_value:
        invoke_with_function_calling(api_key_value)
        # fetch_models(api_key_value)
        # for _ in range(3):
        #    generate_content(api_key_value)
