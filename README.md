# WGIT :rocket:

An automatic, interactive command-line tool to push your code to GitHub without having to remember or type out complex git commands.

## Installation

```bash
pip install WGIT
```

## Features

- **Automated Workflow**: Automatically initializes a git repository, detects current branches, and pushes your code.
- **Interactive File Staging**: Choose whether to stage all files or selectively pick which files you want to commit using a beautiful checkbox menu.
- **Changed Files Summary**: View a color-coded table of all Modified, Added, and Deleted files before you commit.
- **Conventional Commits**: Optionally select conventional commit prefixes (e.g., `feat:`, `fix:`) from a dropdown menu to keep your git history professional.
- **Automatic `.gitignore`**: If your project is missing one, `WGIT` can instantly generate a `.gitignore` file for your specific programming language by fetching the official template from GitHub.
- **Undo Mistakes**: Safely revert your last local commit while preserving all your file changes with a single flag.

## Usage

Simply run the `WGIT` command inside any directory you want to push to GitHub:

```bash
WGIT
```

**To undo your last commit:**
```bash
WGIT --undo
```
