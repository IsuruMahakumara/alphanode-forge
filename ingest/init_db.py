"""Initialize forge systematic state DB."""

from forge.execution.state import init_db

if __name__ == "__main__":
    init_db()
    print("systematic state DB initialized")
