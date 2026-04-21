import re
from dataclasses import dataclass
from typing import List, Union, Optional


@dataclass
class VowelPhoneme:
    char: str
    position: Optional[int] = None


@dataclass
class ConsonantPhoneme:
    char: str
    soft: bool = False
    long: bool = False
    weak: bool = False


class RussianPhonemizer:
    def __init__(self):
        self.vowels_map = {
            'а': 'а', 'е': 'э', 'ё': 'о', 'и': 'и', 'о': 'о',
            'у': 'у', 'ы': 'ы', 'э': 'э', 'ю': 'у', 'я': 'а'
        }
        self.iotated = set("еёюя")
        self.softening_vowels = set("еёиюя")
        self.consonants = set("бвгджзйклмнпрстфхцчшщ")
        self.unvoiced = set("пфктшсхцчщ")
        self.always_soft = set("чщй")
        self.always_hard = set("цшж")
        self.accent = '\u0301'

    def _get_word_structure(self, word: str):
        """Identifies stress and maps vowels to their relative positions."""
        # Find vowel indices and detect which one is stressed
        stressed_idx = -1

        # We iterate and keep track of actual character indices (ignoring accents)
        clean_word = ""
        temp_vowel_indices = []

        i = 0
        while i < len(word):
            char = word[i].lower()
            if char in self.vowels_map:
                temp_vowel_indices.append(len(clean_word))
                clean_word += char
                if i + 1 < len(word) and word[i+1] == self.accent:
                    stressed_idx = len(temp_vowel_indices) - 1
                    i += 1 # skip accent
            else:
                clean_word += char
            i += 1

        return clean_word, temp_vowel_indices, stressed_idx

    def process_word(self, word: str) -> List[Union[VowelPhoneme, ConsonantPhoneme]]:
        clean_word, v_indices, s_idx = self._get_word_structure(word)
        phonemes = []

        for i, char in enumerate(clean_word):
            # --- VOWEL LOGIC ---
            if char in self.vowels_map:
                # Calculate relative position
                v_pos = None
                if s_idx != -1:
                    # Find which vowel number this is (0-indexed)
                    current_v_num = v_indices.index(i)
                    v_pos = current_v_num - s_idx

                # Check for iotation (start of word, after vowel, or after ь/ъ)
                is_after_vowel = i > 0 and clean_word[i-1] in self.vowels_map
                is_after_separator = i > 0 and clean_word[i-1] in "ьъ"

                if (i == 0 or is_after_vowel or is_after_separator) and char in self.iotated:
                    phonemes.append(ConsonantPhoneme(char='й', soft=True))

                phonemes.append(VowelPhoneme(char=self.vowels_map[char], position=v_pos))

            # --- CONSONANT LOGIC ---
            elif char in self.consonants:
                # Special case for 'щ'
                target_char = 'ш' if char == 'щ' else char
                is_long = (char == 'щ')

                # Softness
                is_soft = char in self.always_soft
                if not is_soft and char not in self.always_hard:
                    if i + 1 < len(clean_word):
                        next_char = clean_word[i+1]
                        if next_char in self.softening_vowels or next_char == 'ь':
                            is_soft = True

                # Weakness (before unvoiced or end of word)
                is_weak = False
                if i + 1 == len(clean_word):
                    is_weak = True
                elif i + 1 < len(clean_word):
                    next_char = clean_word[i+1]
                    if next_char in self.unvoiced or next_char == 'ь' and i+2 == len(clean_word):
                         # Note: 'ь' itself doesn't cause weakness, but what follows it might
                         # Dialectologists vary here; using basic rule from prompt:
                         pass
                    if next_char in self.unvoiced:
                        is_weak = True

                phonemes.append(ConsonantPhoneme(
                    char=target_char,
                    soft=is_soft,
                    long=is_long,
                    weak=is_weak,
                ))

            # Note: 'ь' and 'ъ' are not added as phonemes; they modify traits.

        return phonemes

    def phonemize(self, text: str):
        # Tokenize preserving punctuation and spaces
        tokens = re.split(r'(\s+|[.,!?;:()"—])', text)
        result = []

        for token in tokens:
            if not token:
                continue
            if re.match(r'[\w\u0301]+', token):
                result.append(self.process_word(token))
            else:
                result.append(token) # Keep punctuation/spaces as strings

        return result
