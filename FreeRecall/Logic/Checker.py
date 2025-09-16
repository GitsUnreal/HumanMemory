
class Checker:
    """
    Class to check the user's input against the original serial list.
    """
    @staticmethod
    def check(serial_list: list[int | None], user_input: list[int | None]) -> list[bool]:
        """
        Compares the original serial list with the user's input and returns a list of booleans indicating correctness.

        Args:
            serial_list (list[int | None]): The original list of integers (0-99) or None for empty slots.
            user_input (list[int | None]): The user's input list of integers (0-99) or None for empty slots.

        Returns:
            list[bool]: A list of booleans where True indicates a correct match and False indicates an incorrect match.
        """
        return [s == u for s, u in zip(serial_list, user_input)]