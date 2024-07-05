"""
Module to store utilities and other code utilized around the project
"""


def get_non_empty_input(text: str):
    """
    Get user input without spaces and good formatted and avoid any empty input
    """
    while True:
        user_input = input(text).strip()
        if user_input:
            return user_input
        print("Input cannot be empty. Please try again.")