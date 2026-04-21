def generate_transcription(phonemized_text: list) -> str:
    """
    Converts the phonemized data structure into a Cyrillic phonetic string.
    """
    output = []

    # Mapping punctuation to slashes
    phrase_ends = {",", ";", ":", "(", ")", "—"}
    sentence_ends = {".", "!", "?"}

    for token in phonemized_text:
        if isinstance(token, str):
            # Handle punctuation and whitespace
            if any(p in token for p in sentence_ends):
                output.append(" //")
            elif any(p in token for p in phrase_ends):
                output.append(" /")
            elif token.isspace():
                output.append(token)
            continue

        # Handle word (list of phonemes)
        word_str = ""
        for p in token:
            if hasattr(p, 'position'):  # VowelPhoneme
                word_str += p.char
                if p.position == 0:
                    word_str += '\u0301'
            else:  # ConsonantPhoneme
                word_str += p.char
                if p.soft and p.char != 'й':
                    word_str += "’"
                if p.long:
                    word_str += ":"
        output.append(word_str)

    # Clean up spacing (e.g., prevent " // //" or leading spaces)
    raw_result = "".join(output)
    return ' '.join(raw_result.split())
