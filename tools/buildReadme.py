import os
import json
import requests
import time
from dotenv import load_dotenv
import sys

# What is this?
"""
This is a script to generate a README.md file for the repository.

Here is how it works:
- It will get all links from the repos from the urls.txt file.
- Then it will get the details from the github api and save it in a json file (repos_raw.json).
- Then it will generate a README.md file with the details from the json file.
"""

# Load the environment variables
load_dotenv()
githubToken = os.getenv('GITHUB_TOKEN')
if not githubToken:
    print("GitHub Token not found, yoy may encounter rate limiting")

# Get the links from the urls.txt file
def getLinks():
    print("Getting links from urls.txt")
    links = []

    # read the links from the file
    with open('urls.txt', 'r') as file:
        content = file.read()
        for line in content.splitlines():
            links.append(line.strip())

    # remove duplicates and save it back to the file
    links = list(set(links))
    with open('urls.txt', 'w') as file:
        for link in links:
            file.write(f"{link}\n")

    print(f"Found {len(links)} links")  # Debug print
    return links


# Get the details from the github api
def getDetails(links):
    print("Getting details from GitHub API")
    details = []
    if not os.path.exists('repos_raw.json'):
        saveDetails(details)
    with open('repos_raw.json', 'r') as file:
        data = json.load(file)
        for d in data:
            details.append(d)
    for link in links:
        # if the link is not a github link, then skip it
        if 'github.com' not in link:
            print(f"Skipping: {link}")
            continue
                    
        # convert the URL to a user/repo format
        repo = link.replace('https://github.com/', '')
        # if there is something after the repo name, like a "/", "?", or "#", then remove it
        print(f"Link: {repo}")
        if '?' in repo:
            repo = repo.split('?')[0]
        if '#' in repo:
            repo = repo.split('#')[0]
        # if there is a second "/" in the repo, then remove everything after it
        if repo.count('/') > 1:
            repo = repo[:repo.index('/', repo.index('/') + 1)]

        # check if the details are already in the json file
        found = False
        for detail in details:
            if repo in detail['full_name']:
                found = True
                break
        if found:
            print(f"Already in the json file: {repo}")
            continue

        
        # print(f"Getting details for: {repo}")

        # get the details from the github api
        url = f"https://api.github.com/repos/{repo}"
        headers = {
            'Authorization': f'token {githubToken}'
        }
        print(f"Getting details for: {url}")
        response = requests.get(url, headers=headers)
        # print(response.json())
        if response.status_code == 200:
            data = response.json()
            details.append(data)
            print(f"Got details for: {repo}")
            saveDetails(details)
        # if is rate limited
        elif 'API rate limit exceeded' in response.json()['message']:

            print(f"Rate limited, saving details to repos_raw.json")
            with open('repos_raw.json', 'w') as file:
                json.dump(details, file, indent=4)
            print("Details saved")
            break
        elif response.status_code == 404:
            print(f"Repository not found: {repo}")
        else:
            print(f"Failed to get details for {repo}: {response.json()['message']}")
        time.sleep(0.2)  # sleep to avoid rate limiting
    return details

