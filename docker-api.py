from argparse import ArgumentParser
from random import choice
import docker
from time import sleep
import os
import pandas as pd
from uuid import uuid4
import json

# our own ID
IMAGE_NAME = 'fr-spain_ytb'
OUTPUT_DIR = os.path.join(os.getcwd(), 'output')
ARGS_DIR = os.path.join(os.getcwd(), 'arguments')
NUM_TRAINING_VIDEOS = 5
WATCH_DURATION = 30

# for Windows - os.getuid() doesn't exist on Windows
try:
    USERNAME = os.getuid()  # Unix/Linux
except AttributeError:
    USERNAME = 1000  # Default value for Windows

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--build', action="store_true", help='Build docker image')
    parser.add_argument('--run', action="store_true", help='Run all docker containers')
    parser.add_argument('--simulate', action="store_true", help='Only generate arguments but do not start containers')
    
    # Search configuration
    parser.add_argument('--search-query', default='gilet jaune', help='Search query to analyze')
    parser.add_argument('--channels-per-ideology', default=5, type=int, help='Number of channels per ideology')
    parser.add_argument('--videos-per-channel', default=5, type=int, help='Number of videos per channel')
    parser.add_argument('--max-results', default=10, type=int, help='Maximum search results to collect')
    
    args = parser.parse_args()
    return args, parser

def build_image():
    # Get docker client and build image
    client = docker.from_env()

    # Build the image from the Dockerfile
    #   -> tag specifies the name
    #   -> rm specifies that delete intermediate images after build is completed
    _, stdout = client.images.build(path='.', tag=IMAGE_NAME, rm=True)
    for line in stdout:
        if 'stream' in line:
            print(line['stream'], end='')
    
def get_mount_volumes():
    # Binds "/app/output" on the container -> "OUTPUT_DIR" actual folder on disk
    # Binds "/app/arguments" on the container -> "ARGS_DIR" actual folder on disk  
    # Binds "/app/data" on the container -> "data" actual folder on disk
    data_dir = os.path.join(os.getcwd(), 'data')
    return { 
        OUTPUT_DIR: { "bind": "/app/output" }, 
        ARGS_DIR: { "bind": "/app/arguments" },
        data_dir: { "bind": "/app/data" }
    }

def max_containers_reached(client, max_containers):
    try:
        return len(client.containers.list()) >= max_containers
    except:
        return True

def get_channels_by_ideology(csv_file='data/chaines_clean.csv'):
    """Get channels organized by political ideology"""
    channels_df = pd.read_csv(csv_file, sep=';')
    
    return {
        'Left': channels_df[channels_df['idee_pol'] == 'gauche']['channel_id'].tolist(),
        'RadicalLeft': channels_df[channels_df['idee_pol'] == 'gauche radicale']['channel_id'].tolist(),
        'Right': channels_df[channels_df['idee_pol'] == 'droite']['channel_id'].tolist(),
        'ExtremeRight': channels_df[channels_df['idee_pol'] == 'droite extrême']['channel_id'].tolist()
    }

def get_training_videos(csv):
    """Retrieve videos by ideology from CSV file"""
    try:
        videos_df = pd.read_csv(csv, sep=';')  # Support for CSV with ; separator
        
        # Support for multiple video file structures
        if 'video_id' in videos_df.columns:
            video_col = 'video_id'
        elif 'id' in videos_df.columns:
            video_col = 'id'
        elif 'youtube_id' in videos_df.columns:
            video_col = 'youtube_id'
        else:
            print("Warning: No video ID column found in video file")
            return {'Left': [], 'RadicalLeft': [], 'Right': [], 'ExtremeRight': []}
        
        # Support for multiple ideology columns
        if 'idee_pol' in videos_df.columns:
            ideology_col = 'idee_pol'
        elif 'ideology' in videos_df.columns:
            ideology_col = 'ideology'
        elif 'ideologie' in videos_df.columns:
            ideology_col = 'ideologie'
        else:
            print("Warning: No ideology column found in video file")
            return {'Left': [], 'RadicalLeft': [], 'Right': [], 'ExtremeRight': []}
        
        # Ideology mapping (compatible with your channels AND possible old formats)
        return {
            'Left': videos_df[videos_df[ideology_col].isin(['gauche', 'Left'])][video_col].tolist(),
            'RadicalLeft': videos_df[videos_df[ideology_col].isin(['gauche radicale', 'gauche radicale ', 'RadicalLeft'])][video_col].tolist(),
            'Right': videos_df[videos_df[ideology_col].isin(['droite', 'Right'])][video_col].tolist(),
            'ExtremeRight': videos_df[videos_df[ideology_col].isin(['droite extrême', 'droite extreme', 'ExtremeRight'])][video_col].tolist()
        }
    except Exception as e:
        print(f"Error reading video file: {e}")
        # If no video file, return empty lists
        return {
            'Left': [],
            'RadicalLeft': [],
            'Right': [],
            'ExtremeRight': []
        }

