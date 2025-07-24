#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug pour identifier le problème de l'analyseur thématique
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, "scripts")

def debug_donnees_intermediaires():
    """Debug des données entre recherche et analyse"""
    print("🔍 DEBUG DES DONNÉES INTERMÉDIAIRES")
    print("=" * 60)
    
    # Recherche des fichiers de logs récents
    logs_dir = Path("logs/diagnostic")
    if logs_dir.exists():
        # Fichier JSON le plus récent
        json_files = list(logs_dir.glob("logs_detailles_*.json"))
        if json_files:
            latest_log = max(json_files, key=lambda x: x.stat().st_mtime)
            print(f"📄 Fichier log trouvé: {latest_log}")
            
            try:
                with open(latest_log, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # Analyse des entreprises avec résultats
                logs_entreprises = log_data.get('logs_entreprises', [])
                entreprises_avec_donnees = [
                    e for e in logs_entreprises 
                    if e.get('nb_resultats_valides', 0) > 0
                ]
                
                print(f"🏢 Entreprises avec données: {len(entreprises_avec_donnees)}")
                
                for entreprise in entreprises_avec_donnees[:3]:
                    nom = entreprise.get('nom', 'Inconnu')
                    nb_valides = entreprise.get('nb_resultats_valides', 0)
                    print(f"\n📊 {nom}: {nb_valides} résultats valides")
                    print(f"   🔍 Recherche OK: {entreprise.get('recherche_web_ok', False)}")
                    print(f"   🎯 Analyse OK: {entreprise.get('analyse_thematique_ok', False)}")
                    
                    if entreprise.get('erreurs'):
                        print(f"   ❌ Erreurs: {entreprise['erreurs']}")
                
                return True
                
            except Exception as e:
                print(f"❌ Erreur lecture log: {e}")
    
    print("⚠️ Aucun log détaillé trouvé")
    return False

def test_analyseur_direct():
    """Test direct de l'analyseur avec données simulées"""
    print("\n🧪 TEST DIRECT DE L'ANALYSEUR")
    print("=" * 60)
    
    try:
        from analyseur_thematiques import AnalyseurThematiques
        
        # Configuration
        thematiques = ['recrutements', 'evenements', 'innovations', 'vie_entreprise']
        analyseur = AnalyseurThematiques(thematiques)
        
        print(f"📋 Analyseur initialisé avec {len(thematiques)} thématiques")
        print(f"🎯 Seuil pertinence: {analyseur.seuil_pertinence}")
        
        # Données test réalistes simulant vos vraies données
        resultats_test = [
            {
                'entreprise': {
                    'nom': 'MADAME CLAUDINE ZABLITH',
                    'commune': 'Bussy-Saint-Georges',
                    'siret': '12345678901234'
                },
                'donnees_thematiques': {
                    'recrutements': {
                        'mots_cles_trouves': ['recrutement', 'emploi'],
                        'pertinence': 0.6,
                        'extraits_textuels': [
                            {
                                'titre': 'CLAUDINE ZABLITH - Emploi disponible',
                                'description': 'Recherche personnel pour poste disponible',
                                'url': 'https://example.com/emploi'
                            }
                        ],
                        'type': 'recherche_bing'
                    },
                    'vie_entreprise': {
                        'mots_cles_trouves': ['développement'],
                        'pertinence': 0.4,
                        'extraits_textuels': [
                            {
                                'titre': 'Développement activité ZABLITH',
                                'description': 'Expansion des services proposés',
                                'url': 'https://example.com/dev'
                            }
                        ],
                        'type': 'recherche_bing'
                    }
                }
            }
        ]
        
        print(f"\n📊 Test avec données simulées réalistes...")
        
        # Test étape par étape
        print("1️⃣ Test méthode analyser_resultats...")
        try:
            resultats = analyseur.analyser_resultats(resultats_test)
            print(f"   ✅ Méthode exécutée: {len(resultats)} résultats")
            
            if resultats and len(resultats) > 0:
                entreprise = resultats[0]
                
                print(f"\n2️⃣ Analyse du résultat:")
                print(f"   📝 Nom: {entreprise.get('nom', 'N/A')}")
                print(f"   🏆 Score global: {entreprise.get('score_global', 0):.3f}")
                print(f"   🎯 Thématiques principales: {entreprise.get('thematiques_principales', [])}")
                
                # Détail de l'analyse thématique
                analyse_thematique = entreprise.get('analyse_thematique', {})
                print(f"\n3️⃣ Détail analyse thématique:")
                
                for thematique, details in analyse_thematique.items():
                    trouve = details.get('trouve', False)
                    score = details.get('score_pertinence', 0)
                    print(f"   {thematique}: {'✅' if trouve else '❌'} (score: {score:.3f})")
                
                # Verdict
                if entreprise.get('score_global', 0) > 0:
                    print(f"\n🎉 ANALYSEUR FONCTIONNE!")
                    print(f"   Le problème vient d'ailleurs...")
                    return True
                else:
                    print(f"\n⚠️ Score global = 0")
                    print(f"   L'analyseur ne détecte rien...")
                    return False
            else:
                print(f"   ❌ Aucun résultat retourné")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur dans analyser_resultats: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except ImportError as e:
        print(f"❌ Erreur import analyseur: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_structure_donnees():
    """Debug de la structure des données entre modules"""
    print("\n🔬 DEBUG STRUCTURE DES DONNÉES")
    print("=" * 60)
    
    try:
        from recherche_web import RechercheWeb
        from datetime import timedelta
        
        # Test de ce que produit vraiment la recherche
        recherche = RechercheWeb(timedelta(days=180))
        
        entreprise_test = {
            'nom': 'TEST ENTREPRISE',
            'commune': 'Paris',
            'secteur_naf': 'Commerce',
            'site_web': ''
        }
        
        print("🔍 Test recherche pour comprendre la structure...")
        resultats = recherche.rechercher_entreprise(entreprise_test)
        
        print(f"📊 Structure des résultats de recherche:")
        print(f"   🔑 Clés principales: {list(resultats.keys())}")
        
        donnees_thematiques = resultats.get('donnees_thematiques', {})
        print(f"   📋 Données thématiques: {list(donnees_thematiques.keys())}")
        
        # Affichage de la structure détaillée
        for thematique, donnees in donnees_thematiques.items():
            print(f"\n   🎯 {thematique}:")
            if isinstance(donnees, dict):
                print(f"      📝 Sous-clés: {list(donnees.keys())}")
                for key, value in donnees.items():
                    if isinstance(value, list):
                        print(f"         {key}: liste de {len(value)} éléments")
                    elif isinstance(value, dict):
                        print(f"         {key}: dict avec {len(value)} clés")
                    else:
                        print(f"         {key}: {type(value).__name__}")
            else:
                print(f"      ⚠️ Type inattendu: {type(donnees)}")
        
        return resultats
        
    except Exception as e:
        print(f"❌ Erreur debug structure: {e}")
        return None

def generer_rapport_force():
    """Force la génération d'un rapport même avec données minimales"""
    print("\n🚀 GÉNÉRATION FORCÉE D'UN RAPPORT")
    print("=" * 60)
    
    try:
        from generateur_rapports import GenerateurRapports
        
        # Données minimales pour test
        entreprises_test = [
            {
                'nom': 'TEST ENTREPRISE 1',
                'commune': 'Paris',
                'siret': '12345678901234',
                'secteur_naf': 'Commerce',
                'score_global': 0.5,
                'thematiques_principales': ['recrutements'],
                'analyse_thematique': {
                    'recrutements': {
                        'trouve': True,
                        'score_pertinence': 0.6,
                        'sources': ['web_general'],
                        'details': [{
                            'source': 'web_general',
                            'score': 0.6,
                            'informations': {
                                'extraits_textuels': [{
                                    'titre': 'Test recrutement',
                                    'description': 'Offre emploi test',
                                    'url': 'https://example.com'
                                }]
                            }
                        }]
                    }
                }
            }
        ]
        
        generateur = GenerateurRapports()
        
        print("📊 Génération rapport Excel de test...")
        try:
            rapport_excel = generateur.generer_rapport_excel(entreprises_test)
            print(f"✅ Rapport Excel: {rapport_excel}")
        except Exception as e:
            print(f"❌ Erreur Excel: {e}")
        
        print("🌐 Génération rapport HTML de test...")
        try:
            rapport_html = generateur.generer_rapport_html(entreprises_test)
            print(f"✅ Rapport HTML: {rapport_html}")
        except Exception as e:
            print(f"❌ Erreur HTML: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur génération forcée: {e}")
        return False

def main():
    """Debug complet du système"""
    print("🚀 DEBUG COMPLET DU SYSTÈME DE VEILLE")
    print("=" * 70)
    
    # 1. Debug des données intermédiaires
    print("\n" + "="*70)
    debug_donnees_intermediaires()
    
    # 2. Test direct de l'analyseur
    print("\n" + "="*70)
    analyseur_ok = test_analyseur_direct()
    
    # 3. Debug structure des données
    print("\n" + "="*70)
    structure_donnees = debug_structure_donnees()
    
    # 4. Génération forcée d'un rapport
    print("\n" + "="*70)
    rapport_force = generer_rapport_force()
    
    # 5. Diagnostic final
    print("\n" + "="*70)
    print("🎯 DIAGNOSTIC FINAL")
    print("="*70)
    
    if analyseur_ok and rapport_force:
        print("✅ SYSTÈME FONCTIONNEL - Le problème est dans les données")
        print("\n💡 SOLUTION:")
        print("1. Vos données collectées ne sont pas dans le bon format")
        print("2. L'analyseur ne les reconnaît pas")
        print("3. Il faut adapter la structure des données")
        
        if structure_donnees:
            print(f"\n📋 STRUCTURE RÉELLE DE VOS DONNÉES:")
            print("Utilisez cette information pour adapter l'analyseur")
    
    elif not analyseur_ok:
        print("❌ PROBLÈME DANS L'ANALYSEUR")
        print("\n💡 SOLUTION:")
        print("1. L'analyseur thématique a un bug")
        print("2. Vérifiez que toutes les méthodes sont bien ajoutées")
        print("3. Vérifiez la configuration des mots-clés")
    
    else:
        print("⚠️ PROBLÈME MIXTE")
        print("Contactez-moi avec les résultats de ce debug")

if __name__ == "__main__":
    main()