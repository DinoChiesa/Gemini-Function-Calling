# Gemini Function calling example

Large Language Models (LLMs) seem almost magic. But they are constrained by some limitations:

- They are frozen after training, leading to stale knowledge.
- They can't query or modify external data.

_The above and some of the text following is paraphrased from [Google's documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling)_

_This isn't quite true at this point_.  The [Gemini
UI](https://gemini.google.com) can now provide correct and accurate answers to
these questions:
  - "Can you tell me the weather in Des Moines, IA?"
  - "Are the Seattle Mariners playing tonight, and if so, which team are they playing?"

This is because the latest Gemini models are augmenting the LLM capabilities with Google Search.
_But_ Gemini obviously cannot directly plug into systems or services that are local to your environment.

Function calling can mitigate this limitation. Function calling is sometimes
referred to as tool use because it allows the model to augment its knowledge with information
obtained via systems outside its purview, via functions defined within the app's logic, or remote
APIs accessible to the app, but not accessible to Gemini.

![function calling image](https://cloud.google.com/static/vertex-ai/generative-ai/docs/multimodal/images/function-calling.png)

While the documentation on the referenced page specifically refers to Vertex AI,
the generic Gemini endpoint at generativelanguage.googleapis.com also supports
function calling. This repo demonstrates some of that.


## OK, So what's going on in this Repo?

This example code shows how to invoke generativelanguage.googleapis.com :

 1. ...to list available models, and to generateContent.
    The latter could be used, for example, to ask for a dynamically-generated limerick or
    to suggest ideas for a holiday in Croatia - normal LLM Chat use cases.

    This is in [test1-gemini-generate-content.py](./test1-gemini-generate-content.py)

 2. to generateContent, with the aid of tools available in YOUR APP that Gemini can
    ask your app to invoke.

    This is in [test2-gemini-function-calling.py](./test2-gemini-function-calling.py)

The purpose of this repo is just for educational and illustration purposes.
So people can see how it works.


Before we get into more specific details on how to use these things, let's cover some background.

## How does function calling work in Gemini?

Here's a simplified flow:

1. You define functions: In your application code, you describe functions that can perform specific actions (e.g., get current weather, fetch product details from a database, book a meeting).

1. You pass function descriptions to Gemini: When you send a prompt to Gemini, you also provide the descriptions (name, parameters, what it does) of your available functions.

1. Gemini analyzes the prompt: If Gemini determines that the user's request requires an action that one of your defined functions can handle, it doesn't try to answer directly.

1. Gemini returns a "function call" request: Instead of a text answer, the model returns a structured JSON object indicating which function it wants to call and with what arguments (extracted from the user's prompt).

1. You execute the function: Your application code receives this JSON, executes the specified local function with the provided arguments.

1. You send the function's result back to Gemini: You then make another call to Gemini, providing the output/result from your function.

1. Gemini uses the result to generate a final response: Gemini incorporates the information from your function's execution to provide a comprehensive and relevant answer to the user's original prompt.


## The difference between the generic Gemini endpoint and Vertex AI

Both Gemini and Vertex AI  are accessible via API endpoints. Both of them generate content dynamically.

The key difference lies in their intended use cases and features:

- The generativelanguage.googleapis.com endpoint (often referred to as the Gemini API or Google AI Studio's API) is designed for developers to quickly get started and prototype with Gemini models. It's simpler to use, often leveraging API keys for authentication.

- The aiplatform.googleapis.com endpoint is part of Vertex AI, Google Cloud's unified machine learning platform. This endpoint is geared towards enterprise applications and production environments. It offers more robust features like integration with other Google Cloud services (IAM for authentication, MLOps tools), data residency options, and potentially different pricing and quota structures.

A good approach, start with generativelanguage.googleapis.com for exploration
and early development. When you're ready to build scalable, production-ready
applications with more control and integration, transition to the Vertex AI
endpoint.


## Using Function Calling with Gemini, in detail

OK let's get started.

A simple REST call to Gemini might look like this:

```
POST :gemini/v1beta/models/:model:generateContent?key=:key
Content-Type: application/json

{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
         "text": "What are some good approaches to improving my sleep quality?"
        }
      ]
    }
  ],
  "generation_config": {
    "temperature": 1,
    "topP": 1
  }
}
```

When submitting a prompt to the LLM, an app can augment that JSON to provide the model with a
description of "tools" that THE APP can use to help the LLM respond to the user's prompt.

A modified payload might look like this:

```
POST :gemini/v1beta/models/:model/:generateContent?key=:key
Content-Type: application/json

{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "What is the minimum word score for Rabblerouser in Scrabble?"
        }
      ]
    }
  ],
  "tools": [
    {
      "functionDeclarations": [
        {
          "name": "get_min_scrabble_word_score",
          "description": "Returns the minimum score for a given word in the game Scrabble (tm)",
          "parameters": {
            "type": "object",
            "properties": {
              "candidate": {
                "type": "string",
                "description": "The word to score"
              }
            },
            "required": [
              "candidate"
            ]
          }
        }
      ]
    }
  ]
}
```
In the above:
- `:gemini` => `https://generativelanguage.googleapis.com`
- `:model` => something like `gemini-2.5-flash-preview-05-20`
- `:apikey` => you get from [Google AI Studio](https://aistudio.google.com/)

(Actually, [Gemini](https://gemini.google.com) is smart enough to figure out
Scrabble word scores, too, but let's just put that aside for the moment.)

When you send that request to Gemini, you can get a response like the following:

```
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "functionCall": {
              "name": "get_min_scrabble_word_score",
              "args": {
                "candidate": "Rabblerouser"
              }
            }
          }
        ],
        "role": "model"
      },
      "finishReason": "STOP",
      "index": 0
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 82,
    "candidatesTokenCount": 24,
    "totalTokenCount": 172,
    "promptTokensDetails": [
      {
        "modality": "TEXT",
        "tokenCount": 82
      }
    ],
    "thoughtsTokenCount": 66
  },
  "modelVersion": "models/gemini-2.5-flash-preview-05-20"
}
```

Basically, this is Gemini saying to _your app_: please invoke that function you
told me about, with these arguments.  If your app is designed correctly, it
invokes the function locally, and then passes back information to Gemini about
the results. That information must be added to the original prompt, structured
like so:

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "What is the minimum word score for Rabblerouser in scrabble?"
        }
      ]
    },
    {
      "parts": [
        {
          "functionCall": {
            "name": "get_min_scrabble_word_score",
            "args": {
              "candidate": "Rabblerouser"
            }
          }
        }
      ],
      "role": "model"
    },
    {
      "role": "tool",
      "parts": [
        {
          "functionResponse": {
            "name": "get_min_scrabble_word_score",
            "response": {
              "content": {
                "candidate": "Rabblerouser",
                "result": 19
              }
            }
          }
        }
      ]
    }
  ]
  ...
}
```

In that payload, you're giving Gemini the original prompt, PLUS the thing it
asked for PLUS the data you collected at its request.

And then Gemini can assemble and digest all of that information and provide back
a coherent response.  This back-and-forth can continue for multiple
iterations. If Gemini thinks that invoking the tools your app has access too,
can help produce a correct answer, it will tell your app that, by sending back
"functionCall" elements in the response as shown above.

So, depending on the number of tools you register and the query you pass in,
your app may need to iterate a few times, going back and forth with Gemini,
before Gemini gives a final answer.


## Trying the code - Pre-requisites

You need these things:

- to have python and pip installed on your machine

- an API key for Gemini, that you can get for free at [Google AI Studio](https://aistudio.google.com/)

  Store it in the file named ".google-gemini-apikey"

- an API Key for TomTom, that you can get for free from [TomTom](https://developer.tomtom.com)
  Register it for the Geocoding APIs.

  Store it in the file named ".tomtom-apikey"

## One time setup

Make a new directory. Set up a venv for python.

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests
```

## Run the basic "generate content" test

This will select one of a fixed set of prompts, send it to Gemini, and display the results.

```bash
python3 test1-gemini-generate-content.py
```

Interesting, but _not function calling_.


## Run the function calling test

This will select a function calling prompt, and engage in the back-and-forth with Gemini, and finally display the final Result:

```bash
python3 test2-gemini-function-calling.py
```

The "tools" defined for this test include:
 - `get_weather_forecast` - even though Gemini can do this itself.
 - `get_min_scrabble_word_score` - even though Gemini can do this too.
 - `get_is_known_word` - this performs a dictionary lookup on a word candidate, to determine if it is a valid word to be scored in Scrabble.


This script also prints the payloads sent in and out, during this exchange, to allow you to see
what's happening.

## Interesting Note

Almost all of the python code in this repo was generated by Gemini, in response to English prompts.

## Disclaimer

This example is not an official Google product, nor is it part of an
official Google product.

## License

This material is [Copyright © 2025 Google LLC](./NOTICE).
and is licensed under the [Apache 2.0 License](LICENSE).


