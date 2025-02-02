import os
from github import Github
import xml.etree.ElementTree as ET


def get_github_stats(token):
    """Fetch GitHub statistics using the GitHub API."""
    # Initialize GitHub API
    g = Github(token)
    user = g.get_user("krislette")
    
    # Initialize statistics
    stats = {
        'repos': 0,
        'contributed': 0,
        'commits': 0,
        'stars': 0,
        'followers': user.get_followers().totalCount,
        'additions': 0,
        'deletions': 0
    }
    
    # Get repository count and stars
    repos = user.get_repos()
    stats['repos'] = repos.totalCount
    
    for repo in repos:
        # Count stars
        stats['stars'] += repo.stargazers_count
        
        # Count commits, additions, and deletions
        try:
            commits = repo.get_commits()
            stats['commits'] += commits.totalCount
            
            # Get weekly commit stats
            weekly_stats = repo.get_stats_code_frequency()
            if weekly_stats:
                for week in weekly_stats:
                    stats['additions'] += week.additions
                    stats['deletions'] += abs(week.deletions)  # deletions are negative
        except Exception as e:
            print(f"Error processing repo {repo.name}: {str(e)}")
    
    # Get repositories contributed to
    contributed_repos = g.search_repositories(f"contributor:{user.login}")
    stats['contributed'] = contributed_repos.totalCount
    
    return stats


def update_svg_file(stats, input_file, output_file):
    """Update the SVG file with new statistics."""
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Find and update the GitHub stats text elements
    for text in root.findall(".//{http://www.w3.org/2000/svg}text"):
        for tspan in text.findall(".//{http://www.w3.org/2000/svg}tspan"):
            if 'Repos' in tspan.text:
                # Update repos and contributed
                tspan.text = f"Repos: {stats['repos']} {{Contributed: {stats['contributed']}}}  | "
            elif 'Commits' in tspan.text:
                # Update commits and stars
                tspan.text = f"Commits: {stats['commits']}  | Stars: {stats['stars']}"
            elif 'Followers' in tspan.text:
                # Update followers and lines of code
                total_lines = stats['additions'] + stats['deletions']
                tspan.text = f"Followers: {stats['followers']}  | Lines of Code: {total_lines} ("
            elif '18,347' in tspan.text:
                # Update additions
                tspan.text = f"{stats['additions']}++"
            elif '4,088' in tspan.text:
                # Update deletions
                tspan.text = f"{stats['deletions']}--"
    
    # Save the updated SVG
    tree.write(output_file, encoding='utf-8', xml_declaration=True)


if __name__ == "__main__":
    # Get GitHub token from environment variable
    github_token = os.getenv('GH_TOKEN')
    if not github_token:
        raise ValueError("GitHub token not found in environment variables")
    
    # Get statistics
    stats = get_github_stats(github_token)
    
    # Update both SVG files
    update_svg_file(stats, 'modes/dark_mode.svg', 'modes/dark_mode.svg')
    update_svg_file(stats, 'modes/light_mode.svg', 'modes/light_mode.svg')
