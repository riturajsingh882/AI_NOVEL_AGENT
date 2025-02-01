from git import Repo, GitError
import os
from datetime import datetime
import logging
import yaml
from pathlib import Path

class GitManager:
    def __init__(self):
        self.repo_path = Path(__file__).parent.parent
        self.repo = Repo(self.repo_path)
        
        # Load GitHub credentials from config
        config_path = self.repo_path / 'config' / 'api_config.yaml'
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Set authenticated remote URL
        repo_name = "AI_NOVEL"  # REPLACE WITH YOUR REPO NAME
        remote_url = (
            f"https://{config['GITHUB']['username']}:{config['GITHUB']['token']}"
            f"@github.com/{config['GITHUB']['username']}/{repo_name}.git"
        )
        self.repo.git.remote("set-url", "origin", remote_url)

        # Configure commit author identity
        self.repo.git.config("--local", "user.name", config['GITHUB']['username'])
        self.repo.git.config("--local", "user.email", config['GITHUB']['email'])

    def commit_changes(self):
        try:
            if not self.repo.index.diff("HEAD") and not self.repo.untracked_files:
                logging.warning("No changes to commit")
                return

            self.repo.git.add(all=True)
            commit_msg = f"Daily Write: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.repo.index.commit(commit_msg)
            
            origin = self.repo.remote(name='origin')
            origin.push(refspec='main:main')
            
        except GitError as e:
            logging.error(f"Git operation failed: {str(e)}")
            raise