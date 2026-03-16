"""Test tool1 - basic LLM interactions."""

# /// script
# requires-python = ">=3.13"
# dependencies = [
#  "requests",
#  "python-dotenv",
# ]
# ///

# Copyright © 2025-2026 Google LLC.
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

import argparse
import json
import os
import random

from dotenv import load_dotenv
import requests

load_dotenv()

INSTRUCTION_PROMPTS = [
    {
        "instruction": (
            "You are an expert travel advisor. You are helpful and polite."
        ),
        "prompts": [
            (
                "Someone told me <<Expect cool weather when you visit>>,"
                " speaking of Seattle in May. What would the expected"
                " temperature range be?"
            ),
            (
                "If I am visiting Seattle in June (I will be flying in), should"
                " I rent a car, or would it be better to take public transit"
                " and uber/lyft?"
            ),
        ],
    },
    {
        "instruction": (
            "You are an expert in residential real estate topics. You are"
            " helpful and polite."
        ),
        "prompts": [
            (
                "When is the best time of year to begin building a home? What"
                " factors are important to consider? Are there some times of"
                " year that are 'slow' for contractors, which might give me an"
                " opportunity for savings?"
            ),
            (
                "What are typical construction costs per sq ft, for various"
                " classes of residential housing? What's the rate for a good,"
                " medium-grade 'Buick' grade class of home? What about"
                " 'Cadillac' grade?"
            ),
            (
                "What is the typical ratio of cost for land vs cost for the"
                " building, in new construction of a single family home?"
            ),
        ],
    },
    {
        "instruction": (
            "You are a nutritionist. You provide matter-of-fact information, in"
            " your thorough, explanatory answers."
        ),
        "prompts": [
            (
                "For a given amount of protein consumption, is it better for me"
                " if I consume it earlier in the day, or later in the day? I"
                " want to optimize for absorption and satiety."
            ),
            (
                "Should I consider an apple to be a good source of fiber? How"
                " much fiber should a healthy adult consume ddaily?"
            ),
            (
                "About how many grams of carbohydrate does a medium sized"
                " <<Cosmic Crisp>> apple supply? About how many carbs would a"
                " normal 2500-calorie diet include?"
            ),
            (
                "What are the ratios of macronutrients I should shoot for in my"
                " daily diet, if I'm a normal healty adult male?"
            ),
        ],
    },
]

USED_PROMPTS = []


def getBaseApiUrl() -> str:
  """Internal function that reads the environment variable BASE_API_URL."""
  return os.environ.get(
      "BASE_API_URL", "https://generativelanguage.googleapis.com"
  )


def getModelName() -> str:
  """Internal function that reads the environment variable TEXT_MODEL_NAME."""
  return os.environ.get("TEXT_MODEL_NAME", "gemini-flash-latest")


def getGeminiKey() -> str:
  """Internal function that reads the environment variable GEMINI_APIKEY."""
  return os.environ.get("GEMINI_APIKEY", "-unset-")


def fetch_models(api_key):
  """Fetches models from the Google Generative Language API and prints the JSON response."""
  if not api_key:
    return

  my_headers = {"x-goog-api-key": api_key}

  url = f"{getBaseApiUrl()}/v1beta/models"

  try:
    response = requests.get(url, headers=my_headers)
    response.raise_for_status()
    models_data = response.json()
    print(json.dumps(models_data, indent=2))

  except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
  except json.JSONDecodeError:
    print("Failed to decode JSON from response.")


def generate_content(api_key):
  """Generates content using the Google Generative Language API via a POST request.

  and prints the JSON response.
  """
  if not api_key:
    return

  global USED_PROMPTS

  url = f"{getBaseApiUrl()}/v1beta/models/{getModelName()}:generateContent"

  available_options = []
  for scenario in INSTRUCTION_PROMPTS:
    for prompt in scenario["prompts"]:
      if prompt not in USED_PROMPTS:
        available_options.append((scenario["instruction"], prompt))

  if not available_options:
    print("All prompts have been used. Resetting tracker.")
    USED_PROMPTS.clear()
    for scenario in INSTRUCTION_PROMPTS:
      for prompt in scenario["prompts"]:
        available_options.append((scenario["instruction"], prompt))

  selected_instruction, selected_prompt = random.choice(available_options)
  USED_PROMPTS.append(selected_prompt)

  payload = {
      "system_instruction": {"parts": {"text": selected_instruction}},
      "contents": [{"role": "user", "parts": [{"text": selected_prompt}]}],
      "generation_config": {"temperature": 1, "topP": 1},
  }

  headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}

  try:
    print(f"\nGenerating content with model: {getModelName()}...")
    print(f"Instruction: {selected_instruction}")
    print(f"Prompt: {selected_prompt}")
    print("Payload:")
    print(json.dumps(payload, indent=2))
    input("\nPress ENTER to continue...")

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


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description=(
          "Test script for Gemini API content generation (w/o function"
          " calling). Verbose logging is on by default."
      )
  )
  parser.add_argument(
      "--quiet",
      action="store_true",
      help="Disable verbose logging of API requests and responses.",
  )
  args = parser.parse_args()
  gemini_api_key = getGeminiKey()

  if not gemini_api_key:
    print(
        "No gemini API key found in environment 'GEMINI_APIKEY'. Cannot"
        " continue."
    )
    raise SystemExit

  fetch_models(gemini_api_key)
  for _ in range(3):
    generate_content(gemini_api_key)
