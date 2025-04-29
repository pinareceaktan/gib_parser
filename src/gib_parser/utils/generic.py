import hashlib


def generate_hash_from_dict(dict_el) -> dict:
    base_string = "|".join(list(dict_el.values()))
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()
