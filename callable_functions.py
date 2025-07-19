# Copyright © 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import os

import requests

from text_utils import read_text_from_file

TOMTOM_BASE_URL = "https://api.tomtom.com"
WEATHER_GOV_BASE_URL = "https://api.weather.gov"
WEATHER_GOV_USER_AGENT = "python test_gemini"
TOMTOM_APIKEY = os.environ.get("TOMTOM_APIKEY", "")


def get_weather_forecast(*args):
    """
    Fetches weather forecast for a given placename.
    Expects placename (e.g., "Chicago, IL") as the first argument.
    Returns a dict with "temperature" and "periodName", or an error dict.
    """
    if not args:
        error_msg = (
            "Error: get_weather_forecast expects at least one argument (placename)."
        )
        print(error_msg)
        return {"error": error_msg}
    placename = args[0]

    if not TOMTOM_APIKEY:
        return {
            "error": "TomTom API key is missing or could not be read from environment TOMTOM_APIKEY."
        }

    # 1. Get Lat/Lon from TomTom
    geocode_url = f"{TOMTOM_BASE_URL}/search/2/geocode/{requests.utils.quote(placename)}.json?key={TOMTOM_APIKEY}"
    latitude = None
    longitude = None

    try:
        print(f"Fetching geocode for '{placename}' from TomTom...")
        response_geocode = requests.get(geocode_url)
        response_geocode.raise_for_status()
        geocode_data = response_geocode.json()

        if not geocode_data.get("results"):
            error_msg = f"No geocoding results found for '{placename}'."
            print(error_msg)
            return {"error": error_msg}

        position = geocode_data["results"][0].get("position")
        if not position or "lat" not in position or "lon" not in position:
            error_msg = (
                f"Could not extract lat/lon from TomTom response for '{placename}'."
            )
            print(error_msg)
            return {"error": error_msg}

        latitude = position["lat"]
        longitude = position["lon"]
        print(f"Got lat/lon: {latitude}, {longitude}")

    except requests.exceptions.RequestException as e:
        error_msg = f"TomTom API request failed for '{placename}': {e}"
        print(error_msg)
        return {"error": error_msg, "details": str(e)}
    except json.JSONDecodeError:
        error_msg = f"Failed to decode JSON from TomTom API for '{placename}'."
        print(error_msg)
        return {"error": error_msg}
    except (KeyError, IndexError) as e:
        error_msg = (
            f"Unexpected structure in TomTom API response for '{placename}': {e}"
        )
        print(error_msg)
        return {"error": error_msg, "details": str(e)}

    # 2. Get Weather.gov forecast office URL
    points_url = f"{WEATHER_GOV_BASE_URL}/points/{latitude},{longitude}"
    weather_headers = {"User-Agent": WEATHER_GOV_USER_AGENT}
    forecast_grid_data_url = None

    try:
        print(f"Fetching weather points for {latitude},{longitude} from Weather.gov...")
        response_points = requests.get(
            points_url, headers=weather_headers, allow_redirects=False
        )  # Handle redirect manually

        if response_points.status_code == 301:  # Handle redirect
            redirect_url = response_points.headers.get("Location")
            if not redirect_url:
                error_msg = "Weather.gov points API redirected (301) but no Location header found."
                print(error_msg)
                return {"error": error_msg}
            print(f"Redirected to: {redirect_url}")
            if not redirect_url.startswith("https://"):
                print(
                    f"Redirect URL '{redirect_url}' is not fully qualified. Prepending WEATHER_GOV_BASE_URL."
                )
                redirect_url = f"{WEATHER_GOV_BASE_URL}{redirect_url}"  # Ensure no double slashes if redirect_url starts with /
                if not redirect_url.startswith(
                    f"{WEATHER_GOV_BASE_URL}/"
                ) and redirect_url.startswith(
                    f"{WEATHER_GOV_BASE_URL}"
                ):  # if it became https://api.weather.govrelative/path
                    redirect_url = redirect_url.replace(
                        f"{WEATHER_GOV_BASE_URL}", f"{WEATHER_GOV_BASE_URL}/", 1
                    )

            response_points = requests.get(redirect_url, headers=weather_headers)

        response_points.raise_for_status()
        points_data = response_points.json()

        forecast_grid_data_url = points_data.get("properties", {}).get("forecast")
        if not forecast_grid_data_url:
            error_msg = "Could not find 'properties.forecast' URL in Weather.gov points response."
            print(error_msg)
            return {"error": error_msg}
        print(f"Got forecast grid data URL: {forecast_grid_data_url}")

    except requests.exceptions.RequestException as e:
        error_msg = f"Weather.gov points API request failed: {e}"
        print(error_msg)
        return {"error": error_msg, "details": str(e)}
    except json.JSONDecodeError:
        error_msg = "Failed to decode JSON from Weather.gov points API."
        print(error_msg)
        return {"error": error_msg}
    except (KeyError, IndexError) as e:
        error_msg = f"Unexpected structure in Weather.gov points API response: {e}"
        print(error_msg)
        return {"error": error_msg, "details": str(e)}

    # 3. Get actual forecast
    try:
        print(f"Fetching actual forecast from: {forecast_grid_data_url}...")
        response_forecast = requests.get(
            forecast_grid_data_url, headers=weather_headers
        )
        response_forecast.raise_for_status()
        forecast_data = response_forecast.json()

        periods = forecast_data.get("properties", {}).get("periods")
        if not periods or not isinstance(periods, list) or len(periods) == 0:
            error_msg = "No forecast periods found in Weather.gov forecast response."
            print(error_msg)
            return {"error": error_msg}

        first_period = periods[0]
        temperature = first_period.get("temperature")
        period_name = first_period.get("name")

        if temperature is None or period_name is None:
            error_msg = "Could not extract temperature or period name from forecast."
            print(error_msg)
            return {
                "error": error_msg,
                "details": "Missing 'temperature' or 'name' in first period.",
            }

        print(f"Forecast for '{placename}': {period_name} - {temperature}F")
        return {"temperature": temperature, "periodName": period_name}

    except requests.exceptions.RequestException as e:
        error_msg = f"Weather.gov forecast API request failed: {e}"
        print(error_msg)
        return {"error": error_msg, "details": str(e)}
    except json.JSONDecodeError:
        error_msg = "Failed to decode JSON from Weather.gov forecast API."
        print(error_msg)
        return {"error": error_msg}
    except (KeyError, IndexError) as e:
        error_msg = f"Unexpected structure in Weather.gov forecast API response: {e}"
        print(error_msg)
        return {"error": error_msg, "details": str(e)}


