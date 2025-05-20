import random

NAMES = [
    "Roberto", "Blake", "Carson", "Ali", "Sundar", "Suresh", "Surpreet",
    "Yinbang", "Cal", "Maria", "David", "Aisha", "Kenji"
]

ENGLISH_WORDS = [
    "Boredom", "Cacophony", "Concrete", "Ephemeral", "Juxtaposition", "Labyrinth",
    "Mellifluous", "Nefarious", "Parameter", "Quintessential", "Quixotic",
    "Rabblerouser", "Serendipity", "Standoffish", "Ubiquitous", "Xylophone", "Zephyr"
]

REPLACEMENTS = {
    "NAMES": NAMES,
    "ENGLISH_WORDS": ENGLISH_WORDS
}

def replace_placeholders_in_string(text_content, replacements_map):
    """
    Replaces placeholders in a string with randomly selected values from provided lists.
    Placeholders are e.g. :NAME, :ENGLISH_WORD.
    The replacements_map is a dict like {'NAMES': [...], 'ENGLISH_WORDS': [...]}.
    """
    for key, word_list in replacements_map.items():
        # Determine the placeholder string based on the key
        actual_placeholder_to_find = ""
        if key == "NAMES":
            actual_placeholder_to_find = ":NAME"
        elif key == "ENGLISH_WORDS":
            actual_placeholder_to_find = ":ENGLISH_WORD"
        # Add more specific placeholder mappings here if needed

        if actual_placeholder_to_find:
            while actual_placeholder_to_find in text_content:
                if word_list:  # Ensure the list is not empty
                    replacement_word = random.choice(word_list)
                    text_content = text_content.replace(actual_placeholder_to_find, replacement_word, 1)
                else:
                    # If the list is empty, break to avoid infinite loop on placeholder
                    print(f"Warning: Word list for {key} is empty, cannot replace {actual_placeholder_to_find}")
                    break
    return text_content
