"""
EYTDriver - Extend youtube Driver, based on ytdriver package
modernized with 2025 selectors (works without ytdriver, by redefining everything we need (for example Video class) in the same file)
"""
from selenium.webdriver import Chrome, ChromeOptions, Firefox, FirefoxOptions
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from time import sleep
import subprocess
import re
import json
import os

# Import yt_dlp if available, otherwise define a simple fallback
try:
    from yt_dlp import YoutubeDL
except ImportError:
    YoutubeDL = None

# ========================================
# UTILITY CLASSES
# ========================================

class VideoUnavailableException(Exception):
    """Exception for private/deleted/copyright videos."""
    pass

class VideoMetadata:
    """Video metadata extracted via yt-dlp."""
    def __init__(self, video_json):
        self.id = video_json.get('id', '')
        self.title = video_json.get('title', '')
        self.webpage_url = video_json.get('webpage_url', '')
        self.duration = video_json.get('duration', 0)
        self.thumbnail = video_json.get('thumbnail', '')
        self.description = video_json.get('description', '')
        self.upload_date = video_json.get('upload_date', '')
        self.channel_id = video_json.get('channel_id', '')
        self.channel_url = video_json.get('channel_url', '')
        self.age_limit = video_json.get('age_limit', 0)
        self.channel_name = video_json.get('uploader', '')
        self.view_count = video_json.get('view_count', 0)
        self.like_count = video_json.get('like_count', 0)
        self.comment_count = video_json.get('comment_count', 0)
        self.average_rating = video_json.get('average_rating', 0)
        self.categories = video_json.get('categories', [])
        self.tags = video_json.get('tags', [])
        self.video_json = video_json

class Video:
    """Class to encapsulate a YouTube video."""
    
    YT_DLP = YoutubeDL(dict(quiet=True)) if YoutubeDL else None
    
    def __init__(self, elem, url):
        self.elem = elem
        self.url = url
        # Extract video ID from URL
        match = re.search(r'[?&]v=(.*?)(?:&|$)', url)
        self.videoId = match.group(1) if match else ''
        self.__metadata = None

    def get_metadata(self):
        """Retrieve metadata via yt-dlp."""
        if not self.__metadata and self.YT_DLP:
            try:
                self.__metadata = Video.YT_DLP.extract_info(self.url, download=False)
                return VideoMetadata(self.__metadata)
            except:
                pass
        return None

# ========================================
# MAIN CLASS
# ========================================

