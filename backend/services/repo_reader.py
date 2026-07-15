import os
import shutil
import git


def normalize_repo_url(repo_url: str) -> str:
    """Accept a Git URL or a browser-style GitHub repository address."""
    repo_url = repo_url.strip()
    if not repo_url:
        raise ValueError("Repository URL cannot be empty.")
    if "://" not in repo_url and not repo_url.startswith("git@"):
        return f"https://{repo_url}"
    return repo_url


def clone_repo(repo_url: str, clone_dir: str = "cloned_repo") -> str:
    """
    Clones a GitHub repo to a local folder.
    If the folder already exists, deletes it first (so we always get a fresh clone).
    Returns the path where it was cloned.
    """
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)

    repo_url = normalize_repo_url(repo_url)
    print(f"Cloning {repo_url} into {clone_dir} ...")
    git.Repo.clone_from(repo_url, clone_dir)
    print("Clone complete.")

    return clone_dir


if __name__ == "__main__":
    # small test repo, quick to clone
    test_url = "https://github.com/octocat/Hello-World"
    path = clone_repo(test_url)
    print("Repo cloned at:", path)

    # list what's inside it
    print("\nFiles found:")
    for root, dirs, files in os.walk(path):
        # skip the hidden .git folder
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            print(os.path.join(root, f))
