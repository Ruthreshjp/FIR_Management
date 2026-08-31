import os
import shutil

src = r"C:\Users\RUTHRESH.J.P\.gemini\antigravity-ide\brain\a18674b6-edb0-4c28-8746-16de98d0f6e9\autofir_logo_1788102955592.jpg"
dest_dir = r"d:\auto_fir\frontend\public"
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

dest = os.path.join(dest_dir, "logo.jpg")
shutil.copy2(src, dest)

print(f"Copied to {dest}")
