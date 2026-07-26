import os
import subprocess
import datetime
import sys
import time
import argparse
import requests
import questionary
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()

def run_cmd(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error executing {' '.join(cmd)}:[/bold red] {e.stderr}")
        return False

def undo_last_commit():
    try:
        subprocess.run(["git", "rev-parse", "HEAD"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        console.print("[bold red]No commits to undo.[/bold red]")
        return
        
    with console.status("[bold yellow]Undoing last commit...[/bold yellow]", spinner="dots"):
        if run_cmd(["git", "reset", "--soft", "HEAD~1"]):
            console.print("[bold green]✔ Last commit undone locally. File changes are preserved.[/bold green]")

def check_gitignore():
    if not os.path.exists(".gitignore"):
        create = Confirm.ask("[bold magenta]No .gitignore found. Do you want to generate one?[/bold magenta]")
        if create:
            lang = questionary.select(
                "Select primary language/framework for .gitignore:",
                choices=["Python", "Node", "Java", "C++", "Go", "Ruby", "Rust", "Other (Empty)"]
            ).ask()
            
            if lang and lang != "Other (Empty)":
                with console.status(f"[bold yellow]Fetching {lang} .gitignore...[/bold yellow]"):
                    try:
                        url = f"https://raw.githubusercontent.com/github/gitignore/main/{lang}.gitignore"
                        resp = requests.get(url)
                        if resp.status_code == 200:
                            with open(".gitignore", "w") as f:
                                f.write(resp.text)
                            console.print("[bold green]✔ .gitignore generated![/bold green]")
                        else:
                            console.print("[bold red]Failed to fetch template.[/bold red]")
                    except Exception as e:
                        console.print(f"[bold red]Error fetching template: {e}[/bold red]")
            else:
                open(".gitignore", "a").close()
                console.print("[bold green]✔ Empty .gitignore created.[/bold green]")

def show_git_status():
    try:
        result = subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.PIPE, text=True, check=True)
        files = []
        for line in result.stdout.splitlines():
            if line:
                status = line[:2]
                path = line[3:]
                files.append((status, path))
    except subprocess.CalledProcessError:
        return []

    if not files:
        console.print("[bold yellow]No changes detected in the repository to commit.[/bold yellow]")
        return []
        
    table = Table(title="Changed Files", show_header=True, header_style="bold magenta")
    table.add_column("Status", style="cyan")
    table.add_column("File Path", style="green")
    
    for status, path in files:
        s_text = "Modified" if "M" in status else "Added" if "A" in status or "??" in status else "Deleted" if "D" in status else status.strip()
        color = "yellow" if "Modified" in s_text else "green" if "Added" in s_text else "red"
        table.add_row(f"[{color}]{s_text}[/{color}]", path)
        
    console.print(table)
    return files

def main():
    parser = argparse.ArgumentParser(description="WGIT - Automatic Git Push CLI")
    parser.add_argument("--undo", action="store_true", help="Undo the last local commit")
    args = parser.parse_args()

    if args.undo:
        undo_last_commit()
        return

    console.print("[bold cyan]Welcome to WGIT![/bold cyan] :rocket:")
    
    if not os.path.exists(".git"):
        with console.status("[bold yellow]Initializing git repository...[/bold yellow]", spinner="dots"):
            if not run_cmd(["git", "init"]):
                return
            time.sleep(0.5)
        console.print("[bold green]✔ Git repository initialized.[/bold green]")

    check_gitignore()

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

    changed_files = show_git_status()
    if not changed_files:
        return

    add_all = Confirm.ask("[bold magenta]Do you want to stage ALL changed files?[/bold magenta]", default=True)
    if add_all:
        with console.status("[bold yellow]Staging all files...[/bold yellow]", spinner="dots2"):
            if not run_cmd(["git", "add", "."]):
                return
    else:
        choices = [f"{path} ({status})" for status, path in changed_files]
        selected = questionary.checkbox(
            "Select files to stage:",
            choices=choices
        ).ask()
        
        if not selected:
            console.print("[bold yellow]No files selected. Aborting.[/bold yellow]")
            return
            
        with console.status("[bold yellow]Staging selected files...[/bold yellow]", spinner="dots2"):
            for item in selected:
                path = item.split(" (")[0]
                run_cmd(["git", "add", path])

    add_comment = Confirm.ask("[bold magenta]Do you want to add a git commit comment?[/bold magenta]")
    
    if add_comment:
        use_conventional = Confirm.ask("[bold magenta]Use Conventional Commits prefix (e.g. feat:, fix: )?[/bold magenta]")
        if use_conventional:
            prefix = questionary.select(
                "Select commit type:",
                choices=["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore"]
            ).ask()
            msg = Prompt.ask("[bold magenta]Enter commit message[/bold magenta]").strip()
            comment = f"{prefix}: {msg}" if msg else f"{prefix}: update"
        else:
            comment = Prompt.ask("[bold magenta]Enter commit comment[/bold magenta]").strip()
            if not comment:
                comment = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        comment = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    with console.status(f"[bold yellow]Committing with message: '{comment}'...[/bold yellow]", spinner="dots2"):
        subprocess.run(["git", "commit", "-m", comment], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(0.3)

    # Auto-detect branch
    current_branch = ""
    try:
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
