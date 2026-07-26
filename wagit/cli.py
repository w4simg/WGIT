import os
import subprocess
import datetime
import sys
import time
import argparse
import requests
import questionary
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.align import Align

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

def get_groq_api_key():
    config_file = os.path.expanduser("~/.wagit_config")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            for line in f:
                if line.startswith("GROQ_API_KEY="):
                    return line.strip().split("=")[1]
    
    console.print("[bold yellow]Groq API Key not found.[/bold yellow]")
    console.print("[italic cyan]You can get a free API key here: https://console.groq.com/keys[/italic cyan]")
    api_key = Prompt.ask("[bold magenta]Enter your Groq API Key (it will be saved securely)[/bold magenta]").strip()
    if api_key:
        with open(config_file, "w") as f:
            f.write(f"GROQ_API_KEY={api_key}\n")
        return api_key
    return None

def generate_ai_commit():
    api_key = get_groq_api_key()
    if not api_key:
        console.print("[bold red]API Key is required for AI commits.[/bold red]")
        return None
        
    try:
        diff_result = subprocess.run(["git", "diff", "--staged"], stdout=subprocess.PIPE, text=True, check=True)
        diff = diff_result.stdout.strip()
        if not diff:
            console.print("[bold red]No staged changes found to generate a commit message.[/bold red]")
            return None
            
        if len(diff) > 15000:
            diff = diff[:15000] + "\n... (diff truncated)"
            
        with console.status("[bold yellow]Generating smart commit message with Groq AI...[/bold yellow]", spinner="dots"):
            from groq import Groq
            client = Groq(api_key=api_key)
            
            prompt = (
                "You are an expert developer. Generate a concise, professional git commit message based on the following git diff. "
                "Only output the commit message itself, nothing else. Do not wrap in quotes or code blocks.\n\n"
                f"Diff:\n{diff}"
            )
            
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            return completion.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"[bold red]Error generating AI commit: {e}[/bold red]")
        return None

def startup_animation():
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(style="magenta", complete_style="green"),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task1 = progress.add_task("[cyan]Initializing environment...", total=100)
        task2 = progress.add_task("[yellow]Loading modules...", total=100)
        task3 = progress.add_task("[magenta]Checking git status...", total=100)
        
        while not progress.finished:
            progress.update(task1, advance=6)
            progress.update(task2, advance=3)
            progress.update(task3, advance=4.5)
            time.sleep(0.02)
            
    panel = Panel.fit(
        "[bold cyan]W A G I T[/bold cyan]\n[italic green]Automatic Git Push CLI[/italic green]",
        border_style="bold magenta",
        padding=(1, 5)
    )
    console.print(Align.center(panel))
    console.print()

def onboard_api():
    console.print("[bold cyan]--- WAGIT API Onboarding ---[/bold cyan]")
    console.print("[italic cyan]You can get a free API key here: https://console.groq.com/keys[/italic cyan]")
    api_key = Prompt.ask("[bold magenta]Enter your new Groq API Key to update your configuration[/bold magenta]").strip()
    if api_key:
        config_file = os.path.expanduser("~/.wagit_config")
        with open(config_file, "w") as f:
            f.write(f"GROQ_API_KEY={api_key}\n")
        console.print("[bold green]✔ API Key successfully updated![/bold green]")

def save_history(repo_link, commit_msg):
    history_file = os.path.expanduser("~/.wagit_history.json")
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except Exception:
            pass
            
    entry = {
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "repo_link": repo_link,
        "commit_message": commit_msg
    }
    history.append(entry)
    
    try:
        with open(history_file, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        console.print(f"[bold red]Failed to save history: {e}[/bold red]")

def show_history():
    history_file = os.path.expanduser("~/.wagit_history.json")
    if not os.path.exists(history_file):
        console.print("[bold yellow]No commit history found.[/bold yellow]")
        return
        
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
            
        if not history:
            console.print("[bold yellow]No commit history found.[/bold yellow]")
            return
            
        table = Table(title="WAGIT Commit History", show_header=True, header_style="bold magenta")
        table.add_column("Time", style="cyan")
        table.add_column("Repository", style="green")
        table.add_column("Commit Message", style="yellow")
        
        for entry in reversed(history[-20:]):
            table.add_row(entry.get("timestamp", ""), entry.get("repo_link", ""), entry.get("commit_message", ""))
            
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Failed to read history: {e}[/bold red]")

def main():
    parser = argparse.ArgumentParser(
        description="WAGIT - Automatic Git Push CLI",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Guides & Usage:
---------------
1. Run `WAGIT` in any directory to automatically:
   - Initialize a git repository (if none exists)
   - Add a remote origin (if none exists)
   - Generate a .gitignore file (if none exists)
   - Select files to stage
   - Write a smart commit message using AI (Groq) or manually
   - Push to GitHub

2. Run `WAGIT --undo` to safely undo your last local commit while keeping your file changes.
3. Run `WAGIT --onboard` to update your Groq API Key.
4. Run `WAGIT --history` to view a log of your past commits.
"""
    )
    parser.add_argument("--undo", action="store_true", help="Undo the last local commit")
    parser.add_argument("--onboard", action="store_true", help="Update your Groq API Key")
    parser.add_argument("--history", action="store_true", help="View your commit history")
    args = parser.parse_args()

    if args.undo:
        undo_last_commit()
        return
    if args.onboard:
        onboard_api()
        return
    if args.history:
        show_history()
        return

    startup_animation()
    
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
        use_ai = Confirm.ask("[bold magenta]Use Smart AI to generate the commit message?[/bold magenta]")
        
        if use_ai:
            ai_msg = generate_ai_commit()
            if ai_msg:
                comment = Prompt.ask("[bold magenta]Edit/Confirm commit message[/bold magenta]", default=ai_msg).strip()
            else:
                comment = Prompt.ask("[bold magenta]Enter commit comment manually[/bold magenta]").strip()
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
            save_history(repo_link, comment)
        else:
            console.print("[bold red]Failed to push. Please check your credentials, permissions, and repository link.[/bold red]")

if __name__ == "__main__":
    main()
