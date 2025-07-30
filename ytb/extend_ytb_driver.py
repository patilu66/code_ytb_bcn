from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import subprocess
import re
import json

# Import yt_dlp if available, otherwise define a simple fallback
try:
    from yt_dlp import YoutubeDL
except ImportError:
    YoutubeDL = None

from ytdriver import YTDriver as BaseYTDriver, Video as BaseVideo, VideoUnavailableException as BaseVideoUnavailableException
from selenium.webdriver import Chrome, ChromeOptions

class EYTDriver(BaseYTDriver):

    def handle_consent(self):
        try:
            wait = WebDriverWait(self.driver, 2)
            consent_button = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//span[contains(text(), 'Accept all') or contains(text(), 'Tout accepter') or contains(text(), 'Accepter')]]"
            )))
            consent_button.click()
            self._YTDriver__log("Consentement RGPD accepté.")
            sleep(2)  # laisse le temps à la page de se recharger après clic
        except TimeoutException:
            self._YTDriver__log("Pas de popup consentement détecté.")
        except Exception as e:
            self._YTDriver__log(f"Erreur lors de la gestion du consentement : {e}")



    def get(self, url):
        self.driver.get(url)
        self.handle_consent()



    def go_to_channel(self, channel_url):
        self.driver.get(channel_url)
        self.handle_consent()
        sleep(2)

    def go_to_channel_from_handle(self, handle):
        if not handle.startswith('@'):
            handle = '@' + handle
        url = f'https://www.youtube.com/{handle}'
        self._YTDriver__log(f"Going to channel: {url}")
        self.go_to_channel(url)




    def watch_top_video(self):
        """
        Aller sur la page vidéos d'une chaîne et récupérer les vidéos populaires
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.common.action_chains import ActionChains
        from time import sleep

        self.driver.get(self.driver.current_url + "/videos")
        self.handle_consent()
        sleep(2)

        # Cliquer sur "Populaires"
        chips = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ytChipShapeChip')]")
        found = False
        for chip in chips:
            if chip.text.strip().lower() == "populaires":
                self._YTDriver__log("Bouton 'Populaires' trouvé, on clique.")
                self.driver.execute_script("arguments[0].click();", chip)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "ytd-rich-item-renderer"))
                )
                sleep(1)
                found = True
                break

        if not found:
            self._YTDriver__log("Aucun bouton 'Populaires' trouvé.")
            return []

        # Récupérer les vidéos populaires
        self._YTDriver__log("Récupération des vidéos populaires...")
        videos = []
        try:
            # Attendre que les vidéos se chargent - utiliser ytd-rich-item-renderer
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "ytd-rich-item-renderer"))
            )
            
            # Récupérer les éléments vidéo - utiliser ytd-rich-item-renderer au lieu de ytd-grid-video-renderer
            video_elements = self.driver.find_elements(By.TAG_NAME, 'ytd-rich-item-renderer')
            self._YTDriver__log(f"Trouvé {len(video_elements)} éléments vidéo")
            
            for video_elem in video_elements:
                try:
                    link = video_elem.find_element(By.CSS_SELECTOR, 'a#video-title-link')
                    href = link.get_attribute('href')
                    if href:
                        videos.append(BaseVideo(video_elem, href))
                except Exception as e:
                    self._YTDriver__log(f"Erreur lors de la récupération d'une vidéo: {e}")
                    continue
            
            self._YTDriver__log(f"Récupéré {len(videos)} vidéos populaires")
            return videos
            
        except TimeoutException:
            self._YTDriver__log("Timeout en attendant les vidéos populaires")
            return []
        except Exception as e:
            self._YTDriver__log(f"Erreur lors de la récupération des vidéos: {e}")
            return []

    # Override des méthodes du package parent avec des sélecteurs mis à jour
    
    def get_homepage_recommendations(self, scroll_times=0):
        """
        Version simplifiée - style YTdriver_code.py
        Collect videos from the YouTube homepage.
        """
        self._YTDriver__log("Getting homepage recommendations")
        
        # Aller à la homepage
        try:
            self._YTDriver__log('Clicking homepage icon')
            self.driver.find_element(By.ID, 'logo-icon').click()
        except:
            self._YTDriver__log('Getting homepage via URL')
            self.get('https://www.youtube.com')

        sleep(2)

        # Scroll pour charger plus de contenu
        for _ in range(scroll_times):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            sleep(0.2)

        # Collecter les vidéos de la homepage (sélecteur le plus simple)
        video_containers = self.driver.find_elements(By.TAG_NAME, 'ytd-rich-item-renderer')
        
        homepage = []
        for container in video_containers:
            try:
                link = container.find_element(By.TAG_NAME, 'a')
                href = link.get_attribute('href')
                if href and '/watch?v=' in href:
                    homepage.append(BaseVideo(link, href))
            except:
                continue

        self._YTDriver__log(f"Found {len(homepage)} homepage videos")
        return homepage

    def get_upnext_recommendations(self, topn=5):
        """
        Override de get_upnext_recommendations avec sélecteurs 2025 CORRECTS
        Collect up-next recommendations for the currently playing video.
        """
        self._YTDriver__log("Getting up-next recommendations with CORRECT selectors")
        
        sleep(2)

        try:
            # Le vrai sélecteur moderne : yt-lockup-view-model dans watch-next
            elems = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ytd-watch-next-secondary-results-renderer yt-lockup-view-model'))
            )
            
            self._YTDriver__log(f"Found {len(elems)} lockup elements")
            
            recommendations = []
            for elem in elems[:topn]:
                try:
                    # Chercher le lien dans le yt-lockup-view-model
                    link = elem.find_element(By.CSS_SELECTOR, 'a[href*="/watch?v="]')
                    href = link.get_attribute('href')
                    if href:
                        recommendations.append(BaseVideo(elem, href))
                except Exception as e:
                    self._YTDriver__log(f"Error processing lockup element: {e}")
                    continue
            
            self._YTDriver__log(f"Found {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            self._YTDriver__log(f"Failed to get recommendations: {e}")
            return []

    def search_videos(self, query, scroll_times=0):
        """
        Version simplifiée - style YTdriver_code.py  
        Search for videos.
        """
        self._YTDriver__log(f"Searching for videos: '{query}'")
        
        # Aller à la page de recherche
        search_url = f'https://www.youtube.com/results?search_query={query}'
        self.get(search_url)
        sleep(2)

        # Scroll pour charger plus de résultats
        for _ in range(scroll_times):
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            sleep(0.2)

        # Collecter les vidéos avec le sélecteur le plus simple
        video_elements = self.driver.find_elements(By.TAG_NAME, 'ytd-video-renderer')
        
        results = []
        for video_elem in video_elements:
            try:
                # Premier lien trouvé
                link = video_elem.find_element(By.TAG_NAME, 'a')
                href = link.get_attribute('href')
                if href and '/watch?v=' in href:
                    results.append(BaseVideo(link, href))
            except:
                continue

        self._YTDriver__log(f"Found {len(results)} search results")
        return results

    def play(self, video, duration=5):
        """
        Override de play avec gestion améliorée
        Play a video for a set duration.
        """
        self._YTDriver__log(f"Playing video for {duration} seconds")
        
        try:
            # Cliquer sur la vidéo avec fallbacks améliorés
            self.__click_video_enhanced(video)
            sleep(2)
            
            # Vérifier la disponibilité de la vidéo
            self.__check_video_availability_enhanced()
            
            # Cliquer sur play si nécessaire
            self.__click_play_button_enhanced()
            
            # Gérer les publicités
            self.__handle_ads_enhanced()
            
            # Gérer les popups
            self.__clear_prompts_enhanced()
            
            # Attendre la durée spécifiée
            sleep(duration)
            
        except Exception as e:
            self._YTDriver__log(f"Error during video playback: {e}")

    def __click_video_enhanced(self, video):
        """Version améliorée de __click_video avec meilleurs fallbacks"""
        if hasattr(video, 'elem') and hasattr(video, 'url'):  # C'est un objet Video
            try:
                self._YTDriver__log("Clicking video element via Selenium...")
                video.elem.click()
                return
            except Exception as e:
                self._YTDriver__log(f"Selenium click failed: {e}")
                try:
                    self._YTDriver__log("Trying JavaScript click...")
                    self.driver.execute_script('arguments[0].click()', video.elem)
                    return
                except Exception as e:
                    self._YTDriver__log(f"JavaScript click failed: {e}")
                    self._YTDriver__log("Loading video URL directly...")
                    self.get(video.url)
        elif isinstance(video, str):
            self._YTDriver__log("Loading video URL directly...")
            self.get(video)
        else:
            raise ValueError(f'Unsupported video parameter type: {type(video)}')

    def __check_video_availability_enhanced(self):
        """Version améliorée de la vérification de disponibilité"""
        try:
            # Attendre que la page vidéo soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, '//h1[contains(@class, "ytd-watch-metadata")]')),
                    EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/h1')),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.title')),
                    EC.presence_of_element_located((By.TAG_NAME, 'video')),
                )
            )
        except Exception as e:
            self._YTDriver__log(f"Video may be unavailable: {e}")
            # Ne pas lever d'exception, continuer quand même

    def __click_play_button_enhanced(self):
        """Version améliorée du clic sur play"""
        try:
            # Sélecteurs multiples pour le bouton play
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
                        # Vérifier si c'est vraiment le bouton play
                        title = play_btn.get_attribute('title') or ''
                        aria_label = play_btn.get_attribute('aria-label') or ''
                        
                        if 'play' in title.lower() or 'play' in aria_label.lower():
                            play_btn.click()
                            self._YTDriver__log("Play button clicked")
                            return
                except:
                    continue
                    
        except Exception as e:
            self._YTDriver__log(f"Could not find/click play button: {e}")

    def __handle_ads_enhanced(self):
        """Version améliorée de la gestion des publicités"""
        self._YTDriver__log("Checking for ads...")
        
        max_ad_wait = 60  # Maximum 60 secondes d'attente pour les pubs
        sleep(1)
        
        while True:
            try:
                # Vérifier si une pub est en cours
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
                    self._YTDriver__log("No ads detected")
                    return
                
                self._YTDriver__log("Ad detected, looking for skip button...")
                
                # Chercher le bouton skip
                skip_selectors = [
                    '.ytp-ad-skip-button-container',
                    '.ytp-ad-skip-button',
                    'button[class*="skip"]',
                    'button:contains("Skip")',
                ]
                
                for selector in skip_selectors:
                    try:
                        skip_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if skip_btn.is_displayed() and skip_btn.is_enabled():
                            skip_btn.click()
                            self._YTDriver__log("Ad skipped!")
                            return
                    except:
                        continue
                
                sleep(2)
                
            except Exception as e:
                self._YTDriver__log(f"Error in ad handling: {e}")
                break

    def __clear_prompts_enhanced(self):
        """Version améliorée pour fermer les popups"""
        try:
            # Sélecteurs pour différents types de popups
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
                        self._YTDriver__log("Popup closed")
                        sleep(1)
                        return
                except:
                    continue
                    
        except Exception as e:
            self._YTDriver__log(f"Error closing popups: {e}")


#for information, here is code from the yt driver : from selenium.webdriver import Chrome, ChromeOptions, Firefox, FirefoxOptions
# from selenium.webdriver import Chrome, ChromeOptions, Firefox, FirefoxOptions
# from selenium.webdriver.firefox.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import WebDriverException
# from time import sleep
# from .helpers import Video, VideoUnavailableException, time2seconds
# from pyvirtualdisplay import Display
# import os

# class YTDriver:

#     def __init__(self, browser='chrome', profile_dir=None, use_virtual_display=False, headless=False, verbose=False):
#         """
#         Initializes the webdriver and virtual display

