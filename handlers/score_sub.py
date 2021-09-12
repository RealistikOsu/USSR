
def __pair_panel(name: str, b: str, a: str) -> str:
    """Creates a pair panel string used in score submit ranking panel.
    
    Args:
        name (str): The name of the panel.
        b (str): The before value displayed.
        a (str): The after value displayed.
    """

    return f"{name}Before:{b}|{name}After:{a}"