class EYTDriver:
    """
    EYTDriver - Autonomous version with modern 2025 selectors
    No more dependency on obsolete ytdriver package!
    """
    
    def __init__(self, browser='chrome', profile_dir=None, use_virtual_display=False, headless=False, verbose=False):
        """
        Autonomous driver initialization
        
        Args:
            browser: 'chrome' or 'firefox'
            profile_dir: Browser profile directory  
            use_virtual_display: Virtual display Linux
            headless: Headless mode
            verbose: Detailed logs
        """
        self.verbose = verbose
        
        # Virtual display if requested (Linux)
        if use_virtual_display:
            try:
                from pyvirtualdisplay import Display
                self.__log("Starting virtual display")
                display = Display(size=(1920,1080))
                display.start()
            except ImportError:
                self.__log("pyvirtualdisplay not available")
        
        # Driver initialization
        if browser == 'chrome':
            self.driver = self.__init_chrome(profile_dir, headless)
        elif browser == 'firefox':
            self.driver = self.__init_firefox(profile_dir, headless)
        else:
            raise Exception("Invalid browser", browser)
        
        self.driver.set_page_load_timeout(30)

    def __init_chrome(self, profile_dir, headless):
        """Chrome initialization with optimized options."""
        options = ChromeOptions()
        # Essential Docker options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # Generate unique remote debugging port per container
        import random
        debug_port = 9222 + random.randint(1, 100)
        options.add_argument(f'--remote-debugging-port={debug_port}')
        
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional stability options for Docker
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--lang=en-US')  # Force English locale
        
        # Additional isolation options for parallel containers (conservative approach)
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-sync')  # Safer than disabling all extensions
        
        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Force headless in Docker environment
        if os.path.exists('/.dockerenv') or headless:
            options.add_argument('--headless')
        
        if profile_dir:
            # Ensure unique profile directory per container to avoid conflicts
            import time
            unique_suffix = f"{int(time.time())}{random.randint(1000, 9999)}"
            unique_profile_dir = f"{profile_dir}_{unique_suffix}"
            options.add_argument(f'--user-data-dir={unique_profile_dir}')
            self.__log(f"Using unique profile directory: {unique_profile_dir}")
        
        driver = Chrome(options=options)
        
        # Hide Selenium indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def __init_firefox(self, profile_dir, headless):
        """Firefox initialization."""
        options = FirefoxOptions()
        options.add_argument('--window-size=1920,1080')
        
        if headless:
            options.add_argument('--headless')
        
        service = Service(log_path=os.devnull)
        return Firefox(options=options, service=service)

    def close(self):
        """Close the driver."""
        self.driver.close()

    def __log(self, message):
        """Conditional logging."""
        if self.verbose:
            print(message)

    # ========================================
    # ADDED METHODS (new)
    # ========================================

    def handle_consent(self):
        """Automatic handling of European GDPR popups."""
        try:
            wait = WebDriverWait(self.driver, 2)
            consent_button = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//span[contains(text(), 'Accept all') or contains(text(), 'Tout accepter') or contains(text(), 'Accepter')]]"
            )))
            consent_button.click()
            self.__log("GDPR consent accepted.")
            sleep(2)
        except TimeoutException:
            self.__log("No consent popup detected.")
        except Exception as e:
            self.__log(f"Error handling consent: {e}")

    def get(self, url):
        """Navigation with automatic GDPR handling."""
        self.driver.get(url)
        self.handle_consent()

    def go_to_channel_from_handle(self, handle):
        """Navigate to channel via @handle."""
        if not handle.startswith('@'):
            handle = '@' + handle
        url = f'https://www.youtube.com/{handle}'
        self.__log(f"Going to channel: {url}")
        self.get(url)
        sleep(2)

    def watch_top_video(self):
        """Retrieve popular videos from a channel."""
        self.driver.get(self.driver.current_url + "/videos")
        self.handle_consent()
        sleep(2)

        # Click on "Popular" with enhanced detection
        chips = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ytChipShapeChip')]")
        found = False
        
        # Log all available chips for debugging
        chip_texts = [chip.text.strip() for chip in chips if chip.text.strip()]
        self.__log(f"Available chips: {chip_texts}")
        
        # Try multiple variations of "Popular"
        popular_variations = [
            "populaires", "popular", "più popolari", "más populares", 
            "beliebt", "populair", "популярные", "人気", "热门"
        ]
        
        for chip in chips:
            chip_text = chip.text.strip().lower()
            if any(variation in chip_text for variation in popular_variations):
                self.__log(f"'Popular' button found: '{chip.text.strip()}', clicking.")
                self.driver.execute_script("arguments[0].click();", chip)
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "ytd-rich-item-renderer"))
                    )
                    sleep(2)  # Increased sleep for Docker
                    found = True
                    break
                except TimeoutException:
                    self.__log("Timeout waiting for videos to load after clicking Popular")
                    continue

        if not found:
            self.__log("No 'Popular' button found. Trying fallback: getting recent videos...")
            # Fallback: just get the videos from /videos page without clicking Popular
            sleep(3)
            return self.__get_channel_videos_fallback()

        # Retrieve popular videos with 2025 SELECTOR
        self.__log("Retrieving popular videos...")
        videos = []
        try:
            video_elements = self.driver.find_elements(By.TAG_NAME, 'ytd-rich-item-renderer')
            self.__log(f"Found {len(video_elements)} video elements")
            
            for video_elem in video_elements:
                try:
                    link = video_elem.find_element(By.CSS_SELECTOR, 'a#video-title-link')
                    href = link.get_attribute('href')
                    if href:
                        videos.append(Video(video_elem, href))
                except Exception as e:
                    continue
            
            self.__log(f"Retrieved {len(videos)} popular videos")
            return videos
            
        except Exception as e:
            self.__log(f"Error retrieving videos: {e}")
            return []

    def __get_channel_videos_fallback(self):
        """Fallback method to get channel videos without Popular button."""
        self.__log("Using fallback method to get channel videos...")
        try:
            # Try to get any videos from the current page
            video_elements = self.driver.find_elements(By.TAG_NAME, 'ytd-rich-item-renderer')
            if not video_elements:
                # Try alternative selectors
                video_elements = self.driver.find_elements(By.CSS_SELECTOR, '[id="dismissible"]')
            
            self.__log(f"Fallback: Found {len(video_elements)} video elements")
            
            videos = []
            for video_elem in video_elements[:10]:  # Limit to 10 videos
                try:
                    link = video_elem.find_element(By.CSS_SELECTOR, 'a[href*="/watch?v="]')
                    href = link.get_attribute('href')
                    if href:
                        videos.append(Video(video_elem, href))
                except Exception as e:
                    continue
            
            self.__log(f"Fallback: Retrieved {len(videos)} videos")
            return videos
            
        except Exception as e:
            self.__log(f"Fallback method failed: {e}")
            return []

    # ========================================
    # CORRECTED METHODS (2025 selectors)
    # ========================================

    def get_homepage_recommendations(self, scroll_times=0):
        """Retrieve homepage videos with 2025 SELECTORS."""
        self.__log("Getting homepage recommendations")
        
        try:
            self.__log('Clicking homepage icon')
            self.driver.find_element(By.ID, 'logo-icon').click()
        except:
            self.__log('Getting homepage via URL')
            self.get('https://www.youtube.com')

        sleep(2)

        # Scroll to load more content
        for _ in range(scroll_times):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            sleep(0.2)

        # 2025 SELECTOR: ytd-rich-item-renderer
        video_containers = self.driver.find_elements(By.TAG_NAME, 'ytd-rich-item-renderer')
        
        homepage = []
        for container in video_containers:
            try:
                link = container.find_element(By.TAG_NAME, 'a')
                href = link.get_attribute('href')
                if href and '/watch?v=' in href:
                    homepage.append(Video(link, href))
            except:
                continue

        self.__log(f"Found {len(homepage)} homepage videos")
        return homepage

    def get_upnext_recommendations(self, topn=5):
        """
        🎯 CORE OF THE FIX! Recommendations with CORRECT 2025 SELECTORS
        """
        self.__log("Getting up-next recommendations with MODERN 2025 selectors")
        
        sleep(2)

        try:
            # MODERN 2025 SELECTOR: yt-lockup-view-model
            elems = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ytd-watch-next-secondary-results-renderer yt-lockup-view-model'))
            )
            
            self.__log(f"Found {len(elems)} lockup elements")
            
            recommendations = []
            for elem in elems[:topn]:
                try:
                    link = elem.find_element(By.CSS_SELECTOR, 'a[href*="/watch?v="]')
                    href = link.get_attribute('href')
                    if href:
                        recommendations.append(Video(elem, href))
                except Exception as e:
                    continue
            
            self.__log(f"Found {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            self.__log(f"Failed to get recommendations: {e}")
            return []

    def search_videos(self, query, scroll_times=0):
        """Search with 2025 SELECTORS."""
        self.__log(f"Searching for videos: '{query}'")
        
        # Encode query for URL
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)
        search_url = f'https://www.youtube.com/results?search_query={encoded_query}'
        self.get(search_url)
        sleep(3)  # Give more time for search results to load

        # Scroll for more results
        for _ in range(scroll_times):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            sleep(0.5)  # Increase delay between scrolls

        # 2025 SELECTOR: ytd-video-renderer
        video_elements = self.driver.find_elements(By.TAG_NAME, 'ytd-video-renderer')
        
        results = []
        for video_elem in video_elements:
            try:
                link = video_elem.find_element(By.TAG_NAME, 'a')
                href = link.get_attribute('href')
                if href and '/watch?v=' in href:
                    results.append(Video(link, href))
            except:
                continue

        self.__log(f"Found {len(results)} search results")
        return results

    def play(self, video, duration=5):
        """Video playback with ENHANCED handling."""
        self.__log(f"Playing video for {duration} seconds")
        
        try:
            self.__click_video_enhanced(video)
            sleep(2)
            self.__check_video_availability_enhanced()
            self.__click_play_button_enhanced()
            self.__handle_ads_enhanced()
            self.__clear_prompts_enhanced()
            sleep(duration)
            
        except Exception as e:
            self.__log(f"Error during video playback: {e}")

    # ========================================
    # ENHANCED METHODS (robust)
    # ========================================

    def __click_video_enhanced(self, video):
        """Video click with multiple fallbacks."""
        if hasattr(video, 'elem') and hasattr(video, 'url'):
            try:
                self.__log("Clicking video element via Selenium...")
                video.elem.click()
                return
            except Exception as e:
                try:
                    self.__log("Trying JavaScript click...")
                    self.driver.execute_script('arguments[0].click()', video.elem)
                    return
                except Exception as e:
                    self.__log("Loading video URL directly...")
                    self.get(video.url)
        elif isinstance(video, str):
            self.get(video)
        else:
            raise ValueError(f'Unsupported video parameter type: {type(video)}')

    def __check_video_availability_enhanced(self):
        """Availability check with multiple selectors."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, '//h1[contains(@class, "ytd-watch-metadata")]')),
                    EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/h1')),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.title')),
                    EC.presence_of_element_located((By.TAG_NAME, 'video')),
                )
            )
        except Exception as e:
            self.__log(f"Video may be unavailable: {e}")

    def __click_play_button_enhanced(self):
        """Play click with multiple selectors."""
        try:
            play_selectors = [
                '.ytp-play-button',
                '.ytp-large-play-button', 
                'button[title*="Play"]',
                'button[aria-label*="Play"]',
            ]
            
            for selector in play_selectors:
                try:
                    play_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if play_btn.is_displayed():
                        title = play_btn.get_attribute('title') or ''
                        aria_label = play_btn.get_attribute('aria-label') or ''
                        
                        if 'play' in title.lower() or 'play' in aria_label.lower():
                            play_btn.click()
                            self.__log("Play button clicked")
                            return
                except:
                    continue
                    
        except Exception as e:
            self.__log(f"Could not find/click play button: {e}")

    def __handle_ads_enhanced(self):
        """Ad handling with multiple detection and timeout."""
        self.__log("Checking for ads...")
        sleep(1)
        
        max_attempts = 30  # Maximum 30 attempts (60 seconds)
        attempts = 0
        
        while attempts < max_attempts:
            try:
                attempts += 1
                
                # MULTIPLE DETECTION of ads
                ad_indicators = [
                    '.ytp-ad-preview-container',
                    '.ytp-ad-player-overlay',
                    '.video-ads',
                    '[class*="ad-showing"]'
                ]
                
                ad_detected = False
                for indicator in ad_indicators:
                    try:
                        ad_elem = self.driver.find_element(By.CSS_SELECTOR, indicator)
                        if ad_elem.is_displayed():
                            ad_detected = True
                            break
                    except:
                        continue
                
                if not ad_detected:
                    self.__log("No ads detected")
                    return
                
                self.__log(f"Ad detected (attempt {attempts}/{max_attempts}), looking for skip button...")
                
                # MULTIPLE SELECTORS for skip
                skip_selectors = [
                    '.ytp-ad-skip-button-container',
                    '.ytp-ad-skip-button',
                    'button[class*="skip"]',
                    '.ytp-skip-ad-button',
                    '.videoAdUiSkipButton',
                    '[id*="skip"]'
                ]
                
                for selector in skip_selectors:
                    try:
                        skip_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if skip_btn.is_displayed() and skip_btn.is_enabled():
                            skip_btn.click()
                            self.__log("Ad skipped!")
                            return
                    except:
                        continue
                
                # If after 10 attempts, give up and continue
                if attempts >= 10:
                    self.__log(f"Could not skip ad after {attempts} attempts, continuing anyway...")
                    return
                
                sleep(2)
                
            except Exception as e:
                self.__log(f"Error in ad handling: {e}")
                break

    def __clear_prompts_enhanced(self):
        """Close popups with multiple selectors."""
        try:
            popup_selectors = [
                'button[aria-label*="No thanks"]',
                'button[aria-label*="Not now"]', 
                'button:contains("Not now")',
                'button:contains("No thanks")',
                '.ytd-popup-container button',
                '[role="dialog"] button',
            ]
            
            for selector in popup_selectors:
                try:
                    popup_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if popup_btn.is_displayed():
                        popup_btn.click()
                        self.__log("Popup closed")
                        sleep(1)
                        return
                except:
                    continue
                    
        except Exception as e:
            self.__log(f"Error closing popups: {e}")


# ========================================
# USAGE EXAMPLE
