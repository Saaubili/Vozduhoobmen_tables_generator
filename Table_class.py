class Table:
    def __init__(self, header, bbox, name):
        self.header = header
        self.bbox = bbox
        self.name = name
        self.rows = []

    def set_rows(self, created_rows):
        self.rows = created_rows