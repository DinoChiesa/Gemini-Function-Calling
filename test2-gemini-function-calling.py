import requests
import json
import random
import glob
import os
import argparse

from text_utils import REPLACEMENTS, replace_placeholders_in_string, read_text_from_file
from callable_functions import KNOWN_FUNCTIONS

BASE_API_URL = "https://generativelanguage.googleapis.com"
TEXT_MODEL_NAME = "gemini-2.5-flash-preview-05-20"
GEMINI_APIKEY_FILE = ".google-gemini-apikey"

def _select_random_payload(filename_filter=None):
    """
    Selects a random function candidate-*.json file from the config directory,
    optionally filtering by a string in the filename.
    Loads its JSON content, and returns the payload and the selected file path.
    Returns (None, None) if an error occurs.
    """
    try:
        config_dir_path = "config"
        file_pattern = "fn-*.json"
        search_path = os.path.join(config_dir_path, file_pattern)

        all_candidate_files = glob.glob(search_path)
        if not all_candidate_files:
            print(f"No '{file_pattern}' files found in the '{config_dir_path}' directory.")
            return None, None

        if filename_filter:
            filtered_files = [f for f in all_candidate_files if filename_filter in os.path.basename(f)]
            if not filtered_files:
                print(f"No '{file_pattern}' files containing '{filename_filter}' found in '{config_dir_path}'.")
                return None, None
            selected_file_path = random.choice(filtered_files)
        else:
            selected_file_path = random.choice(all_candidate_files)
        print(f"\nSelected function calling payload file: {selected_file_path}")

        with open(selected_file_path, "r") as f:
            payload_str = f.read()

        payload_str = replace_placeholders_in_string(payload_str, REPLACEMENTS)

        payload = json.loads(payload_str) # Convert back to Python object
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

def invoke_with_function_calling(api_key, verbose=False):
    """
    Gets a random function calling payload, sends its content to the
    Gemini API, and returns a list of extracted function calls.
    Each item in the list is a dictionary with "name" and "arguments".
    If verbose is True, logs full request and response payloads.
    """
    if not api_key:
        return []

    payload, selected_file_path = _select_random_payload(filename_filter=kwargs.get('filename_filter'))
    if not payload:
        return []

    url = f"{BASE_API_URL}/v1beta/models/{TEXT_MODEL_NAME}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"Starting iterative function calling with payload from: {selected_file_path}...")

        # `payload` is the original full payload used for the first call.
        # `ongoing_contents_list` will accumulate parts for subsequent calls.
        # It starts with the user's initial prompt.
        ongoing_contents_list = list(payload.get("contents", []))

        # `current_payload_for_api_call` will be the payload sent in each iteration.
        # For the first iteration, it's the initial payload.
        current_payload_for_api_call = payload
        initial_prompt_text = _get_text_from_payload(payload, type="initial_prompt")
        current_api_response_json = None
        last_processed_api_response_json = None

        max_iterations = 10
        for iteration_num in range(max_iterations):
            print(f"\n--- Iteration {iteration_num + 1} of up to {max_iterations} ---")

            # Make the API call
            response_iter = None
            try:
                print(f"Making API call for iteration {iteration_num + 1}...")
                if verbose:
                    print("Request Payload:")
                    print(json.dumps(current_payload_for_api_call, indent=2, ensure_ascii=False))
                response_iter = requests.post(url, json=current_payload_for_api_call, headers=headers)
                response_iter.raise_for_status()
                current_api_response_json = response_iter.json()
                last_processed_api_response_json = current_api_response_json
                print(f"Response from API received.")
                if verbose:
                    print("Response Payload:")
                    print(json.dumps(current_api_response_json, indent=2, ensure_ascii=False))
            except requests.exceptions.RequestException as e_req_iter:
                print(f"RequestException during API call: {e_req_iter}")
                if response_iter is not None: print(f"Response content: {response_iter.text}")
                break # Exit loop on API error
            except json.JSONDecodeError as e_json_iter:
                print(f"JSONDecodeError during API call: {e_json_iter}")
                break # Exit loop on API error

            extracted_api_calls = extract_function_calls_from_response(current_api_response_json)

            if not extracted_api_calls:
                print("No function calls found in the latest API response. Halting iteration.")
                break

            model_content_part = None
            if current_api_response_json.get("candidates"):
                candidate = current_api_response_json["candidates"][0]
                if "content" in candidate:
                    model_content_part = candidate["content"]

            # Append the model's response (that contained function calls) to ongoing_contents_list
            # Only if it's not the very first iteration's user prompt (which is already there)
            if model_content_part and (iteration_num > 0 or ongoing_contents_list != [model_content_part]):
                 # Check to avoid duplicating the model's response if it was already added.
                 # This logic might need refinement based on exact desired accumulation behavior.
                if not any(part == model_content_part for part in ongoing_contents_list):
                    ongoing_contents_list.append(model_content_part)
            elif not model_content_part:
                print("Warning: Could not find model's content part in the current response to append.")

            function_tool_response_parts = execute_and_format_tool_calls(extracted_api_calls, KNOWN_FUNCTIONS)

            tool_response_section = {"role": "tool", "parts": function_tool_response_parts}
            ongoing_contents_list.append(tool_response_section)

            if iteration_num == max_iterations - 1:
                print("\nMax iterations reached. The current response is considered final.")
                break

            # Prepare payload for the next iteration
            next_api_call_payload_parts = {
                "contents": ongoing_contents_list,
                "tools": payload.get("tools"), # Use original tools definition
                "generation_config": payload.get("generation_config"), # Use original gen config
                "system_instruction": payload.get("system_instruction") # Use original system instruction
            }
            current_payload_for_api_call = {k: v for k, v in next_api_call_payload_parts.items() if v is not None}

        print("\n--- Iterative Function Calling Process Ended ---")
        if last_processed_api_response_json:
            print("Final API Response (or last successfully processed response):")
            print(json.dumps(last_processed_api_response_json, indent=2, ensure_ascii=False))

            final_response_text = _get_text_from_payload(last_processed_api_response_json, type="final_response")

            print("\n--- Summary ---")
            if initial_prompt_text:
                print(f"Initial Prompt: {initial_prompt_text}")
            else:
                print("Initial Prompt: Could not extract.")

            if final_response_text:
                print(f"Final Response Text: {final_response_text}")
            else:
                print("Final Response Text: Could not extract or not a text response.")
            print("\n")
        else:
            print("No API response was successfully processed to be displayed as final.")

    except Exception as e: # Catch-all for other unexpected errors during setup
        print(f"An unexpected error occurred in invoke_with_function_calling: {e}")



