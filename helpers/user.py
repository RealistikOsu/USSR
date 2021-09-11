# Helps with users LOL
def safe_name(s: str) -> str:
    """Generates a 'safe' variant of the name for usage in rapid lookups
    and usage in Ripple database.

    Note:
        A safe name is a name that is:
            - Lowercase
            - Has spaces replaced with underscores
            - Is rstripped.
    
    Args:
        s (str): The username to create a safe variant of.
    """

    return s.lower().replace(" ", "_").rstrip()
