#!/usr/bin/env python3
"""
Example usage of docker-api.py with configurable parameters
Shows how to analyze different protest events with varying parameters
"""

import subprocess
import sys

def run_command(description, command):
    """Run a command and display its description"""
    print(f"\n{'='*60}")
    print(f"EXAMPLE: {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    # Just show the command, don't actually run it unless --execute is provided
    if "--execute" in sys.argv:
        subprocess.run(command)
    else:
        print("(Add --execute flag to actually run these commands)")

def main():
    print("YouTube Sockpuppet Analysis - Example Configurations")
    print("This script shows different ways to configure the analysis")
    
    # Example 1: Default gilet jaune analysis
    run_command(
        "Default Gilet Jaune Analysis (5 channels, 5 videos each)",
        [
            "python", "docker-api.py", "--run", 
            "--mode", "channels",
            "--training-channels", "data/chaines_clean.csv",
            "--search-query", "gilet jaune",
            "--num-channels-per-ideology", "5",
            "--num-videos-per-channel", "5",
            "--max-search-results", "10",
            "--max-recommendations", "10"
        ]
    )
    
    # Example 2: Black Lives Matter analysis with fewer channels
    run_command(
        "Black Lives Matter Analysis (3 channels, 4 videos each)",
        [
            "python", "docker-api.py", "--run",
            "--mode", "channels", 
            "--training-channels", "data/chaines_clean.csv",
            "--search-query", "Black Lives Matter",
            "--num-channels-per-ideology", "3",
            "--num-videos-per-channel", "4",
            "--max-search-results", "15",
            "--max-recommendations", "8"
        ]
    )
    
    # Example 3: Farmer protests analysis with more intensive training
    run_command(
        "Farmer Protests Analysis (8 channels, 3 videos each)",
        [
            "python", "docker-api.py", "--run",
            "--mode", "channels",
            "--training-channels", "data/chaines_clean.csv", 
            "--search-query", "manifestation agriculteurs",
            "--num-channels-per-ideology", "8",
            "--num-videos-per-channel", "3",
            "--max-search-results", "12",
            "--max-recommendations", "15"
        ]
    )
    
    # Example 4: Climate protests analysis
    run_command(
        "Climate Protests Analysis (6 channels, 2 videos each, more results)",
        [
            "python", "docker-api.py", "--run",
            "--mode", "channels",
            "--training-channels", "data/chaines_clean.csv",
            "--search-query", "climat manifestation",
            "--num-channels-per-ideology", "6", 
            "--num-videos-per-channel", "2",
            "--max-search-results", "20",
            "--max-recommendations", "12"
        ]
    )
    
    # Example 5: Simulation mode (test configuration without running containers)
    run_command(
        "Simulation Mode - Test Configuration Without Running Containers",
        [
            "python", "docker-api.py", "--simulate",
            "--mode", "channels",
            "--training-channels", "data/chaines_clean.csv",
            "--search-query", "manifestation étudiante",
            "--num-channels-per-ideology", "4",
            "--num-videos-per-channel", "6"
        ]
    )
    
    print(f"\n{'='*60}")
    print("KEY PARAMETERS EXPLAINED:")
    print("='*60}")
    print("--search-query: The protest event to search for")
    print("--num-channels-per-ideology: How many channels to randomly select per ideology") 
    print("--num-videos-per-channel: How many popular videos to watch per channel")
    print("--max-search-results: How many search results to collect")
    print("--max-recommendations: How many recommendations to collect after watching")
    print("--simulate: Test configuration without actually running containers")
    print(f"{'='*60}")
    
    if "--execute" not in sys.argv:
        print("\nTo actually run any of these commands, add --execute flag")
        print("Example: python examples.py --execute")

if __name__ == '__main__':
    main()
