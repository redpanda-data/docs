class FilePair:
    def __init__(self, header, implementation) -> None:
        self.header = header
        self.implementation = implementation

    def __repr__(self) -> str:
        return f"(header={self.header}, implementation={self.implementation})"
