import re

def required(value, label):
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{label} is required.")
    return value

def positive_int(value, label, minimum=0):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a whole number.")
    if number < minimum:
        raise ValueError(f"{label} must be at least {minimum}.")
    return number

def optional_email(value):
    value = (value or "").strip()
    if value and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise ValueError("Enter a valid email address.")
    return value or None