#         ### Arguments:
#         - `browser`: Specify `chrome` or `firefox` to launch the corresponding webdriver.
#         - `profile_dir`: Specify a directory to save the browser profile so it can be loaded later. Set to `None` to not save the profile.
#         - `use_virtual_display`: Set to `True` to launch a virtual display using `pyvirtualdisplay`.
#         - `headless`: Set to `True` to run the browser in headless mode.
#         - `verbose`: Set to `True` to enable logging messages.
#         """

#         self.verbose = verbose

#         if use_virtual_display:
#             self.__log("Starting virtual display")
#             display = Display(size=(1920,1080))
#             display.start()

#         if browser == 'chrome':
#             self.driver = self.__init_chrome(profile_dir, headless)
#         elif browser == 'firefox':
#             self.driver = self.__init_firefox(profile_dir, headless)
#         else:
#             raise Exception("Invalid browser", browser)

#         self.driver.set_page_load_timeout(30)

#     def close(self):
#         """
#         Close the underlying webdriver.
#         """
#         self.driver.close()

#     def get_homepage(self, scroll_times=0):
#         """
#         Collect videos from the YouTube homepage.

#         ### Arguments:
#         - `scroll_times`: Number of times to scroll the homepage.

#         ### Returns:
#         - List of videos of type `ytdriver.helpers.Video`.

