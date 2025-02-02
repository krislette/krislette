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
                    stats['deletions'] += abs(week.deletions)
        except Exception as e:
            print(f"Error processing repo {repo.name}: {str(e)}")
    
    # Get repositories contributed to
    contributed_repos = g.search_repositories(f"contributor:{user.login}")
    stats['contributed'] = contributed_repos.totalCount
    
    return stats

def update_svg_file(stats, input_file, output_file):
    """Update the SVG file with new statistics."""
    # Register the SVG namespace
    ET.register_namespace('', "http://www.w3.org/2000/svg")

    tree = ET.parse(input_file)
    root = tree.getroot()

    # Find and update the GitHub stats text elements
    for text in root.findall(".//{http://www.w3.org/2000/svg}text"):
        for tspan in text.findall(".//{http://www.w3.org/2000/svg}tspan"):
            if tspan.text:
                # Update Repos and Contributed stats
                if 'Repos' in tspan.text:
                    parts = tspan.text.split()
                    if len(parts) >= 2:
                        parts[1] = str(stats['repos'])
                        if len(parts) > 4 and parts[4] == '{Contributed:':
                            parts[5] = str(stats['contributed']) + '}'
                        tspan.text = ' '.join(parts)

                # Update Commits and Stars
                elif 'Commits' in tspan.text:
                    parts = tspan.text.split()
                    if len(parts) >= 2:
                        parts[1] = str(stats['commits'])
                        if len(parts) > 4 and parts[4] == '|':
                            parts[5] = str(stats['stars'])
                        tspan.text = ' '.join(parts)

                # Update Followers and Lines of Code
                elif 'Followers' in tspan.text:
                    parts = tspan.text.split()
                    if len(parts) >= 2:
                        parts[1] = str(stats['followers'])
                        if len(parts) > 4 and parts[4] == '|':
                            additions = stats.get('additions', 0)
                            deletions = stats.get('deletions', 0)
                            total_lines = additions + deletions
                            parts[5] = str(total_lines)
                            parts[7] = f"({additions:,}++,"
                            parts[8] = f"{deletions:,}--)"
                        tspan.text = ' '.join(parts)

    # Save SVG & preserve formatting by using xml_declaration and encoding
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
