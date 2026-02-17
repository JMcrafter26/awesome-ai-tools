#!/usr/bin/env python3
"""
Check for repositories that haven't received commits in over 2 years
and categorize them as outdated.
"""

import json
import requests
from datetime import datetime, timedelta
import time
import os

def load_repos():
    """Load repositories from repos.json"""
    with open('repos.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_last_commit_date(owner, repo, github_token=None):
    """
    Get the last commit date for a repository
    Returns: datetime object or None if error
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        response = requests.get(url, headers=headers, params={'per_page': 1})
        if response.status_code == 200:
            commits = response.json()
            if commits and len(commits) > 0:
                commit_date_str = commits[0]['commit']['committer']['date']
                return datetime.strptime(commit_date_str, '%Y-%m-%dT%H:%M:%SZ')
        elif response.status_code == 409:
            # Repository is empty
            return None
        else:
            print(f"  ⚠️  Error {response.status_code} for {owner}/{repo}")
            return None
    except Exception as e:
        print(f"  ❌ Exception for {owner}/{repo}: {e}")
        return None

def check_outdated_repos(days_threshold=730):
    """
    Check all repos and identify which are outdated (no commits in X days)
    Default: 730 days = 2 years
    """
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  Warning: GITHUB_TOKEN not found in environment variables.")
        print("   API rate limits will be much lower (60 requests/hour).")
        print("   Set GITHUB_TOKEN to increase to 5000 requests/hour.\n")
    
    repos = load_repos()
    threshold_date = datetime.now() - timedelta(days=days_threshold)
    
    outdated = []
    active = []
    errors = []
    
    print(f"Checking {len(repos)} repositories...")
    print(f"Threshold: Last commit before {threshold_date.strftime('%Y-%m-%d')}\n")
    
    for i, repo_data in enumerate(repos, 1):
        owner = repo_data['owner']
        repo = repo_data['name']
        full_name = f"{owner}/{repo}"
        
        print(f"[{i}/{len(repos)}] Checking {full_name}...", end=' ')
        
        last_commit = get_last_commit_date(owner, repo, github_token)
        
        if last_commit is None:
            print("⚠️  Could not fetch")
            errors.append({
                'repo': full_name,
                'data': repo_data
            })
        elif last_commit < threshold_date:
            days_ago = (datetime.now() - last_commit).days
            print(f"🔴 OUTDATED (last commit: {last_commit.strftime('%Y-%m-%d')}, {days_ago} days ago)")
            outdated.append({
                'repo': full_name,
                'last_commit': last_commit.strftime('%Y-%m-%d'),
                'days_ago': days_ago,
                'data': repo_data
            })
        else:
            days_ago = (datetime.now() - last_commit).days
            print(f"✅ Active (last commit: {last_commit.strftime('%Y-%m-%d')}, {days_ago} days ago)")
            active.append({
                'repo': full_name,
                'last_commit': last_commit.strftime('%Y-%m-%d'),
                'days_ago': days_ago,
                'data': repo_data
            })
        
        # Rate limiting: small delay between requests
        time.sleep(0.1)
    
    # Generate report
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total repositories checked: {len(repos)}")
    print(f"Active (commits within 2 years): {len(active)}")
    print(f"Outdated (no commits in 2+ years): {len(outdated)}")
    print(f"Errors: {len(errors)}")
    
    if outdated:
        print("\n" + "="*80)
        print("OUTDATED REPOSITORIES")
        print("="*80)
        outdated_sorted = sorted(outdated, key=lambda x: x['days_ago'], reverse=True)
        for item in outdated_sorted:
            print(f"  • {item['repo']}")
            print(f"    Last commit: {item['last_commit']} ({item['days_ago']} days ago)")
            print(f"    URL: {item['data']['html_url']}")
            print()
    
    # Save results to JSON
    results = {
        'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'threshold_days': days_threshold,
        'threshold_date': threshold_date.strftime('%Y-%m-%d'),
        'summary': {
            'total': len(repos),
            'active': len(active),
            'outdated': len(outdated),
            'errors': len(errors)
        },
        'outdated_repos': outdated_sorted if outdated else [],
        'errors': errors
    }
    
    with open('outdated_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n📄 Full report saved to: outdated_report.json")
    
    return results

def create_outdated_section(outdated_repos):
    """
    Generate markdown for an 'Archived/Outdated' section
    """
    if not outdated_repos:
        return ""
    
    section = "\n## Archived Projects\n\n"
    section += "_These projects haven't been updated in over 2 years and may be unmaintained._\n\n"
    
    for item in sorted(outdated_repos, key=lambda x: x['data']['name'].lower()):
        data = item['data']
        section += f"- **[{data['name']}]({data['html_url']})** - {data['description']} "
        section += f"![Stars](https://img.shields.io/github/stars/{data['owner']}/{data['name']}?style=flat-square) "
        section += f"_(Last updated: {item['last_commit']})_\n"
    
    return section

if __name__ == "__main__":
    print("🔍 Checking for outdated repositories...\n")
    results = check_outdated_repos()
    
    # Optionally generate markdown section
    if results['outdated_repos']:
        print("\n" + "="*80)
        print("MARKDOWN SECTION FOR OUTDATED REPOS")
        print("="*80)
        print(create_outdated_section(results['outdated_repos']))
