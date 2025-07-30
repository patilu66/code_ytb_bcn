#!/usr/bin/env python3
"""
Test script pour vérifier la fonction de recherche
"""

from eytdriver_autonomous import EYTDriver
import time

def test_search():
    """Test de la fonction de recherche 'gilet jaune'"""
    print("Initialisation du driver...")
    
    # Initialize driver in headless mode for testing
    driver = EYTDriver(browser='chrome', headless=True, verbose=True)
    
    try:
        print("Test de recherche: 'gilet jaune'")
        
        # Test search function
        search_results = driver.search_videos('gilet jaune', scroll_times=1)
        
        print(f"Résultats trouvés: {len(search_results)}")
        
        if search_results:
            print("Premier résultat:")
            first_video = search_results[0]
            print(f"  URL: {first_video.url}")
            print(f"  Video ID: {first_video.videoId}")
        
        # Test watching a video briefly
        if search_results:
            print("Test de lecture du premier résultat...")
            driver.play(search_results[0], 5)
            
            print("Test des recommandations...")
            recommendations = driver.get_upnext_recommendations()
            print(f"Recommandations trouvées: {len(recommendations)}")
        
        print("Test réussi!")
        
    except Exception as e:
        print(f"Erreur pendant le test: {e}")
        return False
    finally:
        print("Fermeture du driver...")
        driver.close()
    
    return True

if __name__ == '__main__':
    test_search()
