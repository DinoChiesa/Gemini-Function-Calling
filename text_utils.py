import random

NAMES = [
    "Roberto", "Blake", "Carson", "Ali", "Sundar", "Suresh", "Surpreet",
    "Yinbang", "Cal", "Maria", "David", "Aisha", "Kenji"
]

FOODS = [
    "Broccoli", "Papaya", "Oatmeal"    , "Carrots", "Cabbage"
]

ENGLISH_WORDS = [
    "Apple",           # A
    "Boredom",         # B
    "Borogoves",       # Nonsense
    "Brillig",         # Nonsense
    "Cacophony",       # C
    "Concrete",        # C (already present)
    "Dystopian",       # D
    "Eledricious",     # Not-a-word
    "Ephemeral",       # E
    "Flummox",         # F
    "Gargantuan",      # G
    "Gimble",          # Nonsense
    "Gyrattable",      # Not-a-word
    "Halcyon",         # H
    "Incandescent",    # I
    "Juxtaposition",   # J
    "Kaleidoscope",    # K
    "Labyrinth",       # L
    "Manxome",         # Nonsense
    "Mellifluous",     # M
    "Mimserable",      # Not-a-word
    "Nefarious",       # N
    "Onomatopoeia",    # O
    "Parameter",       # P
    "Pulsameter",      # Not-a-word
    "Quintessential",  # Q
    "Quixotic",        # Q (already present)
    "Rabblerouser",    # R
    "Serendipity",     # S
    "Slithy",          # Nonsense
    "Standoffish",     # S (already present)
    "Tesseract",       # T
    "Toves",           # Nonsense
    "Ubiquitous",      # U
    "Vicarious",       # V
    "Wabe",            # Nonsense
    "Wanderlust",      # W
    "Xylophone",       # X
    "Yare",            # Y
    "Zephyr"           # Z
]
ENGLISH_WORDS.sort() # Ensure the list is sorted alphabetically

REPLACEMENTS = {
    ":NAME": NAMES,
    ":FOOD": FOODS,
    ":ENGLISH_WORD": ENGLISH_WORDS
}

def replace_placeholders_in_string(text_content, replacements_map):
    """
    Replaces placeholders in a string with randomly selected values from provided lists.
    Placeholders are e.g. :NAME, :ENGLISH_WORD.
    The replacements_map is a dict like {'NAMES': [...], 'ENGLISH_WORDS': [...]}.
    """
    for placeholder, word_list in replacements_map.items():
        available_words_for_this_key = [] # Initialize as empty before the loop

        while placeholder in text_content:
            if not available_words_for_this_key:
                if not word_list: # Original source list is empty, cannot refill.
                    # Silently break as no more replacements are possible for this placeholder.
                    break
                # Populate/Re-populate the list here
                available_words_for_this_key = list(word_list)
                random.shuffle(available_words_for_this_key)

            # If word_list was empty, the break above would have been hit.
            # So, if we are here, available_words_for_this_key is populated.
            replacement_word = available_words_for_this_key.pop()
            text_content = text_content.replace(placeholder, replacement_word, 1)

    return text_content
