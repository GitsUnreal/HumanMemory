import random

class MainLogic:
    def generate_serial(self) -> list[int]:
        """Generate a random serial of 10 numbers between 1 and 99."""
        return [random.randint(1, 99) for _ in range(10)]
    
    def check_serial(self, generated: list[int], entered: list[int | None]) -> list[bool]:
        """Check the entered serial against the generated one.
        
        Returns a list of booleans indicating correctness for each position.
        """
        results = []
        for gen, ent in zip(generated, entered):
            if ent is None:
                results.append(False)
            else:
                results.append(gen == ent)
        return results
    

