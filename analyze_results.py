#!/usr/bin/env python3
"""
Analysis script for YouTube Sockpuppet results
"""

import json
import os
from collections import defaultdict
import pandas as pd

def load_puppet_results(output_dir="output/puppets"):
    """Load all puppet result files"""
    results = {}
    
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                ideology = filename.split(',')[0]
                results[ideology] = data
    
    return results

def extract_search_data(results):
    """Extract search results and recommendations by ideology"""
    search_data = {}
    
    for ideology, data in results.items():
        search_results = []
        recommendations = []
        
        for action in data.get('actions', []):
            if action['action'] == 'search_results':
                search_results = action['params']
            elif action['action'] == 'search_recommendations':
                recommendations = action['params']
        
        search_data[ideology] = {
            'search_results': search_results,
            'recommendations': recommendations
        }
    
    return search_data

def analyze_overlap(search_data):
    """Analyze overlap and differences between ideologies"""
    ideologies = list(search_data.keys())
    
    print("=== SEARCH RESULTS ANALYSIS ===\n")
    
    # Find common videos across all ideologies
    all_search_results = [search_data[ideology]['search_results'] for ideology in ideologies]
    
    if all_search_results:
        common_videos = set(all_search_results[0])
        for results in all_search_results[1:]:
            common_videos &= set(results)
        
        print(f"Videos common to ALL ideologies: {len(common_videos)}")
        print(f"Common videos: {list(common_videos)[:6]}...\n")
    
    # Analyze differences by ideology
    for ideology in ideologies:
        search_results = search_data[ideology]['search_results']
        recommendations = search_data[ideology]['recommendations']
        
        print(f"--- {ideology.upper()} ---")
        print(f"Search results: {len(search_results)} videos")
        print(f"First 3: {search_results[:3]}")
        print(f"Unique to this ideology: {set(search_results) - common_videos}")
        print(f"Recommendations: {recommendations}")
        print()

def analyze_recommendations_diversity(search_data):
    """Analyze diversity in recommendations"""
    print("=== RECOMMENDATION ANALYSIS ===\n")
    
    all_recommendations = []
    ideology_recommendations = {}
    
    for ideology, data in search_data.items():
        recs = data['recommendations']
        all_recommendations.extend(recs)
        ideology_recommendations[ideology] = set(recs)
    
    unique_recommendations = set(all_recommendations)
    print(f"Total unique recommendations across all ideologies: {len(unique_recommendations)}")
    
    # Find shared recommendations
    shared_recs = ideology_recommendations[list(ideology_recommendations.keys())[0]]
    for ideology, recs in ideology_recommendations.items():
        shared_recs &= recs
    
    print(f"Recommendations shared by ALL ideologies: {len(shared_recs)}")
    print(f"Shared recommendations: {list(shared_recs)}")
    
    # Find ideology-specific recommendations
    print("\n--- IDEOLOGY-SPECIFIC RECOMMENDATIONS ---")
    for ideology, recs in ideology_recommendations.items():
        unique_to_ideology = recs - shared_recs
        print(f"{ideology}: {len(unique_to_ideology)} unique recommendations")
        print(f"  {list(unique_to_ideology)}")

def generate_comparison_table(search_data):
    """Generate a comparison table of results"""
    print("\n=== COMPARISON TABLE ===")
    
    # Create DataFrame
    rows = []
    max_results = max(len(data['search_results']) for data in search_data.values())
    
    for i in range(max_results):
        row = {'Position': i+1}
        for ideology, data in search_data.items():
            if i < len(data['search_results']):
                row[ideology] = data['search_results'][i]
            else:
                row[ideology] = ''
        rows.append(row)
    
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

def main():
    """Main analysis function"""
    print("YouTube Sockpuppet Analysis")
    print("=" * 50)
    
    # Load results
    try:
        results = load_puppet_results()
        print(f"Loaded results for {len(results)} ideologies: {list(results.keys())}\n")
    except Exception as e:
        print(f"Error loading results: {e}")
        return
    
    # Extract search data
    search_data = extract_search_data(results)
    
    # Perform analysis
    analyze_overlap(search_data)
    analyze_recommendations_diversity(search_data)
    generate_comparison_table(search_data)
    
    print("\n=== SUMMARY ===")
    print("Analysis complete! This shows how YouTube's algorithm")
    print("creates different information bubbles for different political ideologies")
    print("when searching for the same protest event ('gilet jaune').")

if __name__ == '__main__':
    main()
