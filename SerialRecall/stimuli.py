# Stimuli helpers and pools
import random
import string
import re

# Letter pools
# Exclude some vowels to reduce letter-name ambiguities in recall (classic consonant spans)
CONSONANTS = [c for c in string.ascii_uppercase if c not in list("AEIOU")]

# Phonologically similar clusters (examples)
PHONO_CLUSTERS = [
    list("BPD"),     # voicing/stop confusables
    list("FV"),      # labiodental fricatives
    list("SZ"),      # alveolar fricatives
    list("CGJKQ"),   # hard /k/ /g/ confusions in names
    list("TMN"),     # nasal/stop names
]

# Visually similar clusters (based on uppercase shapes)
VISUAL_CLUSTERS = [
    list("MW"),
    list("NV"),
    list("BDPR"),    # vertical stems and bowls
    list("CEGOQ"),   # circular shapes
    list("ILJT"),    # tall verticals
]

# 3-letter words (simple, common, distinct). Keep uppercase for uniformity.
THREE_LETTER_WORDS = [
    "CAT","DOG","JOB","EYE","SUN","BOX","HAT","CAR","MAP","PEN",
    "KEY","BED","CUP","LIP","BUS","HOT","RED","BIG","TOP","LEG",
    "ARM","ANT","FOX","OWL","BAG","CAP","HEN","PIG","RAT","JAM",
]

def sample_letters(n, avoid_immediate_repeat=True):
    seq = []
    pool = CONSONANTS.copy()
    for i in range(n):
        choices = pool
        if avoid_immediate_repeat and seq:
            choices = [c for c in pool if c != seq[-1]]
        seq.append(random.choice(choices))
    return seq

def sample_from_clusters(n, clusters):
    # Combine clusters into a flat pool, but ensure each trial tends to include cluster members
    # Strategy: select a cluster or two, sample more heavily from them, fill with other consonants
    seq = []
    chosen = random.sample(clusters, k=min(2, len(clusters)))
    heavy_pool = [c for cl in chosen for c in cl]
    base_pool = list(set([c for cl in clusters for c in cl]))
    others = [c for c in CONSONANTS if c not in base_pool]
    while len(seq) < n:
        if random.random() < 0.6:
            seq.append(random.choice(heavy_pool))
        else:
            seq.append(random.choice(others))
        if len(seq) >= 2 and seq[-1] == seq[-2]:
            seq[-1] = random.choice(CONSONANTS)
    return seq

def sample_words(n, words=THREE_LETTER_WORDS):
    return random.sample(words, k=n)  # unique words per trial

def stringify(seq):
    if all(len(x) == 1 for x in seq):
        return "".join(seq)
    return " ".join(seq)

def parse_response(text, is_words=False):
    text = text.strip().upper()
    if is_words:
        # Accept spaces and/or commas as separators
        parts = [p for p in re.split(r"[\s,]+", text) if p]
        return parts
    # letters: remove any non-letters, split into single chars
    letters = [c for c in text if c in string.ascii_uppercase]
    return letters

def score_serial_recall(target, response):
    # Position-wise correct
    L = max(len(target), len(response))
    correct_positions = 0
    pos_correct = []
    for i in range(L):
        t = target[i] if i < len(target) else None
        r = response[i] if i < len(response) else None
        is_ok = (t == r and t is not None)
        pos_correct.append(1 if is_ok else 0)
        if is_ok: correct_positions += 1
    all_or_nothing = 1 if (len(target) == len(response) and all(pos_correct[:len(target)])) else 0
    prop_correct = correct_positions / len(target) if len(target) > 0 else 0.0
    return {
        "pos_correct": pos_correct[:len(target)],
        "n_correct": correct_positions,
        "prop_correct": prop_correct,
        "all_or_nothing": all_or_nothing
    }
