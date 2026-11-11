from storage import save_data, load_data

sample_tasks = [
    {
        "title": "Python Assignment",
        "subject": "Computer Programming",
        "completed": False
    }
]

# Save the sample tasks
save_data("test_storage.json", sample_tasks)

# Load the saved tasks
loaded_tasks = load_data("test_storage.json")

# Display the loaded information
print(loaded_tasks)