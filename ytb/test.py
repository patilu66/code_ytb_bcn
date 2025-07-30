from extend_ytb_driver import EYTDriver
from datetime import datetime
import os

driver = EYTDriver(browser='chrome', verbose=True)

# try:
#     driver.go_to_channel_from_handle("lemondefr")
#     print("Session active après aller sur la chaîne.")
    
#     top_videos = driver.watch_top_video()
#     video = top_videos[0] if top_videos else None
#     if video:
#         print(f"Regardé la vidéo : {video.title}")
#         driver.play(video, 30)  # Regarde la vidéo pendant 30 secondes
#     else:
#         print("Aucune vidéo trouvée sur la chaîne.")


   
    

# finally:
#      print("Fermeture du driver")
#      driver.close()


if __name__ == '__main__':
  # initialize the driver
  driver = EYTDriver(browser='chrome', verbose=True)

  #open the YouTube homepage avec l'url https://www.youtube.com
  driver.get("https://www.youtube.com")

  # search for a keyword
  videos = driver.search_videos('sports', scroll_times=0)
  if videos:
    print(f"Found {len(videos)} videos for 'sports'")
    driver.play(videos[0])
  
  # get upnext recommendations and navigate through them
  for i in range(3):
    recommendations = driver.get_upnext_recommendations(1)
    if recommendations:
      video = recommendations[0]
      print(f"Playing recommendation {i+1}")
      driver.play(video)
    else:
      print(f"No recommendations found at step {i+1}")
      break

  # get videos from the youtube homepage
  print("Getting homepage recommendations...")
  videos = driver.get_homepage_recommendations()

  # check if any videos found
  if len(videos) > 0:
    print(f"Found {len(videos)} homepage videos")
    # play the top video from the homepage for 30 seconds
    driver.play(videos[0], 30)
  else:
    print("No homepage videos found")
    
  # close driver
  driver.close()