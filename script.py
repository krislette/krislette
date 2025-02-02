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
        'repos': user.public_repos + (user.owned_private_repos if hasattr(user, 'owned_private_repos') else 0),
        'contributed': 0,
        'commits': 0,
        'stars': 0,
        'followers': user.get_followers().totalCount,
        'additions': 0,
        'deletions': 0
    }

    # Initialize repos for subsequent stats
    repos = user.get_repos()
    
    for repo in repos:
        # Count stars
        stats['stars'] += repo.stargazers_count 

        # Count commits, additions, and deletions
        try:
            commits = repo.get_commits()
            stats['commits'] += commits.totalCount

            # Fetch weekly commit stats properly
            weekly_stats = repo.get_stats_code_frequency()

            if weekly_stats:
                for week in weekly_stats:
                    stats['additions'] += week.additions
                    stats['deletions'] += abs(week.deletions)
        except Exception as e:
            print(f"Error processing repo {repo.name}: {str(e)}")

    # Count repositories the user has contributed to
    contributed_repos = set()
    for event in user.get_events():
        if event.type == "PushEvent":
            contributed_repos.add(event.repo.name)

    stats['contributed'] = len(contributed_repos)

    return stats


def update_svg_file(stats, input_file, output_file):
    """Update the SVG file with new statistics."""
    print(f"\nStarting SVG update process for {input_file}")
    print(f"Stats to be updated: {stats}")

    try:
        # Register the SVG namespace
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        print("Registered SVG namespace")
        
        # Parse the SVG file
        tree = ET.parse(input_file)
        root = tree.getroot()
        print("Successfully parsed SVG file")
        
        # Define namespaces
        namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        updates_made = 0
    
        # Dictionary to track if we've found each stat section
        found_stats = {
            'repos': False,
            'commits': False,
            'stars': False,
            'followers': False,
            'lines': False
        }

        # Find all text elements
        for text in root.findall(".//svg:text", namespaces):
            tspans = text.findall(".//svg:tspan", namespaces)
            current_section = None

            for i, tspan in enumerate(tspans):
                if tspan.text is None:
                    continue

                # Print for debugging
                print(f"Processing tspan: '{tspan.text}'")

                # Update Repos and Contributed
                if tspan.text == "Repos" and not found_stats['repos']:
                    # Next tspan should be the repos count
                    next_tspan = tspans[i + 1]
                    next_tspan.text = str(stats['repos'])
                    updates_made += 1
                    print(f"Updated repos to: {stats['repos']}")

                    # Find and update contributed count
                    for j in range(i + 2, i + 5):
                        if tspans[j].text == "Contributed":
                            tspans[j + 1].text = str(stats['contributed'])
                            updates_made += 1
                            print(f"Updated contributed to: {stats['contributed']}")
                            break
                    found_stats['repos'] = True

                # Update Commits
                elif tspan.text == "Commits" and not found_stats['commits']:
                    next_tspan = tspans[i + 1]
                    next_tspan.text = f"{stats['commits']:,}"
                    updates_made += 1
                    print(f"Updated commits to: {stats['commits']:,}")
                    found_stats['commits'] = True

                # Update Stars
                elif tspan.text == "Stars" and not found_stats['stars']:
                    next_tspan = tspans[i + 1]
                    next_tspan.text = str(stats['stars'])
                    updates_made += 1
                    print(f"Updated stars to: {stats['stars']}")
                    found_stats['stars'] = True

                # Update Followers
                elif tspan.text == "Followers" and not found_stats['followers']:
                    next_tspan = tspans[i + 1]
                    next_tspan.text = str(stats['followers'])
                    updates_made += 1
                    print(f"Updated followers to: {stats['followers']}")
                    found_stats['followers'] = True

                # Update Lines of Code and additions/deletions
                elif tspan.text == "Lines of Code" and not found_stats['lines']:
                    total_lines = stats['additions'] + stats['deletions']
                    # Update total lines
                    next_tspan = tspans[i + 1]
                    next_tspan.text = f"{total_lines:,}"
                    updates_made += 1
                    print(f"Updated total lines to: {total_lines:,}")

                    # Update additions
                    additions_tspan = tspans[i + 2]
                    additions_tspan.text = f"{stats['additions']:,}++"
                    updates_made += 1
                    print(f"Updated additions to: {stats['additions']:,}++")

                    # Update deletions
                    deletions_tspan = tspans[i + 3]
                    deletions_tspan.text = f"{stats['deletions']:,}--"
                    updates_made += 1
                    print(f"Updated deletions to: {stats['deletions']:,}--")
                    found_stats['lines'] = True

        print(f"\nTotal updates made: {updates_made}")
        print("Stats found:", found_stats)

        if updates_made == 0:
            print("WARNING: No updates were made to the SVG!")

        # Save the updated SVG
        print(f"\nAttempting to save updates to {output_file}")
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print("Successfully saved updated SVG file")

    except Exception as e:
        print(f"ERROR: An exception occurred: {str(e)}")
        raise


if __name__ == "__main__":
    # Get GitHub token from environment variable
    github_token = os.getenv('GH_TOKEN')
    if not github_token:
        raise ValueError("GitHub token not found in environment variables")

    # Get statistics
    stats = get_github_stats(github_token)
    print("Retrieved stats:", stats)  # Add this line

    # Check if files exist and are writable
    for mode in ['dark_mode.svg', 'light_mode.svg']:
        path = os.path.join('modes', mode)
        print(f"Checking {path}:")
        print(f"  File exists: {os.path.exists(path)}")
        print(f"  File is writable: {os.access(path, os.W_OK) if os.path.exists(path) else 'N/A'}")

    # Update both SVG files
    update_svg_file(stats, 'modes/dark_mode.svg', 'modes/dark_mode.svg')
    update_svg_file(stats, 'modes/light_mode.svg', 'modes/light_mode.svg')
