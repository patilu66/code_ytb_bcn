"""
Test spécifique pour la chaîne Le Monde
- Va sur la chaîne lemondefr
- Regarde les 2 vidéos les plus populaires
- Suit une recommandation
"""

from extend_ytb_driver import EYTDriver

def test_lemonde_channel():
    # Initialize driver
    driver = EYTDriver(browser='chrome', verbose=True, headless=False)
    
    try:
        print("=== TEST CHAÎNE LE MONDE ===")
        
        # Aller sur la chaîne Le Monde
        print("\n1. Navigation vers la chaîne lemondefr...")
        driver.go_to_channel_from_handle("lemondefr")
        print("✅ Arrivé sur la chaîne Le Monde")
        
        # Regarder les vidéos les plus populaires
        print("\n2. Récupération des vidéos populaires...")
        top_videos = driver.watch_top_video()
        
        if not top_videos:
            print("❌ Aucune vidéo trouvée sur la chaîne")
            return
            
        print(f"✅ Trouvé {len(top_videos)} vidéos sur la chaîne")
        
        # Regarder les 2 premières vidéos (ou moins si pas assez)
        videos_to_watch = min(2, len(top_videos))
        
        for i in range(videos_to_watch):
            print(f"\n3.{i+1}. Lecture de la vidéo {i+1}...")
            try:
                driver.play(top_videos[i], 5)  # Regarder 5 secondes
                print(f"✅ Vidéo {i+1} lue avec succès")
            except Exception as e:
                print(f"❌ Erreur lors de la lecture de la vidéo {i+1}: {e}")
        
        # Après avoir regardé les vidéos, chercher des recommandations
        print("\n4. Recherche de recommandations...")
        recommendations = driver.get_upnext_recommendations(3)
        
        if recommendations:
            print(f"✅ Trouvé {len(recommendations)} recommandations")
            
            # Regarder la première recommandation
            print("\n5. Lecture d'une recommandation...")
            try:
                driver.play(recommendations[0], 5)  # Regarder 5 secondes
                print("✅ Recommandation lue avec succès")
                
                # Vérifier s'il y a de nouvelles recommandations
                print("\n6. Vérification des nouvelles recommandations...")
                new_recommendations = driver.get_upnext_recommendations(2)
                if new_recommendations:
                    print(f"✅ Trouvé {len(new_recommendations)} nouvelles recommandations")
                else:
                    print("ℹ️ Pas de nouvelles recommandations trouvées")
                    
            except Exception as e:
                print(f"❌ Erreur lors de la lecture de la recommandation: {e}")
        else:
            print("❌ Aucune recommandation trouvée")
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        
    finally:
        print("\n=== FIN DU TEST ===")
        driver.close()

if __name__ == '__main__':
    test_lemonde_channel()
