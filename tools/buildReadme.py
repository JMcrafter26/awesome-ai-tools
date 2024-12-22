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
        json.dump(details, file, indent=4)
    
    # clean_detailsJson
    with open('repos.json', 'r') as file:
        clean_detailsJson = json.load(file)

    
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
            # get categories from the clean_detailsJson, else set it to None
            'category': clean_detailsJson[detail['full_name']]['category'] if detail['full_name'] in clean_detailsJson else None,
            'sub_category': clean_detailsJson[detail['full_name']]['sub_category'] if detail['full_name'] in clean_detailsJson else None,
            # get added_at from the clean_detailsJson, else set it to Current date (in human readable format - utc)
            'added_at': clean_detailsJson[detail['full_name']]['added_at'] if detail['full_name'] in clean_detailsJson else time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        }
        clean_details.append(clean_detail)
    with open('repos.json', 'w', encoding='utf-8') as file:
        json.dump(clean_details, file, indent=4)
    print("Details saved")

# Generate the README.md file
def generateReadme(details):
    print("Sorting the details")
    # group the details by simmilar topics, only group if at least two repos have the same topic
    topics = {}
    # allowed_topics = [
    #     'speech',
    #     'music',
    #     'image',
    #     'video',
    #     'text-to-speech',
    #     'productivity',
    #     'agent',
    #     'tts',
    # ]

    # ignored_topics = [
    #     'ai',
    #     'machine-learning',
    #     'deep-learning',
    #     'python',
    #     'neural-network',
    #     'tensorflow',
    #     'keras',
    #     'pytorch',
    #     'nlp',
    #     'natural-language-processing',
    #     'gpt-3',
    #     'gpt-4',
    #     'openai',
    #     'transformer',
    #     'transformers',
    #     'chatbot',
    #     'chatgpt',
    #     'chat',
    #     'chatbot',
    #     'chatbots',
    #     'ai-chatbot',
    #     'ai-chat',
    #     'artificial-intelligence',
    #     'language-model',
    #     'large-language-model',
    #     'llm',
    #     'ollama',
    #     'gpt',
    #     'minicpm',
    #     'minicpm-v',
    #     'html',
    #     'llama',
    #     'large-language-models',
    #     'llama2',
    #     'llama-2',
    #     'llava',
    #     'llama3',
    #     'chatgpt-4',
    #     'machine-learning-compilation',
    #     'react',
    # ]
    # for detail in details:
    #     for topic in detail['topics']:
    #         # if topic not in allowed_topics:
    #             # continue
    #         if topic in ignored_topics:
    #             continue
    #         if topic not in topics:
    #             topics[topic] = []
    #         topics[topic].append(detail)

    main_topics = {
        'speech': ['speech', 'tts', 'text-to-speech', 'voice', 'voice-cloning', 'speech-synthesis'],
        'music': ['music', 'audio'],
        'image': ['image', 'vision', 'super-resolution', 'image-processing'],
        'face': ['face', 'facial-recognition', 'face-recognition', 'face-detection', 'deep-fake', 'face-swap'],
        'video': ['video', 'media'],
        'text-to-speech': ['text-to-speech'],
        'productivity': ['productivity'],
        'agent': ['agent'],
    }
    
    for detail in details:
        found = False
        for topic, subtopics in main_topics.items():
            for subtopic in subtopics:
                if subtopic in detail['topics']:
                    found = True
                    if topic not in topics:
                        topics[topic] = []
                    topics[topic].append(detail)
                    break
            if found:
                break
        if not found:
            if 'ai' in detail['topics']:
                if 'ai' not in topics:
                    topics['ai'] = []
                topics['ai'].append(detail)
            else:
                if 'other' not in topics:
                    topics['other'] = []
                topics['other'].append(detail)



    # sort the topics by the number of repos in them
    topics = dict(sorted(topics.items(), key=lambda item: len(item[1]), reverse=True))
    # remove duplicates
    for topic, repos in topics.items():
        topics[topic] = list({repo['full_name']: repo for repo in repos}.values())

    # a repo can only be in one topic, so if a repo is in multiple topics, then remove it from the less popular topic
    # create a map of repo to topic
    repo_to_topic = {}
    for topic, repos in topics.items():
        for repo in repos:
            repo_to_topic[repo['full_name']] = topic
    # remove the repo from the less popular topic
    for topic, repos in topics.items():
        for repo in repos:
            for other_topic, other_repos in topics.items():
                if other_topic == topic:
                    continue
                if repo['full_name'] in [r['full_name'] for r in other_repos]:
                    other_repos = [r for r in other_repos if r['full_name'] != repo['full_name']]
                    topics[other_topic] = other_repos


    # remove empty topics
    topics = {topic: repos for topic, repos in topics.items() if len(repos) > 0}

    # if a repo is not in any topic, then add it to the "Other" topic
    other_repos = []
    for detail in details:
        found = False
        for topic, repos in topics.items():
            for repo in repos:
                if detail['full_name'] == repo['full_name']:
                    found = True
                    break
        if not found:
            other_repos.append(detail)
    if len(other_repos) > 0:
        topics['Other'] = other_repos




    print("Generating README.md")
    with open('README-new.md', 'w', encoding='utf-8') as file:
        file.write(f"""# AWESOME AI Tools

![Banner](https://raw.githubusercontent.com/JMcrafter26/awesome-ai-tools/main/.github/banner.jpg)

A list of AWESOME AI tools on Github
""")
        # Table of contents
        file.write("\n## Table of Contents\n")
        for topic in topics.keys():
            file.write(f"- [{topic}](#{topic.lower().replace(' ', '-')}) - {len(topics[topic])} repos\n")
        file.write("\n")
        # Topics
        for topic, repos in topics.items():
            file.write(f"\n## {topic}\n")
            for repo in repos:
                file.write(f"\n### [{repo['name']}]({repo['html_url']})\n")
                file.write(f"{repo['description']}\n\n")
                file.write(f"Stars: {repo['stargazers_count']} | Forks: {repo['forks_count']} | Issues: {repo['open_issues_count']}\n")
                file.write(f"Language: {repo['language']} | License: {repo['license']['name'] if repo['license'] else 'None'}\n")
                file.write(f"Topics: {', '.join(repo['topics'])}\n")
                file.write(f"\n")

    print("README.md generated")

# Main function
def main():
    print("Starting script")
    links = getLinks()
    details = getDetails(links)
    generateReadme(details)
    print("Script finished")

# Run the main function
if __name__ == '__main__':
    main()