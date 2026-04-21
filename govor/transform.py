import re
import copy

from govor.phonemizer import *


class Rule:
    def __init__(self, lhs_raw: str, rhs_raw: str):
        self.lhs, self.final = self._parse_side(lhs_raw)
        self.rhs = self._parse_rhs(rhs_raw, len(self.lhs))

    def _parse_side(self, side: str):
        # Extracts tokens like "(б слаб)", "е", "(С -мягк)"
        tokens = re.findall(r'\([^)]+\)|[^\s()]+', side)
        final = False
        if tokens[-1] == '$':
            final = True
            tokens = tokens[:-1]
        parsed = []
        for t in tokens:
            t = t.strip("()")
            parts = t.split()
            char = parts[0]
            traits = parts[1:] if len(parts) > 1 else []
            parsed.append({'char': char, 'traits': traits})
        return parsed, final

    def _parse_rhs(self, side: str, lhs_len: int):
        tokens = side.split()
        # Handle the shortcut: "(б слаб) = п" -> "1/п"
        if len(tokens) == 1 and not tokens[0].isdigit() and lhs_len == 1:
            tokens = ["1/" + tokens[0]]

        parsed = []
        for t in tokens:
            if '/' in t:
                idx, mod = t.split('/')
                mod = mod.strip("()")
                m_parts = mod.split()
                # Determine if mod is a char or a trait list
                new_char = m_parts[0] if not (m_parts[0].startswith('+') or m_parts[0].startswith('-')) else None
                new_traits = m_parts[1:] if new_char else m_parts
                parsed.append({'idx': int(idx), 'char': new_char, 'traits': new_traits})
            elif t.isdigit():
                parsed.append({'idx': int(t), 'char': None, 'traits': []})
            else:
                # New phoneme from scratch
                t = t.strip("()")
                parts = t.split()
                parsed.append({'idx': None, 'char': parts[0], 'traits': parts[1:]})
        return parsed


class TransformationEngine:
    def __init__(self, rules_text: str):
        self.rules = self._parse_rules(rules_text)
        self.wildcards = {
            'С': lambda p: isinstance(p, ConsonantPhoneme),
            'Г': lambda p: isinstance(p, VowelPhoneme),
            'А': lambda p: isinstance(p, VowelPhoneme) and p.char in "аоэ",
            'К': lambda p: isinstance(p, ConsonantPhoneme) and p.char in "гкх"
        }
        self.trait_map = {
            'мягк': 'soft', 'долг': 'long', 'слаб': 'weak'
        }

    def _parse_rules(self, text: str):
        rules = []
        for line in text.splitlines():
            line = line.split('//')[0].strip() # Remove comments
            if not line or '=' not in line: continue
            lhs, rhs = line.split('=')
            rules.append(Rule(lhs.strip(), rhs.strip()))
        return rules

    def _matches(self, phoneme, pattern):
        # Match surface form or wildcard
        p_char = pattern['char']
        if p_char in self.wildcards:
            if not self.wildcards[p_char](phoneme): return False
        elif p_char != phoneme.char:
            return False

        # Match traits/position
        for trait in pattern['traits']:
            # Position check for vowels
            if (trait.startswith('+') or trait.startswith('-')) and trait[1:].isdigit():
                if not (isinstance(phoneme, VowelPhoneme) and phoneme.position == int(trait)):
                    return False
            # Special "слаб" for vowels (non-stressed)
            elif trait == 'слаб' and isinstance(phoneme, VowelPhoneme):
                if phoneme.position == 0: return False
            # Boolean traits
            else:
                is_negated = trait.startswith('-')
                clean_trait = trait.lstrip('+-')
                attr = self.trait_map.get(clean_trait)
                if attr:
                    val = getattr(phoneme, attr, False)
                    if (not is_negated and not val) or (is_negated and val):
                        return False
        return True

    def transform_word(self, phonemes):
        new_phonemes = list(phonemes)
        for rule in self.rules:
            i = 0
            if rule.final:
                i = max(len(new_phonemes) - len(rule.lhs), 0)
            while i <= len(new_phonemes) - len(rule.lhs):
                window = new_phonemes[i : i + len(rule.lhs)]
                if all(self._matches(window[j], rule.lhs[j]) for j in range(len(rule.lhs))):
                    # Apply Transformation
                    replacement = []
                    for r_item in rule.rhs:
                        if r_item['idx'] is not None:
                            # Modify existing
                            original = copy.deepcopy(window[r_item['idx'] - 1])
                            if r_item['char']: original.char = r_item['char']
                            for tr in r_item['traits']:
                                is_neg = tr.startswith('-')
                                attr = self.trait_map.get(tr.lstrip('+-'))
                                if attr: setattr(original, attr, not is_neg)
                            replacement.append(original)
                        else:
                            # Create new (Implementation depends on char type)
                            # Simplified: assume vowel if char in vowels_map
                            pass # Add logic for generating new Phonemes if needed

                    new_phonemes[i : i + len(rule.lhs)] = replacement
                    i += len(replacement) # Move past the change
                else:
                    i += 1
        return new_phonemes

    def run(self, phonemized_text):
        return [self.transform_word(token) if isinstance(token, list) else token
                for token in phonemized_text]