# Save the details in a json file
def saveDetails(details):
    print("Saving details to repos_raw.json")
    with open('repos_raw.json', 'w', encoding='utf-8') as file:
        json.dump(details, f, indent=4)
    
    # Load existing clean details from repos.json
    existing_clean = {}
    try:
        with open('repos.json', 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
            existing_clean = {repo['full_name']: repo for repo in existing_data}
    except FileNotFoundError:
        pass
    
    # Create clean details for new/updated repos
    clean_details = []
    for detail in details:
        clean_detail = {
            'repo': detail['full_name'],
            'full_name': detail['full_name'],
            'name': detail['name'],
            'owner': detail['owner']['login'],
            'description': detail['description'],
            'html_url': detail['html_url'],
            'stargazers_count': detail['stargazers_count'],
            'forks_count': detail['forks_count'],
            'open_issues_count': detail['open_issues_count'],
            'language': detail['language'],
            'license': detail['license']['spdx_id'] if detail['license'] else None,
            'topics': detail['topics'],
            'category': existing_clean[detail['full_name']]['category'] if detail['full_name'] in existing_clean else None,
            'sub_category': existing_clean[detail['full_name']]['sub_category'] if detail['full_name'] in existing_clean else None,
            'added_at': existing_clean[detail['full_name']]['added_at'] if detail['full_name'] in existing_clean else time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        }
        existing_clean[detail['full_name']] = clean_detail
    
    # Write all repos (existing + new) back to repos.json
    all_repos = list(existing_clean.values())
    with open('repos.json', 'w', encoding='utf-8') as file:
        json.dump(all_repos, file, indent=4)
    print(f"Details saved - Total repos in repos.json: {len(all_repos)}")

# Generate the README.md file
def generateReadme(details):
    print("Sorting the details")
    
    # Define categories with better organization
    category_mapping = {
        'Text Generation & LLMs': [
            'gpt', 'llm', 'language-model', 'text-generation', 'chatbot', 'chatgpt', 'llama',
            'autonomous-agents', 'agent', 'rag', 'embeddings'
        ],
        'Voice & Speech': [
            'speech', 'tts', 'text-to-speech', 'voice', 'voice-cloning', 'speech-synthesis',
            'audio-generation', 'voice-clone'
        ],
        'Music & Audio': [
            'music', 'audio', 'sound'
        ],
        'Image Generation': [
            'image-generation', 'stable-diffusion', 'diffusion', 'text-to-image'
        ],
        'Image Enhancement': [
            'image-restoration', 'super-resolution', 'image-processing', 'face-restoration'
        ],
        'Face & Video': [
            'face', 'facial-recognition', 'face-recognition', 'face-detection', 
            'deep-fake', 'face-swap', 'face-animation', 'lip-sync', 'video-generation',
            'video', 'video-editing', 'video-animation', 'image-animation'
        ],
        'Development Tools': [
            'productivity', 'developer-tools', 'code', 'api', 'framework'
        ],
        'Observability & Monitoring': [
            'observability', 'monitoring', 'ai-observability', 'mlops', 'llmops'
        ],
    }
    
    # Categorize repos
    categorized = {}
    uncategorized = []
    
    for detail in details:
        detail_topics = [t.lower() for t in detail.get('topics', [])]
        detail_desc = (detail.get('description', '') or '').lower()
        
        found_category = False
        for category, keywords in category_mapping.items():
            if any(keyword in detail_topics or keyword in detail_desc for keyword in keywords):
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(detail)
                found_category = True
                break
        
        if not found_category:
            uncategorized.append(detail)
    
    # Add uncategorized to "Other" if exists
    if uncategorized:
        categorized['Other'] = uncategorized

    # Remove duplicates within categories
    for category in categorized:
        seen = {}
        for repo in categorized[category]:
            seen[repo['full_name']] = repo
        categorized[category] = list(seen.values())
    
    # Sort by stars within each category
    for category in categorized:
        categorized[category].sort(key=lambda x: x['stargazers_count'], reverse=True)

    print("Generating README.md")
    with open('README.md', 'w', encoding='utf-8') as file:
        # Header
        file.write("# Awesome AI Tools [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)\n\n")
        file.write("> A curated list of awesome AI tools and repositories on GitHub\n\n")
        
        # Add contribution guide
        file.write("## Contents\n\n")
        for category in categorized.keys():
            anchor = category.lower().replace(' ', '-').replace('&', '').replace('  ', '-')
            file.write(f"- [{category}](#{anchor})\n")
        file.write("- [Contributing](#contributing)\n\n")
        
        # Categories with repos
        for category, repos in categorized.items():
            anchor = category.lower().replace(' ', '-').replace('&', '').replace('  ', '-')
            file.write(f"## {category}\n\n")
            
            for repo in repos:
                name = repo['name']
                url = repo['html_url']
                desc = repo.get('description', 'No description provided.')
                stars = repo['stargazers_count']
                
                # Format with bold name and description (AWESOME list style)
                file.write(f"- **[{name}]({url})** - {desc} ![Stars](https://img.shields.io/github/stars/{repo['full_name']}?style=flat-square)\n")
            
            file.write("\n")
        
        # Footer
        file.write("## Contributing\n\n")
        file.write("Contributions are welcome! Please feel free to submit a Pull Request.\n\n")
        file.write("To add a new tool:\n")
        file.write("1. Add the GitHub URL to `urls.txt`\n")
        file.write("2. Run `python tools/buildReadme.py`\n")
        file.write("3. Submit a PR with your changes\n\n")
        file.write("---\n\n")
        file.write("Made with ❤️ by [JMcrafter26](https://github.com/JMcrafter26)\n")

    print("README.md generated")

# Main function
def main():
    print("Starting script")
    links = getLinks()
    details = getDetails(links)
    
    # Also load from repos.json to include manually added repos
    print("Loading existing repos from repos.json")
    with open('repos.json', 'r', encoding='utf-8') as file:
        existing_repos = json.load(file)
    
    # Merge details with existing repos (prioritize existing if duplicate)
    details_map = {repo['full_name']: repo for repo in details}
    for repo in existing_repos:
        if repo['full_name'] not in details_map:
            details_map[repo['full_name']] = repo
    
    details = list(details_map.values())
    print(f"Total repos to process: {len(details)}")
    
    generateReadme(details)
    print("Script finished")

# Run the main function
if __name__ == '__main__':
    main()