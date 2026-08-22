import os

def get_all_dart_files(project_path):
    dart_files = []
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith(".dart"):
                dart_files.append(
                    os.path.join(root, file)
                )
    return dart_files
