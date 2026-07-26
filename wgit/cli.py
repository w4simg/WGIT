import os
import subprocess
import datetime
import sys
import time
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

def run_cmd(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error executing {' '.join(cmd)}:[/bold red] {e.stderr}")
        return False

def main():
    console.print("[bold cyan]Welcome to WGIT![/bold cyan] :rocket:")
    
    if not os.path.exists(".git"):
        with console.status("[bold yellow]Initializing git repository...[/bold yellow]", spinner="dots"):
            if not run_cmd(["git", "init"]):
                return
            time.sleep(0.5)
        console.print("[bold green]✔ Git repository initialized.[/bold green]")

    repo_link = Prompt.ask("[bold magenta]Enter git repo link[/bold magenta]").strip()
    if repo_link:
        with console.status("[bold yellow]Fetching and setting up remote origin...[/bold yellow]", spinner="bouncingBar"):
            subprocess.run(["git", "remote", "remove", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not run_cmd(["git", "remote", "add", "origin", repo_link]):
                return
            subprocess.run(["git", "fetch", "origin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
        console.print("[bold green]✔ Fetched successfully![/bold green]")
    else:
        console.print("[bold red]Repo link cannot be empty.[/bold red]")
        return

    add_comment = Confirm.ask("[bold magenta]Do you want to add a git commit comment?[/bold magenta]")
    
    if add_comment:
        comment = Prompt.ask("[bold magenta]Enter commit comment[/bold magenta]").strip()
        if not comment:
            comment = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        comment = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    with console.status("[bold yellow]Staging files...[/bold yellow]", spinner="dots2"):
        if not run_cmd(["git", "add", "."]):
            return
        time.sleep(0.3)
        
    with console.status(f"[bold yellow]Committing with message: '{comment}'...[/bold yellow]", spinner="dots2"):
        subprocess.run(["git", "commit", "-m", comment], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(0.3)

    # Auto-detect branch
    current_branch = ""
    try:
        # Get current branch
        result = subprocess.run(["git", "branch", "--show-current"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        current_branch = result.stdout.strip()
    except subprocess.CalledProcessError:
        pass

    if current_branch:
        branch = current_branch
        console.print(f"[bold cyan]Current branch '{branch}' detected. Using it automatically.[/bold cyan]")
    else:
        branch = Prompt.ask("[bold magenta]Branch name[/bold magenta]", default="master").strip()
        with console.status(f"[bold yellow]Preparing branch '{branch}'...[/bold yellow]", spinner="dots"):
            subprocess.run(["git", "branch", "-M", branch], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.3)

    with console.status(f"[bold yellow]Pushing to {branch}...[/bold yellow]", spinner="earth"):
        if run_cmd(["git", "push", "-u", "origin", branch]):
            console.print("[bold green]✔ Pushed successfully![/bold green] :tada:")
        else:
            console.print("[bold red]Failed to push. Please check your credentials, permissions, and repository link.[/bold red]")

if __name__ == "__main__":
    main()
