import requests
import json

def get_is_known_word(*args):
    """
    Checks the online dictionary to determine if the candidate is an actual word."
    Expects the candidate word as the first argument.
    """
    if not args:
        print("Error: get_is_known_word expects at least one argument (candidate word).")
        return False
    candidate = args[0]

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{candidate}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            # Optionally, you might still want to see the JSON response for a known word
            # models_data = response.json()
            # print(json.dumps(models_data, indent=2))
            return True
        elif response.status_code == 404:
            return False
        else:
            # For any other status code, print a message and then raise the exception
            print(f"Unexpected status code {response.status_code} for word '{candidate}': {response.text}")
            response.raise_for_status() # This will re-throw an HTTPError for other bad statuses

    except requests.exceptions.RequestException as e:
        # This will catch the re-thrown error from response.raise_for_status()
        # or other network-related errors from requests.get()
        print(f"An error occurred while checking word '{candidate}': {e}")
        return False # Or re-raise, depending on desired error handling for network issues
    except json.JSONDecodeError:
        # This might occur if a 200 response isn't valid JSON, though less likely for this API
        print(f"Failed to decode JSON from response for word '{candidate}'.")
        return False

def get_max_scrabble_word_score(*args):
    """
    Calculates a score for a word based on character values.
    Expects the word as the first argument.
    - Non-ASCII characters result in a score of 0.
    - 'X' or 'Y' (uppercase) = 5 points
    - 'E', 'S', 'T', 'A' (uppercase) = 1 point
    - Other ASCII characters = 2 points
    """
    if not args:
        print("Error: get_max_scrabble_word_score expects at least one argument (word).")
        return 0
    word = args[0]

    total_score = 0

    for char_original in word:
        char_upper = char_original.upper()
        if not char_upper.isascii():
            return 0  # Stop and return 0 if non-ASCII character is found

        if char_upper in ('X', 'Y'):
            total_score += 5
        elif char_upper in ('E', 'S', 'T', 'A'):
            total_score += 1
        else:
            total_score += 2

    # Add bonus points for word length over 9 characters
    if len(word) > 9:
        bonus_points = len(word) - 9
        total_score += bonus_points

    return total_score

KNOWN_FUNCTIONS = {
    "get_max_scrabble_word_score": get_max_scrabble_word_score,
    "get_is_known_word": get_is_known_word,
    # Add other known functions here as they are defined
}
