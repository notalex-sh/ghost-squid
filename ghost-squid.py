#!/usr/bin/env python3
"""
ghost squid - Discover GitHub accounts from email addresses

does require you to have an api token

by notalex.sh
"""

import argparse
import base64
import json
import os
import random
import string
import sys
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from getpass import getpass
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

class Color:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


API = "https://api.github.com"
API_VER = "2022-11-28"
ENV_FILE = Path(".env")
GITIGNORE = Path(".gitignore")

def colored(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}"

def print_banner():
    # print cool banner
    banner = r"""
       _               _                   _     _ 
  __ _| |__   ___  ___| |_   ___  __ _ _  _(_) __| |
 / _` | '_ \ / _ \/ __| __| / __|/ _` | || | |/ _` |
| (_| | | | | (_) \__ \ |_  \__ \ (_| | || | | (_| |
 \__, |_| |_|\___/|___/\__| |___/\__, |\_,_|_|\__,_|
 |___/                                |_|            
                                                
    """ + colored("Discover GitHub accounts from emails", Color.CYAN)
    print(colored(banner, Color.MAGENTA))
    print(colored("⚠️  ETHICAL USE ONLY - Use responsibly\n", Color.YELLOW))

class GitHubAPI:
    # handles GitHub API interactions
    
    def __init__(self, token: str):
        self.token = token
        self.user_cache = None
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VER,
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "ghost-squid/1.0",
        }
    
    def request(self, method: str, path: str, body: Optional[Dict] = None) -> Dict:
        data = None if body is None else json.dumps(body).encode("utf-8")
        url = f"{API}{path}"
        
        try:
            req = Request(url, data=data, method=method, headers=self._headers())
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            try:
                error_json = json.loads(error_body)
                message = error_json.get("message", str(e))
            except:
                message = str(e)
            raise Exception(f"API error ({e.code}): {message}")
    
    def get_user(self) -> Dict:
        if self.user_cache is None:
            self.user_cache = self.request("GET", "/user")
        return self.user_cache
    
    def create_repo(self, name: str) -> Dict:
        # creates a temp repository to make commit
        body = {
            "name": name,
            "private": True,
            "auto_init": True,
            "description": "Temporary probe - will be deleted"
        }
        return self.request("POST", "/user/repos", body)
    
    def delete_repo(self, owner: str, repo: str):
        # deletes the temp repo
        req = Request(f"{API}/repos/{owner}/{repo}", method="DELETE", headers=self._headers())
        with urlopen(req, timeout=30):
            pass
    
    def create_commit(self, owner: str, repo: str, email: str) -> str:
        # create commit with email as author
        content = base64.b64encode(f"probe {email}".encode()).decode()
        
        body = {
            "message": f"probe: {email}",
            "content": content,
            "author": {
                "name": random_name(),
                "email": email,
                "date": random_date()
            },
            "committer": {
                "name": "Probe Bot",
                "email": "bot@phantom.local",
                "date": random_date()
            }
        }
        
        result = self.request("PUT", f"/repos/{owner}/{repo}/contents/probe.txt", body)
        return result["commit"]["sha"]
    
    def get_commit_author(self, owner: str, repo: str, sha: str) -> Tuple[str, str]:
        # get GitHub username from commit
        for _ in range(8):
            data = self.request("GET", f"/repos/{owner}/{repo}/commits/{sha}")
            user = data.get("author") or {}
            email = (data.get("commit") or {}).get("author", {}).get("email", "")
            
            if user.get("login"):
                return user["login"], email
            time.sleep(1.0)
        
        return "", email
    
    def get_profile(self, username: str) -> Dict:
        # get user profile
        if not username:
            return {}
        return self.request("GET", f"/users/{username}")

def random_name() -> str:
    first = ["John", "Joe", "Fred"]
    last = ["Doe", "Bloggs", "Nurk", "Public"]
    return f"{random.choice(first)} {random.choice(last)}"

def random_date(days: int = 30) -> str:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    delta = (now - start).total_seconds()
    random_time = start + timedelta(seconds=random.randrange(int(delta)))
    return random_time.isoformat()

def random_repo_name() -> str:
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"tmp-probe-{int(time.time())}-{suffix}"

def validate_email(email: str) -> bool:
    # basic email validation
    return "@" in email and "." in email.split("@")[1]

def load_env() -> Dict[str, str]:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env

def save_token(token: str):
    env = load_env()
    env["GITHUB_TOKEN"] = token.strip()
    
    ENV_FILE.write_text("\n".join(f"{k}={v}" for k, v in env.items()) + "\n")
    try:
        lines = GITIGNORE.read_text().splitlines() if GITIGNORE.exists() else []
        if ".env" not in lines:
            lines.append(".env")
            GITIGNORE.write_text("\n".join(lines) + "\n")
    except:
        pass

