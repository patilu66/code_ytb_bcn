from eytdriver_autonomous import EYTDriver, Video, VideoUnavailableException
import sys
import json
from datetime import datetime
import os
from random import choice
import csv

puppet = None

def parse_args():
    with open(sys.argv[1]) as f:
        return json.load(f)

def init_puppet(puppetId, profile_dir):
    global puppet
    # Disable virtual display on Windows
    use_virtual_display = os.name != 'nt'  # False on Windows, True on Linux
    
    # Force headless mode in Docker environment
    headless_mode = os.path.exists('/.dockerenv') or os.name != 'nt'
    
    puppet = dict(
        # driver=EYTDriver(verbose=True, profile_dir=profile_dir),#, use_virtual_display=True),
        driver=EYTDriver(browser='chrome', verbose=True, use_virtual_display=use_virtual_display, headless=headless_mode),
        puppetId=puppetId,
        actions=[],
        start_time=datetime.now()
    )
    return puppet

def makedir(outputDir, d):
    dir = os.path.join(outputDir, d)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def make_url(videoId):
    return 'https://youtube.com/watch?v=%s' % videoId

def add_action(action, params=None):
    print(action, params)
    puppet['actions'].append(dict(action=action, params=params))

def get_homepage():
    homepage = puppet['driver'].get_homepage_recommendations()
    add_action('get_homepage', [vid.videoId for vid in homepage])
    return homepage

def get_recommendations():
    recommendations = puppet['driver'].get_upnext_recommendations()
    add_action('get_recommendations', [vid.videoId for vid in recommendations])
    return recommendations

def watch(video: Video, duration):
    driver = puppet['driver']
    driver.play(video, duration=duration)
    add_action('watch', video.videoId)

def load_channels_from_csv(csv_file, ideology_filter=None):
    """Load channels from CSV file and return list of channel handles, optionally filtered by ideology."""
    channels = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                if 'id_ytb' in row and row['id_ytb']:
                    # Check ideology filter if provided
                    row_ideology = row.get('idee_pol', '').strip().lower()
                    if ideology_filter:
                        target_ideology = ideology_filter.lower()
                        # Map ideology labels to CSV values
                        ideology_mapping = {
                            'left': 'gauche',
                            'right': 'droite', 
                            'extremeright': 'droite extrême',
                            'radicalleft': 'gauche radicale'
                        }
                        expected_ideology = ideology_mapping.get(target_ideology, target_ideology)
                        if row_ideology != expected_ideology:
                            continue  # Skip this channel
                    
                    # Convert channel handle format (remove spaces, add @)
                    handle = row['id_ytb'].strip()
                    if not handle.startswith('@'):
                        handle = '@' + handle
                    channels.append({
                        'handle': handle,
                        'name': row.get('id', 'Unknown'),
                        'type': row.get('Type', 'Unknown'),
                        'theme': row.get('thématique', 'Unknown'),
                        'ideology': row.get('idee_pol', 'Unknown')
                    })
    except Exception as e:
        print(f"Error loading channels from CSV: {e}")
    return channels

def train_from_channels(channels_file, max_channels=None, videos_per_channel=3, ideology_filter=None):
    """Train puppet by watching popular videos from channels."""
    add_action("channel_training_start")
    
    # Load channels with ideology filter
    channels = load_channels_from_csv(channels_file, ideology_filter)
    if max_channels:
        channels = channels[:max_channels]
    
    print(f"Training from {len(channels)} channels for ideology: {ideology_filter or 'all'}...")
    if channels:
        channel_list = [f"{ch['name']} ({ch['ideology']})" for ch in channels]
        print(f"Selected channels: {channel_list}")
    
    # Get number of videos to actually watch
    trainingN = int(args.get('trainingN', len(channels) * videos_per_channel))
    watched = 0
    
    for channel in channels:
        if watched >= trainingN:
            break
            
        try:
            print(f"Training from channel: {channel['name']} ({channel['handle']})")
            driver = puppet['driver']
            
            # Navigate to channel
            driver.go_to_channel_from_handle(channel['handle'])
            
            # Get popular videos from channel
            popular_videos = driver.watch_top_video()
            
            if not popular_videos:
                print(f"No popular videos found for channel {channel['name']}")
                continue
            
            # Watch up to videos_per_channel videos from this channel
            channel_watched = 0
            for video in popular_videos[:videos_per_channel]:
                if watched >= trainingN or channel_watched >= videos_per_channel:
                    break
                    
                try:
                    print(f"  Watching video {video.videoId}")
                    watch(video, args['duration'])
                    watched += 1
                    channel_watched += 1
                except VideoUnavailableException:
                    print(f"  Video {video.videoId} unavailable, skipping...")
                    continue
                except Exception as e:
                    print(f"  Error watching video {video.videoId}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error processing channel {channel['name']}: {e}")
            continue
    
    add_action("channel_training_end", {"channels_processed": len(channels), "videos_watched": watched})
    print(f"Channel training completed: {watched} videos watched from {len(channels)} channels")

