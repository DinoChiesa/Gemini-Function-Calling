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
            # Keep track of words used for this specific placeholder type within this call
            used_words_for_this_key = set()
            # Create a mutable copy of the word list to pick from
            available_words_for_this_key = list(word_list)
            random.shuffle(available_words_for_this_key) # Shuffle to make pop() effectively random

            while actual_placeholder_to_find in text_content:
                if not available_words_for_this_key:
                    if not word_list: # Original source list is empty, cannot refill.
                        # Silently break as no more replacements are possible for this placeholder.
                        break
                    # Refill available_words_for_this_key from the original word_list
                    available_words_for_this_key = list(word_list)
                    random.shuffle(available_words_for_this_key)
                    used_words_for_this_key.clear() # Reset used words for the new cycle

                # If word_list was empty, the break above would have been hit.
                # So, if we are here, available_words_for_this_key is populated.
                replacement_word = available_words_for_this_key.pop()
                text_content = text_content.replace(actual_placeholder_to_find, replacement_word, 1)
                used_words_for_this_key.add(replacement_word) # Track usage within the current cycle of available_words
    return text_content
