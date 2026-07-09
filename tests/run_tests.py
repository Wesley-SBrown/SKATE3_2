import os
import subprocess

test_dir = "tests/"

with open(os.path.join(test_dir,'selected_files.txt'), 'r') as f:
  filenames = f.readlines()

print(filenames)
num_to_process = len(filenames)

# Path to the bash script relative to tests/ folder
deployment_dir = "scripts/deployment"
script_name = "test_meanlines_and_roi_s3.sh"

# Get absolute path of project root and pass it to environment
project_root = os.path.abspath(os.getcwd())
custom_env = os.environ.copy()
custom_env["PROJECT_ROOT"] = project_root
custom_env["PYTHONPATH"] = (
    f"{project_root}:{custom_env.get('PYTHONPATH', '')}".strip(":")
)

for (i, filename) in enumerate(filenames):
  filename = filename.rstrip()

  if not filename:
    continue # skips empty lines

  print(f"\nimage {i} of {num_to_process}")
  local_path = os.path.abspath(os.path.join(test_dir, filename))

  # uncomment to download from S3
  # call() is deprecated
  # s3_uri = f"s3://WWSSN_Scans/{filename}"
  # subprocess.run(["aws", "s3", "cp", s3_uri, local_path, "--region", "us-east-1", "--profile", "seismo"], check=True)

  print("running test_meanlines_and_roi.sh")
  subprocess.run(
        ["bash", script_name, filename, local_path],
        env=custom_env,
        cwd=deployment_dir,
        check=True,
    )

  # uncomment to delete local file afterwards
  # print(f"deleting {filename}")
  # if os.path.exists(local_path):
  #   os.remove(local_path)
