class Task:

    def __init__(self, title, subject, description="", deadline=""):
        self.title = title
        self.subject = subject
        self.description = description
        self.deadline = deadline
        self.completion_status= False

    def mark_complete(self):
        self.completion_status = True
    
    def display_status(self):
        if self.completion_status:
            return"COMPLETED"
        else:
            return"PENDING"

    def display_details(self):
        print("Task:", self.title)
        print("Subject:", self.subject)
        print("Description:", self.description)
        print("Deadline:", self.deadline)
        print("Completion Status:", self.display_status())