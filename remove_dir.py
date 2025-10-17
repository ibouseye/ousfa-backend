import shutil
import os

dir_to_remove = "D:/ousfa_gemini_cli/backend/backend/"

if os.path.exists(dir_to_remove):
    shutil.rmtree(dir_to_remove)
    print(f"Successfully removed {dir_to_remove}")
else:
    print(f"{dir_to_remove} does not exist.")
