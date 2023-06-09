import ftplib
import os
import sys
args = sys.argv

def list_directories(ftp, path="/"):
    try:
        ftp.cwd(path)
        yield path
        for file in ftp.nlst():
            if file.startswith('.'):
                continue
            try:
                ftp.cwd(file)
                yield from list_directories(ftp, path + file + "/")
                ftp.cwd("..")
            except:
                pass
                # print("  File:", file)
    except:
        print("Failed to change directory to:", path)


args = sys.argv

# FTP server details
ftp_host = args[1]
ftp_user = args[2]
ftp_pass = args[3]

# Local file details
local_dir = '../app/build'
local_files = os.listdir(local_dir)

# Remote directory details
remote_dir = "/" + args[4]

# Load modification times of previously uploaded files from a file
last_modified_file = os.path.join("", 'last_modified.txt')

if os.path.exists(last_modified_file):
    with open(last_modified_file) as f:
        last_modified_times = dict(line.strip().split(None, 1) for line in f)
else:
    last_modified_times = {}

# Get the current modification times of all files in the local directory tree
current_modified_times = {}
for root, dirs, files in os.walk(local_dir):
    for file in files:
        path = os.path.join(root, file)
        relpath = os.path.relpath(path, local_dir).replace('\\', '/')
        current_modified_times[relpath] = str(os.path.getmtime(path))

# Connect to FTP server
ftp = ftplib.FTP(ftp_host, ftp_user, ftp_pass)

# Navigate to remote directory
ftp.cwd(remote_dir)

# Create necessary directories on the remote server
list_dir = list(list_directories(ftp, path=remote_dir))
list_dir = [x.replace(remote_dir, "")[:-1] for x in list_dir]
for subdir in [
    os.path.relpath(root, local_dir).split('/')[0].replace("\\", "/")
    for root, dirs, files in list(os.walk(local_dir))
][1:]:
    if subdir and subdir not in list_dir:
        ftp.mkd(subdir)

# Upload files that have been modified since the last upload
for file, modified_time in current_modified_times.items():
    if file not in last_modified_times or last_modified_times[file] < modified_time:
        local_file_path = os.path.join(local_dir, file)
        print(f"Uploading {local_file_path}")
        with open(local_file_path, 'rb') as f:
            ftp.storbinary('STOR ' + file, f)
        last_modified_times[file] = modified_time

# Save the modification times of the uploaded files to a file
with open(last_modified_file, 'w') as f:
    for file, modified_time in last_modified_times.items():
        f.write(f"{file} {modified_time}\n")

# Close FTP connection
ftp.quit()

print('Files uploaded successfully.')