def get_min_scrabble_word_score(*args):
    """
    Calculates a Scrabble score for a word based on standard letter values.
    Expects the word as the first argument.
    - Non-ASCII characters result in a score of 0.
    - Bonus of 1 point for each character over 9.
    Letter scores:
    (1 point) - A, E, I, L, N, O, R, S, T, U
    (2 points) - D, G
    (3 points) - B, C, M, P
    (4 points) - F, H, V, W, Y
    (5 points) - K
    (8 points) - J, X
    (10 points) - Q, Z
    """
    if not args:
        print(
            "Error: get_min_scrabble_word_score expects at least one argument (word)."
        )
        return 0
    word = args[0]

    letter_scores = {
        "A": 1,
        "E": 1,
        "I": 1,
        "L": 1,
        "N": 1,
        "O": 1,
        "R": 1,
        "S": 1,
        "T": 1,
        "U": 1,
        "D": 2,
        "G": 2,
        "B": 3,
        "C": 3,
        "M": 3,
        "P": 3,
        "F": 4,
        "H": 4,
        "V": 4,
        "W": 4,
        "Y": 4,
        "K": 5,
        "J": 8,
        "X": 8,
        "Q": 10,
        "Z": 10,
    }
    total_score = 0

    for char_original in word:
        char_upper = char_original.upper()
        if not char_upper.isascii():
            return 0  # Stop and return 0 if non-ASCII character is found

        total_score += letter_scores.get(
            char_upper, 0
        )  # Default to 0 for non-letters (though isascii should catch most)

    # Add bonus points for word length over 9 characters
    if len(word) > 9:
        bonus_points = len(word) - 9
        total_score += bonus_points

    return total_score


def get_is_known_word(*args):
    """
    Checks the online dictionary to determine if the candidate is an actual word."
    Expects the candidate word as the first argument.
    """
    if not args:
        print(
            "Error: get_is_known_word expects at least one argument (candidate word)."
        )
        return False
    candidate = args[0]

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{candidate}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            # Optionally, you might still want to see the JSON response for a known word.
            # models_data = response.json()
            # print(json.dumps(models_data, indent=2))
            return True
        elif response.status_code == 404:
            return False
        else:
            # For any other status code, print a message and then raise the exception
            print(
                f"Unexpected status code {response.status_code} for word '{candidate}': {response.text}"
            )
            response.raise_for_status()  # This will re-throw an HTTPError for other bad statuses

    except requests.exceptions.RequestException as e:
        # This will catch the re-thrown error from response.raise_for_status()
        # or other network-related errors from requests.get()
        print(f"An error occurred while checking word '{candidate}': {e}")
        return (
            False  # Or re-raise, depending on desired error handling for network issues
        )
    except json.JSONDecodeError:
        # This might occur if a 200 response isn't valid JSON, though less likely for this API
        print(f"Failed to decode JSON from response for word '{candidate}'.")
        return False


KNOWN_FUNCTIONS = {
    "get_min_scrabble_word_score": get_min_scrabble_word_score,
    "get_is_known_word": get_is_known_word,
    "get_weather_forecast": get_weather_forecast,
    # Add other known functions here as they are defined
}