def _get_text_from_payload(data, type="initial_prompt"):
    """Safely extracts text from payload structures."""
    try:
        if type == "initial_prompt":
            return data["contents"][0]["parts"][0]["text"]
        elif type == "final_response":
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except (IndexError, KeyError, TypeError):
        return None
    return None


def execute_and_format_tool_calls(extracted_api_calls, known_functions_map):
    """
    Executes local functions based on extracted API calls and formats their responses.

    Args:
        extracted_api_calls: A list of function call objects from the API.
        known_functions_map: A dictionary mapping function names to callable functions.

    Returns:
        A list of formatted function response parts for the API.
    """
    function_tool_response_parts = []
    if not extracted_api_calls:
        return function_tool_response_parts

    print(f"\nExecuting {len(extracted_api_calls)} extracted function call(s):")
    for fc_from_api in extracted_api_calls:
        function_name = fc_from_api.get("name")
        if function_name in known_functions_map:
            target_function = known_functions_map[function_name]
            args_dict = fc_from_api.get("args")
            arg_values = list(args_dict.values()) if args_dict and isinstance(args_dict, dict) else []

            try:
                result = target_function(*arg_values)
                args_repr = ", ".join(f"'{str(arg)}'" for arg in arg_values)
                print(f"Result of local {function_name}({args_repr}): {result}")

                response_content_for_tool = args_dict.copy() if args_dict else {}
                if function_name == "get_max_scrabble_word_score": response_content_for_tool["score"] = result
                elif function_name == "get_is_known_word": response_content_for_tool["is_known"] = result
                else: response_content_for_tool["result"] = result

                function_tool_response_parts.append({
                    "functionResponse": {"name": function_name, "response": {"content": response_content_for_tool}}
                })
            except TypeError as e_type: print(f"TypeError calling local {function_name} with {arg_values}: {e_type}")
            except Exception as e_exc: print(f"Error calling local {function_name} with {arg_values}: {e_exc}")
        else:
            print(f"Function '{function_name}' is not a known invokable function.")
    return function_tool_response_parts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script for Gemini API function calling. Verbose logging is on by default.")
    parser.add_argument("--quiet", action="store_true", help="Disable verbose logging of API requests and responses.")
    parser.add_argument("--filter", type=str, help="Filter payload files by a string contained in their filename.")
    args = parser.parse_args()

    api_key_value = read_text_from_file(GEMINI_APIKEY_FILE, "Google Gemini API key")
    if api_key_value:
        invoke_with_function_calling(api_key_value, verbose=(not args.quiet), filename_filter=args.filter)
    else:
        print(f"No gemini API key found in '{GEMINI_APIKEY_FILE}'. Cannot continue.")