def spawn_containers(args):
    # Get docker client (only if not in simulation mode)
    if not args.simulate:
        client = docker.from_env()
    else:
        client = None
    
    # List of labels - YOUR 4 IDEOLOGIES
    LABELS = ['Left', 'RadicalLeft', 'Right', 'ExtremeRight']

    # Get training data based on mode
    if args.mode == 'channels':
        print(f"Mode: Channel training (CSV: {args.training_channels})")
        training_data = get_channels_by_ideology(args.training_channels)
        training_type = 'channels'
    else:
        print(f"Mode: Video training (CSV: {args.training_videos})")
        training_data = get_training_videos(args.training_videos)
        training_type = 'videos'

    # Get seeds for testing (not used in search mode)
    try:
        seeds = pd.read_csv(args.testing_videos)['video_id'].to_list()
    except:
        # If no test seeds, use example videos
        print("Warning: No test seeds found. Using default values.")
        seeds = ['9bZkp7q19f0', 'ZZ5LpwO-An4', 'K5le9sYdYkM']  # Examples from your arguments folder
    
    # Display global configuration summary
    print(f"\n{'='*60}")
    print(f"YOUTUBE SOCKPUPPET ANALYSIS CONFIGURATION")
    print(f"{'='*60}")
    print(f"Search Query: '{args.search_query}'")
    print(f"Training Mode: {args.mode}")
    print(f"Channels per Ideology: {args.num_channels_per_ideology}")
    print(f"Videos per Channel: {args.num_videos_per_channel}")
    print(f"Max Search Results: {args.max_search_results}")
    print(f"Max Recommendations: {args.max_recommendations}")
    print(f"Target Ideologies: {', '.join(LABELS)}")
    print(f"Total Sockpuppets: {len(LABELS)}")
    if args.mode == 'channels':
        print(f"Training Data: {args.training_channels}")
        # Count available channels per ideology
        total_available = sum(len(channels) for channels in training_data.values())
        print(f"Total Available Channels: {total_available}")
    else:
        print(f"Training Data: {args.training_videos}")
    print(f"{'='*60}\n")
    
    # Spawn containers for each user
    count = 0

    # Create required directories
    if not os.path.exists(ARGS_DIR):
        os.makedirs(ARGS_DIR)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Training ideology
    for training_label in LABELS:
        print(f"Creating sockpuppet for ideology: {training_label}")

        # Display configuration for this ideology
        print(f"  Configuration:")
        print(f"    - Search query: '{args.search_query}'")
        print(f"    - Channels per ideology: {args.num_channels_per_ideology}")
        print(f"    - Videos per channel: {args.num_videos_per_channel}")
        print(f"    - Max search results: {args.max_search_results}")
        print(f"    - Max recommendations: {args.max_recommendations}")

        # User data for training based on mode
        if args.mode == 'channels':
            # Channel mode: use channel_ids
            training_channels = training_data[training_label]
            if not training_channels:
                print(f"Warning: No channels found for {training_label}")
                continue
            
            # Select random channels using the configurable parameter
            num_channels_to_select = min(len(training_channels), args.num_channels_per_ideology)
            selected_channels = pd.Series(training_channels).sample(
                n=num_channels_to_select, 
                random_state=None  # Ensures truly random selection each time
            ).to_list()
            
            print(f"  Selected {len(selected_channels)} random channels from {len(training_channels)} available for {training_label}")
            
            training_content = {
                'type': 'channels',
                'channels': selected_channels,
                'videos_per_channel': args.num_videos_per_channel
            }
        else:
            # Video mode: use video_ids
            training_videos = training_data[training_label]
            if not training_videos:
                print(f"Warning: No videos found for {training_label}")
                continue
                
            # Select random videos (* 2 for additional backups)
            selected_videos = pd.Series(training_videos).sample(
                min(len(training_videos), NUM_TRAINING_VIDEOS * 2)
            ).to_list()
            
            training_content = {
                'type': 'videos',
                'videos': selected_videos[:NUM_TRAINING_VIDEOS],
                'backup_videos': selected_videos[NUM_TRAINING_VIDEOS:]
            }
        
        # Check for running container list
        if not args.simulate:
            while max_containers_reached(client, args.max_containers):
                # Sleep for a minute if maxContainers are active
                print("Max containers reached. Sleeping...")
                sleep(args.sleep_duration)


        # Try test seeds
        testSeed = choice(seeds)

        # Generate a unique puppet identifier
        puppetId = f'{training_label},{testSeed},{str(uuid4())[:8]}'

        # Write arguments to a file
        with open(os.path.join(ARGS_DIR, f'{puppetId}.json'), 'w') as f:
            if args.mode == 'channels':
                puppetArgs = dict(
                    puppetId=puppetId,
                    # Duration to watch each video
                    duration=WATCH_DURATION,
                    # A description with the search query
                    description=f'Sockpuppet {training_label} - analyzing "{args.search_query}"',
                    # Output directory for sock puppet
                    outputDir='/app/output',
                    # Steps to perform: train from channels then search
                    steps='train_channels,search',
                    # Channels file (use main CSV - sockpuppet.py will filter by ideology)
                    channelsFile='/app/data/chaines_clean.csv',
                    # Ideology filter for this sockpuppet
                    ideologyFilter=training_label,
                    # Number of channels to use (configurable)
                    maxChannels=args.num_channels_per_ideology,
                    # Videos per channel
                    videosPerChannel=args.num_videos_per_channel,
                    # Number of training videos (calculated)
                    trainingN=args.num_channels_per_ideology * args.num_videos_per_channel,
                    # Configurable search query
                    searchQuery=args.search_query,
                    # Configurable max search results
                    maxSearchResults=args.max_search_results,
                    # Configurable max recommendations
                    maxRecommendations=args.max_recommendations,
                    # Mode information
                    mode=args.mode
                )
            else:
                # Original mode for compatibility
                puppetArgs = dict(
                    puppetId=puppetId,
                    # Duration to watch each video
                    duration=WATCH_DURATION,
                    # A description
                    description=f'Sockpuppet {training_label} - Mode: {args.mode}',
                    # Output directory for sock puppet
                    outputDir='/app/output',
                    # Training content (channels or videos depending on mode)
                    training=training_content,
                    # Number of training items
                    trainingN=NUM_TRAINING_VIDEOS,
                    # Seed video
                    testSeed=testSeed,
                    # Steps to perform
                    steps='train,test',
                    # Mode information
                    mode=args.mode
                )
            json.dump(puppetArgs, f, indent=4)


        # Spawn container if it's not a simulation
        if not args.simulate:
            print("Spawning container...")

            # Set outputDir as "/app/output"
            command = ['python', 'sockpuppet.py', f'/app/arguments/{puppetId}.json']

            # Run the container - like manual command but in parallel
            container_name = f'sockpuppet_{training_label.lower()}_{str(uuid4())[:8]}'
            print(f"Launching container {container_name}...")
            
            client.containers.run(
                IMAGE_NAME, 
                command, 
                volumes=get_mount_volumes(), 
                shm_size='512M', 
                remove=True, 
                name=container_name,
                detach=True  # Parallel as desired
            )
            
            print(f"Container {training_label} launched in parallel.")
            
        # Increment count of containers
        count += 1

    print("Total containers spawned:", count)

def main():

    args, parser = parse_args()

    if args.build:
        print("Starting docker build...")
        build_image()
        print("Build complete!")

    if args.run or args.simulate:
        spawn_containers(args)

    if not args.build and not args.run and not args.simulate:
        parser.print_help()


if __name__ == '__main__':
    main()