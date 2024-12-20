import os
import json
import requests
import time
import dotenv

# What is this?
"""
This is a script to generate a README.md file for the repository.

Here is how it works:
- It will get all links from the repos from the urls.txt file.
- Then it will get the details from the github api and save it in a json file (repos.json).
- Then it will generate a README.md file with the details from the json file.
"""

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
    for link in links:
        # if the link is not a github link, then skip it
        if 'github.com' not in link:
            print(f"Skipping: {link}")
            continue
        # if it already is in the json file, then skip it
        if os.path.exists('repos.json'):
            with open('repos.json', 'r') as file:
                data = json.load(file)
                for d in data:
                    if link in d['html_url']:
                        print(f"Already in the json file: {link}")
                        details.append(d)
                        continue
                    
        # convert the URL to a user/repo format
        link = link.replace('https://github.com/', '')
        # if there is something after the repo name, like a "/", "?", or "#", then remove it
        print(f"Link: {link}")
        if '?' in link:
            link = link.split('?')[0]
        if '#' in link:
            link = link.split('#')[0]
        # if there is a second "/" in the link, then remove everything after it
        if link.count('/') > 1:
            link = link[:link.index('/', link.index('/') + 1)]

        
        # print(f"Getting details for: {link}")

        # get the details from the github api
        url = f"https://api.github.com/repos/{link}"
        print(f"Getting details for: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            details.append(data)
            print(f"Details for {link}: {data}")
        else:
            print(f"Failed to get details for {link}: {response.status_code}")
        time.sleep(1)  # sleep for 1 second to avoid rate limiting
    return details

# Save the details in a json file
def saveDetails(details):
    print("Saving details to repos.json")
    with open('repos.json', 'w') as file:
        json.dump(details, file, indent=4)
    print("Details saved")

# Generate the README.md file
def generateReadme(details):
    print("Generating README.md")
    with open('README-new.md', 'w') as file:
        file.write(f"# Awesome Repositories\n\n")
        for detail in details:
            file.write(f"## [{detail['name']}]({detail['html_url']})\n")
            file.write(f"{detail['description']}\n\n")
            file.write(f"**Language:** {detail['language']}\n\n")
            file.write(f"**Stars:** {detail['stargazers_count']} | **Forks:** {detail['forks_count']} | **Watchers:** {detail['watchers_count']}\n\n")
            file.write(f"**Created At:** {detail['created_at'].split('T')[0]} | **Updated At:** {detail['updated_at'].split('T')[0]}\n\n")
            file.write(f"---\n\n")
    print("README.md generated")

# Main function
def main():
    print("Starting script")
    links = getLinks()
    details = getDetails(links)
    saveDetails(details)
    generateReadme(details)
    print("Script finished")

# Run the main function
if __name__ == '__main__':
    main()