#         """
#         # try to find the youtube icon
#         try:
#             self.__log('Clicking homepage icon')
#             self.driver.find_element(By.ID, 'logo-icon').click()
#         except:
#             self.__log('Getting homepage via URL')
#             self.driver.get('https://www.youtube.com')

#         # wait for page to load
#         sleep(2)

#         # scroll page to load more results
#         for _ in range(scroll_times):
#             self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
#             sleep(0.2)
            

#         # collect video-like tags from homepage
#         videos = self.driver.find_elements(By.XPATH, '//div[@id="contents"]/ytd-rich-item-renderer')

#         # identify actual videos from tags
#         homepage = []
#         for video in videos:
#             a = video.find_elements(By.TAG_NAME, 'a')[0]
#             href = a.get_attribute('href')
#             if href is not None and href.startswith('https://www.youtube.com/watch?'):
#                 homepage.append(Video(a, href))

#         return homepage

#     def get_recommendations(self, topn=5):

#         """
#         Collect up-next recommendations for the currently playing video.

#         ### Arguments:
#         - `topn`: Number of recommendations to return.

#         ### Returns:
#         - List of videos of type `ytdriver.helpers.Video`.
        
#         """
#         # wait for page to load
#         sleep(2)

#         # wait for recommendations
#         elems = WebDriverWait(self.driver, 30).until(
#             EC.presence_of_all_elements_located((By.TAG_NAME, 'ytd-compact-video-renderer'))
#         )

