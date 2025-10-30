# ghost squid 🦑

Discover GitHub accounts associated with email addresses using commit author linking.

---

## What It Does

**ghost squid** probes email addresses to find linked GitHub accounts. It works by:

1. Creating a temporary private repository
2. Making a commit with the target email as the author
3. Checking if GitHub automatically links that commit to a user account
4. Fetching the full profile if found
5. Cleaning up by deleting the temporary repository

This leverages GitHub's automatic linking of commits to accounts when the email matches a verified email address.

---

## Quick Start

### Installation

```bash
# Download the script
git clone https://github.com/notalex-sh/ghost-squid.git
```

**Requirements:** Python 3.7+ (no external dependencies)

### First Run

On first run, you'll need a GitHub Personal Access Token:

```bash
python3 ghost-squid.py user@example.com
```

The script will:
1. Detect no token is configured
2. Open your browser to GitHub's token creation page
3. Pre-fill the token description and required scopes
4. Prompt you to paste the token (input is hidden)
5. Validate and save the token to `.env`

**Token Permissions Required:**
- `repo` (full control of repositories)
- `delete_repo` (to clean up temporary repos)

---

## Usage

### Basic Examples

```bash
# Probe a single email
python3 ghost-squid.py octocat@github.com

# Get JSON output (for scripting)
python3 ghost-squid.py user@example.com --json

# Keep the temporary repo (for inspection)
python3 ghost-squid.py user@example.com --keep

# Skip the banner
python3 ghost-squid.py user@example.com --no-banner
```

### Output Examples

**When account is found:**
```
       _               _                   _     _ 
  __ _| |__   ___  ___| |_   ___  __ _ _  _(_) __| |
 / _` | '_ \ / _ \/ __| __| / __|/ _` | || | |/ _` |
| (_| | | | | (_) \__ \ |_  \__ \ (_| | || | | (_| |
 \__, |_| |_|\___/|___/\__| |___/\__, |\_,_|_|\__,_|
 |___/                                |_|            
                                                
Discover GitHub accounts from emails
⚠️  ETHICAL USE ONLY - Use responsibly

🔐 Authenticated as: yourusername

⚡ Creating temporary repository... ✓
⚡ Creating probe commit... ✓
⚡ Resolving GitHub account... ✓
🧹 Cleaning up... ✓

✓ ACCOUNT FOUND
Email:     octocat@github.com
Username:  octocat
Name:      The Octocat
Profile:   https://github.com/octocat
Location:  San Francisco
Company:   @github
Stats:     8 repos, 4952 followers
```

**When no account found:**
```
✗ NO ACCOUNT FOUND
Email: unknown@example.com

This email is not linked to any GitHub account
or the user has email privacy enabled.
```

**JSON output (`--json`):**
```json
{
  "email": "octocat@github.com",
  "github_username": "octocat",
  "display_name": "The Octocat",
  "profile_url": "https://github.com/octocat",
  "linked": true
}
```

---

## Advanced Usage

### Batch Processing

Process multiple emails with a shell loop:

```bash
# From a file (one email per line)
while read email; do
  python3 ghost-squid.py "$email" --json --no-banner
  sleep 2  # Rate limiting
done < emails.txt
```

### Automation

```bash
# Save all results to a file
for email in $(cat emails.txt); do
  .python3 ghost-squid.py "$email" --json --no-banner >> results.jsonl
  sleep 2
done

# Then analyze
jq -s 'map(select(.linked == true)) | length' results.jsonl  # Count found
jq -r 'select(.linked) | .github_username' results.jsonl    # List usernames
```

---

## Command-Line Options

```
usage: ghost-squid.py [-h] [--keep] [--no-browser] [--json] [--no-banner] email

positional arguments:
  email          Email address to probe

options:
  -h, --help     Show this help message and exit
  --keep         Keep the temporary repository instead of deleting
  --no-browser   Don't open browser automatically for token setup
  --json         Output results as JSON (no colors/formatting)
  --no-banner    Skip the ASCII art banner
```

---

## How It Works

### The Technique

GitHub has a feature where commits are automatically associated with user accounts:

1. When you push a commit, GitHub looks at the commit's author email
2. If that email matches a verified email on a GitHub account, GitHub links them
3. The commit then shows the user's profile picture and links to their account
4. This linking is visible via the GitHub API

**ghost squid** exploits this behavior for OSINT purposes by:
- Creating commits with target emails as authors
- Checking if GitHub creates the link
- Retrieving the profile if a link exists

### Rate Limits

GitHub API has rate limits:
- **5,000 requests/hour** (authenticated)
- **Repository creation**: 20-50/hour (soft limit)

Each probe uses 5-6 API calls and creates 1 repository, so you can safely probe 20-50 emails per hour.

---

## Configuration

### Token Storage

The token is stored in `.env` in the current directory:

```bash
# .env file contents
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The `.env` file is automatically added to `.gitignore` to prevent accidental commits.

### Alternative: Environment Variable

```bash
# Set token as environment variable (doesn't save to file)
export GITHUB_TOKEN="ghp_your_token_here"
```

### Token Scopes

**Required permissions:**
- `repo` - Create and read repositories
- `delete_repo` - Delete temporary repositories

**Why these scopes:**
- Creating private repos requires `repo` access
- Automatic cleanup requires `delete_repo` permission
- Without `delete_repo`, you'll need to manually delete temp repos

---

## Security & Privacy

This technique only reveals information that GitHub makes semi-public:
- If email is verified and linking is enabled, it's discoverable
- To prevent discovery: enable email privacy in GitHub settings
- No notification is sent when this technique is used
- No way to detect if you've been probed

**GitHub Privacy Settings:**
1. Go to: https://github.com/settings/emails
2. Check: "Keep my email addresses private"
3. Check: "Block command line pushes that expose my email"

---

**Use responsibly and only with proper authorization.**