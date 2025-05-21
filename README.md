# Gemini Function calling example

[This repo is intended for educational and illustration purposes.]

Large Language Models (LLMs) seem almost magic. But they are constrained by some limitations:

- They are frozen after training, leading to stale knowledge.
- They can't query or modify external data.

_The above and some of the text following is paraphrased from [Google's documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling)_

_Also, the above isn't 100% true at this point_.  The [Gemini
UI](https://gemini.google.com) can now provide correct and accurate answers to
these questions:
  - "Can you tell me the weather in Des Moines, IA?"
  - "Are the Seattle Mariners playing tonight, and if so, which team are they playing?"

This is because the latest Gemini models are augmenting the LLM capabilities
with Google Search. So while a given Gemini model might be "frozen" based on its
training date, it can query external tools now.

_But_ Gemini obviously cannot directly plug into systems or services that are local to your environment.

Function calling can mitigate this limitation. Function calling is sometimes
referred to as tool use because it allows the model to augment its knowledge with information
obtained via systems outside its purview, via functions defined within the app's logic, or remote
APIs accessible to the app, but not accessible to Gemini.

![function calling image](https://cloud.google.com/static/vertex-ai/generative-ai/docs/multimodal/images/function-calling.png)

While the documentation on the referenced page specifically refers to Vertex AI,
the generic Gemini endpoint available at generativelanguage.googleapis.com also supports
function calling. This repo demonstrates some of that.


## OK, So what's going on in this Repo?

This example code shows how to invoke generativelanguage.googleapis.com :

 1. ...to list available models, and to generate content.
    The latter could be used, for example, to ask for a dynamically-generated limerick or
    to suggest ideas for a holiday in Croatia - normal LLM Chat use cases circa 2024.

    This is in [test1-gemini-generate-content.py](./test1-gemini-generate-content.py)

 2. ...to generate content with the aid of tools available in YOUR APP that Gemini can
    ask your app to invoke.

    This is in [test2-gemini-function-calling.py](./test2-gemini-function-calling.py)

The purpose of this repo is just for educational and illustration purposes.
So people can see how it works ni a working example.


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

A simple API call to Gemini might look like this:

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

In the above :
- `:gemini` => `https://generativelanguage.googleapis.com`
- `:model` => something like `gemini-2.5-flash-preview-05-20` or one of the other available Gemini models
- `:apikey` => the value you get from [Google AI Studio](https://aistudio.google.com/)
- `:generateContent` => is what it is. It does not get replaced with anything. It's just part of the Gemini API interface.


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
          "text": "In Scrabble, what is the minimum score for the word Rabblerouser?"
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
          "text": "In Scrabble, what is the minimum score for the word Rabblerouser?"
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
asked for, PLUS the data you collected at its request.

And then Gemini can assemble and digest all of that information and provide back
a coherent response. This back-and-forth can continue for multiple
iterations. If Gemini thinks that invoking the tools your app has access too,
can help produce a correct answer, it will tell your app that, by sending back
"functionCall" elements in the response as shown above.

So, depending on the number of tools you register and the query you pass in,
your app may need to iterate a few times, going back and forth with Gemini,
before Gemini gives a final answer.

The example code here shows that.

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

When Gemini sends a response with "functionCall" in it, the script invokes the designated function call available locally.

> This is python, which is a dynamic environment and invoking functions this way is pretty easy.
> But the same approach would work with any app or environment that can conditionally invoke methods.
> It will work in Java, C#, Bash/curl, Powershell, Golang, etc.

This script also prints the payloads sent in and out, during this exchange, to allow you to see
what's happening.

When using a scrabble-oriented question, Gemini sends back a request to call the
`get_is_known_word` function, and after the app sends back the answer from that,
Gemini may also send back a request to call the `get_min_scrabble_word_score`
function.  That shows the iterative back-and-forth.


### One note on the `get_weather_forecast` function

The `get_weather_forecast` function is composed of a set of remote API requests,
first to resolve a placename like "Chicago IL" to a latitude/longitude, and then
to get the weather forecast for a given latitude/longitude.

This just illustrates that a "function" need not only be dependent upon local calculation.
It can do ... lots of things. Anything you can implement in software.


## How does this differ from AI-based Agents ?

Agentic AI is... just this. It's connecting invokable functions to a LLM.  The
idea behind _an agent_ is not limited to supplying more context to the LLM, but
extends to "performing work". Performing an update, or playing a playlist, or
opening the garage door, and so on.  But the interaction model is basically the same: 

 - the app collects a "prompt", sends it to the LLM
 - the LLM may respond with a request for more information , or , in the case of an 
   agent scenario, the LLM may respond with a requested ACTION to perform. 
 - the app then sends results back up to the LLM
 - this back-and-forth cycle may continue

Google publishes an Agent Development Kit that allows you to build agentic apps
more easily. Those apps can be things that run on the command line, or something
that runs on a mobile phone, or a desktop, or as a cloud-based service.

This "function calling" example is just a minimalistic view at the same capability.

## What about MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction)
prescribes a proposed "standard" model for describing tools to LLMs.  Google has
defined a Gemini-specific format for describing tools (see above). With MCP,
Anthropic is saying "We'll support this format, and we want others to support it
too."

So you could do something similar to this "function calling" example, with MCP,
when Gemini supports it. At the I/O Event for 2025, Google announced that
[Gemini will support
MCP](https://blog.google/technology/google-deepmind/google-gemini-updates-io-2025/#performance). This
will be coming soon.

Maybe when that's out I'll deliver a Gemini + MCP example.


## Interesting Note

I'm not a python expert. I know C#, Java, JavaScript, and a little Powershell,
but not much python.  Despite that, I implemented this example in just a few
hours. It took me longer to write the README (honestly).

How did I work this magic?  Almost all of the python code in this repo was
generated by Gemini, in response to English language prompts.

I started with this:
```
Make a new Python script that will use the requests module to make an outbound HTTP request, and
display the JSON-formatted response.  It should be a GET request, to this URL:

https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY_HERE}
```

And that gave me the start.

And I also got particular with lots of prompts like this:
```
Implement the get_min_scrabble_word_score function in callable_functions.py ,
using these letter scores:

(1 point) - A, E, I, L, N, O, R, S, T, U
(2 points) - D, G
(3 points) - B, C, M, P
(4 points) - F, H, V, W, Y
(5 points) - K
(8 points) - J, X
(10 points) - Q, Z

Add a bonus of 1 point for each character in the word beyond the 9th letter.
```

The result of that was:
```py
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
        print("Error: get_min_scrabble_word_score expects at least one argument (word).")
        return 0
    word = args[0]

    letter_scores = {
        'A': 1, 'E': 1, 'I': 1, 'L': 1, 'N': 1, 'O': 1, 'R': 1, 'S': 1, 'T': 1, 'U': 1,
        'D': 2, 'G': 2,
        'B': 3, 'C': 3, 'M': 3, 'P': 3,
        'F': 4, 'H': 4, 'V': 4, 'W': 4, 'Y': 4,
        'K': 5,
        'J': 8, 'X': 8,
        'Q': 10, 'Z': 10
    }
    total_score = 0

    for char_original in word:
        char_upper = char_original.upper()
        if not char_upper.isascii():
            return 0  # Stop and return 0 if non-ASCII character is found

        total_score += letter_scores.get(char_upper, 0) # Default to 0 for non-letters (though isascii should catch most)

    # Add bonus points for word length over 9 characters
    if len(word) > 9:
        bonus_points = len(word) - 9
        total_score += bonus_points

    return total_score
```

Amazing.


## Disclaimer

This example is not an official Google product, nor is it part of an
official Google product.

## License

This material is [Copyright © 2025 Google LLC](./NOTICE).
and is licensed under the [Apache 2.0 License](LICENSE).
