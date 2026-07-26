import os
import subprocess
import datetime
import sys

def run_cmd(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        return False

def main():
    if not os.path.exists(".git"):
        print("Initializing git repository...")
        if not run_cmd(["git", "init"]):
            return

    repo_link = input("Enter git repo link: ").strip()
    if repo_link:
        # Remove existing origin if any, ignore error if it doesn't exist
        subprocess.run(["git", "remote", "remove", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not run_cmd(["git", "remote", "add", "origin", repo_link]):
            return
        print("fetched successfully")
    else:
        print("Repo link cannot be empty.")
        return

    add_comment = input("Do you want to add a git commit comment? (y/n): ").strip().lower()
    
    if add_comment == 'y':
        comment = input("Enter commit comment: ").strip()
        if not comment:
            comment = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        comment = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    print("Staging files...")
    if not run_cmd(["git", "add", "."]):
        return
        
    print(f"Committing with message: '{comment}'")
    # git commit might fail if there's nothing to commit, we ignore the error so push can still run if there are existing commits
    subprocess.run(["git", "commit", "-m", comment], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    branch = input("Branch name (default master): ").strip()
    if not branch:
        branch = "master"

    # Make sure we are on the correct branch and it's created/renamed
    subprocess.run(["git", "branch", "-M", branch], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"Pushing to {branch}...")
    if run_cmd(["git", "push", "-u", "origin", branch]):
        print("Pushed successfully!")
    else:
        print("Failed to push. Please check your credentials, permissions, and repository link.")

if __name__ == "__main__":
    main()
