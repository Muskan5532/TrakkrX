
class Subject:

    def __init__(self, name, description=""):
        self.name = name
        self.description = description

    def display_details(self):
        print("Subject:", self.name)
        print("Description:", self.description)