def save_puppet():
    js = dict(
            puppet_id=puppet['puppetId'],
            start_time=puppet['start_time'],
            end_time=datetime.now(),
            duration=puppet['duration'],
            description=puppet['description'],
            actions=puppet['actions'],
            args=args
        )
    with open(os.path.join(makedir(args['outputDir'], 'puppets'), puppet['puppetId']), 'w') as f:
        json.dump(js, f, default=str, indent=4)

def train():
    get_homepage()
    add_action("training_start")

    # get list of videoIds
    training_videos = args['training']

    # remove empty strings
    training_videos = [videoId for videoId in training_videos if len(videoId) > 0]
    
    # get number of videos to actually watch
    trainingN = int(args['trainingN'])

    # number of videos watched
    watched = 0
    
    for videoId in training_videos:
        # watch until N videos have been watched
        if watched >= trainingN:
            break
        # watch next video if available
        try:
            video = Video(None, make_url(videoId))
            watch(video, args['duration'])
            watched += 1
        except VideoUnavailableException:
            continue
        except Exception as e:
            print(e)
    add_action("training_end")

def test():
    get_homepage()
    add_action("testing_start")
    video = Video(None, make_url(args['testSeed']))
    for _ in range(20):
        watch(video, 0)
        r = get_recommendations()
        video = r[0]
    add_action("testing_end")

def search():
    """Search for a query and collect recommendations from search results."""
    add_action("search_start")
    
    search_query = args.get('searchQuery', 'gilet jaune')
    max_search_results = args.get('maxSearchResults', 10)
    max_recommendations = args.get('maxRecommendations', 10)
    
    print(f"Searching for: '{search_query}'")
    
    # Perform search
    driver = puppet['driver']
    search_results = driver.search_videos(search_query, scroll_times=2)
    
    if search_results:
        print(f"Found {len(search_results)} search results")
        # Use configurable max_search_results instead of hardcoded 10
        limited_results = search_results[:max_search_results]
        add_action("search_results", [vid.videoId for vid in limited_results])
        
        # Watch first search result to trigger recommendations
        first_video = search_results[0]
        print(f"Watching first search result: {first_video.videoId}")
        watch(first_video, 10)  # Short watch to trigger recommendations
        
        # Collect recommendations
        recommendations = get_recommendations()
        if recommendations:
            recommendation_ids = [vid.videoId for vid in recommendations[:max_recommendations]]
            add_action("search_recommendations", recommendation_ids)
            print(f"Collected {len(recommendation_ids)} recommendations after search")
        else:
            print("No recommendations found after search")
    else:
        print(f"No search results found for '{search_query}'")
    
    add_action("search_end")

def intervention():
    get_homepage()
    add_action("intervention_start")
    for videoId in args['intervention']:
        video = Video(None, make_url(videoId))
        watch(video, args['duration'])
        get_homepage()
    add_action("intervention_end")


if __name__ == '__main__':
    args = parse_args()

    try:
        # conduct end-to-end experiment
        profile_dir = os.path.join(makedir(args['outputDir'], 'profiles'), args['puppetId'])
        init_puppet(args['puppetId'], profile_dir)

        for action in args['steps'].split(','):
            if action == 'train':
                train()
            elif action == 'train_channels':
                # Train from channels CSV file
                channels_file = args.get('channelsFile', 'data/chaines_clean.csv')
                max_channels = args.get('maxChannels', None)
                videos_per_channel = args.get('videosPerChannel', 3)
                ideology_filter = args.get('ideologyFilter', None)
                train_from_channels(channels_file, max_channels, videos_per_channel, ideology_filter)
            elif action == 'test':
                test()
            elif action == 'search':
                search()
            elif action == 'intervention':
                intervention()
    
        # finalize puppet
        puppet['driver'].close()
        puppet['steps'] = args['steps']
        puppet['duration'] = args['duration']
        puppet['description'] = args['description']
        save_puppet()
    except Exception as e:
        exception = dict(time=datetime.now(), exception=str(e), module='sock-puppet')
        print(exception)
        with open(os.path.join(makedir(args['outputDir'], 'exceptions'), args['puppetId']), 'w') as f:
            json.dump(exception, f, default=str)