#         # recommended videos array
#         return [Video(elem, elem.find_elements(By.TAG_NAME, 'a')[0].get_attribute('href')) for elem in elems[:topn]]

#     def search_videos(self, query, scroll_times=0):
#         """
#         Search for videos.

#         ### Arguments:
#         - `query` (`str`): Search query.

#         ### Returns:
#         - List of videos of type `ytdriver.helpers.Video`.
        
#         """

#         # load video search results
#         self.driver.get('https://www.youtube.com/results?search_query=%s' % query)

#         # wait for page to load
#         sleep(2)

#         # scroll page to load more results
#         for _ in range(scroll_times):
#             self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
#             sleep(0.2)

#         # collect video-like tags from homepage
#         videos = self.driver.find_elements(By.XPATH, '//div[@id="contents"]/ytd-video-renderer')
        
#         # identify actual videos from tags
#         results = []
#         for video in videos:
#             a = video.find_elements(By.TAG_NAME, 'a')[0]
#             href = a.get_attribute('href')
#             if href is not None and href.startswith('https://www.youtube.com/watch?'):
#                 results.append(Video(a, href))
#         return results


#     def play(self, video, duration=5):
#         """
#         Play a video for a set duration. Returns when that duration passes.

#         ### Arguments:
#         - `video` (`str`|`ytdriver.helpers.Video`): Video object or URL to play.
#         - `duration` (`int`): How long to play the video.
        
#         """
#         try:
#             self.__click_video(video)
#             self.__check_video_availability()
#             self.__click_play_button()
#             self.__handle_ads()
#             self.__clear_prompts()
#             sleep(duration)
#         except WebDriverException as e:
#             self.__log(e)

