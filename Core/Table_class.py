class Table:
    def __init__(self, header, bbox, name, floor):
        self.header = header
        self.bbox = bbox
        self.name = name
        self.rows = []
        self.floor = floor

    def set_rows(self, created_rows):
        self.rows = created_rows