def get_token(no_browser: bool = False) -> str:
    # tries environment
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        return token.strip()
    
    # tries .env file
    env = load_env()
    if "GITHUB_TOKEN" in env:
        return env["GITHUB_TOKEN"].strip()
    
    # prompt user if not found
    print("No GitHub token found.")
    if not no_browser:
        print("Opening token page (fine-grained token suggested: Contents=write, Administration=write)...")
        webbrowser.open("https://github.com/settings/tokens/new?description=ghost-squid-osint&scopes=repo,delete_repo")
        print("Alternatively, classic token: https://github.com/settings/tokens")
    else:
        print("Create token at: https://github.com/settings/personal-access-tokens/new")
        print("Or classic token: https://github.com/settings/tokens/new?description=ghost-squid-osint&scopes=repo,delete_repo")
    
    token = getpass("Paste your GitHub Personal Access Token: ").strip()
    
    if not token:
        sys.exit("No token provided.")
    
    try:
        api = GitHubAPI(token)
        user = api.get_user()
        if "login" not in user:
            raise ValueError("Token did not return a user.")
    except Exception as e:
        sys.exit(f"Token validation failed: {e}")
    
    save_token(token)
    print("Saved token to .env (GITHUB_TOKEN=...).")
    
    return token

def print_result(email: str, username: str, profile: Dict):
    print()
    
    if username:
        print(colored("✓ ACCOUNT FOUND", Color.GREEN + Color.BOLD))
        print(f"{colored('Email:', Color.CYAN)}     {email}")
        print(f"{colored('Username:', Color.CYAN)}  {colored(username, Color.GREEN + Color.BOLD)}")
        
        if profile.get("name"):
            print(f"{colored('Name:', Color.CYAN)}     {profile['name']}")
        if profile.get("html_url"):
            print(f"{colored('Profile:', Color.CYAN)}  {profile['html_url']}")
        if profile.get("bio"):
            bio = profile['bio'][:80] + "..." if len(profile.get('bio', '')) > 80 else profile.get('bio', '')
            print(f"{colored('Bio:', Color.CYAN)}      {bio}")
        if profile.get("location"):
            print(f"{colored('Location:', Color.CYAN)} {profile['location']}")
        if profile.get("company"):
            print(f"{colored('Company:', Color.CYAN)}  {profile['company']}")
        
        stats = []
        if profile.get("public_repos") is not None:
            stats.append(f"{profile['public_repos']} repos")
        if profile.get("followers") is not None:
            stats.append(f"{profile['followers']} followers")
        if stats:
            print(f"{colored('Stats:', Color.CYAN)}    {', '.join(stats)}")
    else:
        print(colored("✗ NO ACCOUNT FOUND", Color.YELLOW + Color.BOLD))
        print(f"{colored('Email:', Color.CYAN)} {email}")
        print(colored("\nThis email is not linked to any GitHub account", Color.DIM))
        print(colored("or the user has email privacy enabled.", Color.DIM))
    
    print()

def main():
    parser = argparse.ArgumentParser(
        prog='ghost-squid',
        description='Discover GitHub accounts from email addresses',
        epilog='Use ethically and responsibly'
    )
    
    parser.add_argument('email', help='Email address to probe')
    parser.add_argument('--keep', action='store_true', help='Keep temporary repository')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t open browser for token')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--no-banner', action='store_true', help='Skip banner')
    
    args = parser.parse_args()
    
    if not args.json and not args.no_banner:
        print_banner()
    
    # validate email
    if not validate_email(args.email):
        sys.exit(colored(f"✗ Invalid email: {args.email}", Color.RED))
    
    # get token
    token = get_token(args.no_browser)
    api = GitHubAPI(token)
    
    # get authenticated user
    me = api.get_user()
    owner = me["login"]
    
    if not args.json:
        print(colored(f"🔐 Authenticated as: {owner}\n", Color.DIM))
    
    # create repository
    repo_name = random_repo_name()
    
    try:
        if not args.json:
            print(colored("⚡ Creating temporary repository...", Color.BLUE), end='', flush=True)
        
        api.create_repo(repo_name)
        
        if not args.json:
            print(colored(" ✓", Color.GREEN))
        
        try:
            # create commit
            if not args.json:
                print(colored("⚡ Creating probe commit...", Color.BLUE), end='', flush=True)
            
            sha = api.create_commit(owner, repo_name, args.email)
            
            if not args.json:
                print(colored(" ✓", Color.GREEN))
                print(colored("⚡ Resolving GitHub account...", Color.BLUE), end='', flush=True)
            
            # resolve username
            username, _ = api.get_commit_author(owner, repo_name, sha)
            
            if not args.json:
                print(colored(" ✓", Color.GREEN))
            
            # get profile
            profile = api.get_profile(username) if username else {}
            
            # output
            if args.json:
                result = {
                    "email": args.email,
                    "github_username": username or None,
                    "display_name": profile.get("name"),
                    "profile_url": profile.get("html_url"),
                    "linked": bool(username)
                }
                print(json.dumps(result, indent=2))
            else:
                print_result(args.email, username, profile)
        
        finally:
            # cleanup
            if args.keep:
                url = f"https://github.com/{owner}/{repo_name}"
                if not args.json:
                    print(colored(f"💾 Repository kept: {url}", Color.CYAN))
            else:
                try:
                    if not args.json:
                        print(colored("🧹 Cleaning up...", Color.DIM), end='', flush=True)
                    api.delete_repo(owner, repo_name)
                    if not args.json:
                        print(colored(" ✓\n", Color.GREEN))
                except Exception as e:
                    if not args.json:
                        print(colored(f"\n⚠️  Failed to delete repo: {e}", Color.YELLOW))
    
    except Exception as e:
        print(colored(f"\n✗ Error: {e}", Color.RED))
        sys.exit(1)
    except KeyboardInterrupt:
        print(colored("\n\n⚠️  Interrupted by user\n\nTemp repos may not be deleted", Color.YELLOW))
        sys.exit(130)

if __name__ == "__main__":
    main()