#     def save_screenshot(self, filename):
#         """
#         Save a screenshot of the current browser window.

#         ### Arguments:
#         - `filename`: Filename to save image as.
#         """
#         return self.driver.save_screenshot(filename)

#     ## Helpers
#     def __log(self, message):
#         if self.verbose:
#             print(message)

#     def __click_video(self, video):
#         if type(video) == Video:
#             try:
#                 # try to click the element using selenium
#                 self.__log("Clicking element via Selenium...")
#                 video.elem.click()
#                 return
#             except Exception as e:
#                 try:
#                     # try to click the element using javascript
#                     self.__log("Failed. Clicking via Javascript...")
#                     self.driver.execute_script('arguments[0].click()', video.elem)
#                 except:
#                     # js click failed, just open the video url
#                     self.__log("Failed. Loading video URL...")
#                     self.driver.get(video.url)
#         elif type(video) == str:
#             self.driver.get(video)
#         else:
#             raise ValueError('Unsupported video parameter!')

#     def __check_video_availability(self):
#         try:
#             WebDriverWait(self.driver, 5).until(
#                 EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/h1'))
#             )
#         except WebDriverException:
#             raise VideoUnavailableException()

#     def __click_play_button(self):
#         try:
#             playBtn = self.driver.find_elements(By.CLASS_NAME, 'ytp-play-button')
#             if 'Play' in playBtn[0].get_attribute('title'):
#                 playBtn[0].click()
#         except:
#             pass

#     def __handle_ads(self):
#         # handle multiple ads
#         while True:
#             sleep(1)

#             # check if ad is being shown
#             preview = self.driver.find_elements(By.CLASS_NAME, 'ytp-ad-preview-container')
#             if len(preview) == 0:
#                 self.__log('Ad not detected')
#                 # ad is not shown, return
#                 return

#             self.__log('Ad detected')
            
#             sleep(1)
#             preview = preview[0]
#             # an ad is being shown
#             # grab preview text to determine ad type
#             text = preview.text.replace('\n', ' ')
#             wait = 0
#             if 'after ad' in text:
#                 # unskippable ad, grab ad length
#                 length = self.driver.find_elements(By.CLASS_NAME, 'ytp-ad-duration-remaining')[0].text
#                 wait = time2seconds(length)
#                 self.__log('Unskippable ad. Waiting %d seconds...' % wait)
#             elif 'begin in' in text or 'end in' in text:
#                 # short ad
#                 wait = int(text.split()[-1])
#                 self.__log('Short ad. Waiting for %d seconds...' % wait)
#             else:
#                 # skippable ad, grab time before skippable
#                 wait = int(text)
#                 self.__log('Skippable ad. Skipping after %d seconds...' % wait)

#             # wait for ad to finish
#             sleep(wait)

#             # click skip button if available
#             skip = self.driver.find_elements(By.CLASS_NAME, 'ytp-ad-skip-button-container')
#             if len(skip) > 0:
#                 skip[0].click()

#     def __clear_prompts(self):
#         try:
#             sleep(1)
#             self.driver.find_element(By.XPATH, '/html/body/ytd-app/ytd-popup-container/tp-yt-iron-dropdown/div/yt-tooltip-renderer/div[2]/div[1]/yt-button-renderer/a/tp-yt-paper-button/yt-formatted-string').click()
#         except:
#             pass
    
#     def __init_chrome(self, profile_dir, headless):
#         options = ChromeOptions()
#         options.add_argument('--no-sandbox')
#         options.add_argument('--window-size=1920,1080')

#         if profile_dir is not None:
#             options.add_argument('--user-data-dir=%s' % profile_dir)
#         if headless:
#             options.add_argument('--headless')

#         return Chrome(options=options)

#     def __init_firefox(self, profile_dir, headless):
#         options = FirefoxOptions()
#         options.add_argument('--window-size=1920,1080')
#         if profile_dir is not None:
#             pass
#         if headless:
#             options.add_argument('--headless')

#         service = Service(log_path=os.path.devnull)
#         return Firefox(options=options, service=service)