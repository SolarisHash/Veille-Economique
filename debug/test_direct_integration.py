#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test direct pour comprendre exactement où les données se perdent
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, "scripts")

def test_pipeline_complet():
    """Test du pipeline complet étape par étape"""
    print("🔬 TEST PIPELINE COMPLET ÉTAPE PAR ÉTAPE")
    print("=" * 70)
    
    try:
        # 1. IMPORT DES MODULES
        print("\n1️⃣ IMPORT DES MODULES")
        print("-" * 40)
        
        from recherche_web import RechercheWeb
        from analyseur_thematiques import AnalyseurThematiques
        
        print("✅ Modules importés avec succès")
        
        # 2. INITIALISATION
        print("\n2️⃣ INITIALISATION")
        print("-" * 40)
        
        recherche = RechercheWeb(timedelta(days=180))
        thematiques = ['recrutements', 'evenements', 'innovations', 'vie_entreprise']
        analyseur = AnalyseurThematiques(thematiques)
        
        print(f"✅ Recherche initialisée")
        print(f"✅ Analyseur initialisé (seuil: {analyseur.seuil_pertinence})")
        
        # 3. ENTREPRISE DE TEST
        print("\n3️⃣ ENTREPRISE DE TEST")
        print("-" * 40)
        
        entreprise_test = {
            'nom': 'MADAME CLAUDINE ZABLITH',
            'commune': 'Bussy-Saint-Georges',
            'siret': '12345678901234',
            'secteur_naf': 'Services aux entreprises',
            'site_web': ''
        }
        
        print(f"🏢 Entreprise: {entreprise_test['nom']}")
        print(f"📍 Commune: {entreprise_test['commune']}")
        
        # 4. RECHERCHE WEB
        print("\n4️⃣ RECHERCHE WEB")
        print("-" * 40)
        
        print("🔍 Exécution recherche...")
        resultats_recherche = recherche.rechercher_entreprise(entreprise_test)
        
        print(f"📊 Résultats de recherche:")
        print(f"   🔑 Clés: {list(resultats_recherche.keys())}")
        
        donnees_thematiques = resultats_recherche.get('donnees_thematiques', {})
        print(f"   📋 Thématiques trouvées: {list(donnees_thematiques.keys())}")
        
        # Analyse détaillée de chaque thématique
        total_resultats_valides = 0
        for thematique, donnees in donnees_thematiques.items():
            if isinstance(donnees, dict):
                pertinence = donnees.get('pertinence', 0)
                nb_extraits = len(donnees.get('extraits_textuels', []))
                total_resultats_valides += nb_extraits
                print(f"   🎯 {thematique}: pertinence={pertinence:.2f}, extraits={nb_extraits}")
            else:
                print(f"   ⚠️ {thematique}: format inattendu ({type(donnees)})")
        
        print(f"   📈 Total résultats valides: {total_resultats_valides}")
        
        if total_resultats_valides == 0:
            print("❌ PROBLÈME: Aucun résultat valide dans la recherche!")
            return False
        
        # 5. PRÉPARATION POUR L'ANALYSEUR
        print("\n5️⃣ PRÉPARATION DONNÉES ANALYSEUR")
        print("-" * 40)
        
        # Format attendu par l'analyseur
        donnees_pour_analyseur = [
            {
                'entreprise': entreprise_test,
                'donnees_thematiques': donnees_thematiques,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        print(f"📦 Données formatées pour analyseur:")
        print(f"   📋 Structure: {list(donnees_pour_analyseur[0].keys())}")
        print(f"   🏢 Entreprise: {donnees_pour_analyseur[0]['entreprise']['nom']}")
        print(f"   📊 Thématiques: {list(donnees_pour_analyseur[0]['donnees_thematiques'].keys())}")
        
        # 6. ANALYSE THÉMATIQUE
        print("\n6️⃣ ANALYSE THÉMATIQUE")
        print("-" * 40)
        
        print("🔬 Exécution analyse...")
        resultats_analyses = analyseur.analyser_resultats(donnees_pour_analyseur)
        
        print(f"📊 Résultats d'analyse:")
        print(f"   📋 Nombre d'entreprises: {len(resultats_analyses)}")
        
        if len(resultats_analyses) > 0:
            entreprise_analysee = resultats_analyses[0]
            
            print(f"\n7️⃣ RÉSULTATS DÉTAILLÉS")
            print("-" * 40)
            
            nom = entreprise_analysee.get('nom', 'N/A')
            score_global = entreprise_analysee.get('score_global', 0)
            thematiques_principales = entreprise_analysee.get('thematiques_principales', [])
            
            print(f"🏢 Entreprise: {nom}")
            print(f"🏆 Score global: {score_global:.3f}")
            print(f"🎯 Thématiques principales: {thematiques_principales}")
            
            # Détail par thématique
            analyse_thematique = entreprise_analysee.get('analyse_thematique', {})
            print(f"\n📋 DÉTAIL PAR THÉMATIQUE:")
            
            for thematique, details in analyse_thematique.items():
                trouve = details.get('trouve', False)
                score = details.get('score_pertinence', 0)
                sources = details.get('sources', [])
                nb_details = len(details.get('details', []))
                
                status = "✅" if trouve else "❌"
                print(f"   {status} {thematique}: score={score:.3f}, sources={sources}, détails={nb_details}")
                
                # Si pas trouvé, debug pourquoi
                if not trouve and thematique in donnees_thematiques:
                    donnee_originale = donnees_thematiques[thematique]
                    pertinence_orig = donnee_originale.get('pertinence', 0)
                    print(f"      🔍 Debug: pertinence originale={pertinence_orig}, seuil={analyseur.seuil_pertinence}")
                    
                    if pertinence_orig > analyseur.seuil_pertinence:
                        print(f"      ⚠️ PROBLÈME: Score suffisant mais pas détecté!")
            
            # 8. VERDICT
            print(f"\n8️⃣ VERDICT")
            print("-" * 40)
            
            if score_global > 0.0:
                print("🎉 SUCCÈS: L'analyseur fonctionne!")
                print(f"   Score: {score_global:.3f}")
                print(f"   Thématiques: {len(thematiques_principales)}")
                return True
            else:
                print("❌ ÉCHEC: Score global = 0")
                print("   L'analyseur ne détecte rien malgré les données")
                
                # Debug approfondi
                print(f"\n🔍 DEBUG APPROFONDI:")
                for thematique in donnees_thematiques.keys():
                    donnee = donnees_thematiques[thematique]
                    pertinence = donnee.get('pertinence', 0)
                    print(f"   {thematique}: pertinence={pertinence} vs seuil={analyseur.seuil_pertinence}")
                    
                    if pertinence > analyseur.seuil_pertinence:
                        print(f"      ⚠️ Devrait être détecté mais ne l'est pas!")
                
                return False
        else:
            print("❌ ÉCHEC: Aucun résultat d'analyse retourné")
            return False
        
    except Exception as e:
        print(f"❌ ERREUR PIPELINE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analyseur_minimal():
    """Test minimal de l'analyseur avec données garanties"""
    print("\n🧪 TEST ANALYSEUR MINIMAL")
    print("=" * 70)
    
    try:
        from analyseur_thematiques import AnalyseurThematiques
        
        # Configuration minimale
        thematiques = ['recrutements']
        analyseur = AnalyseurThematiques(thematiques)
        
        # Réduction forcée du seuil pour ce test
        analyseur.seuil_pertinence = 0.05  # Très permissif
        
        print(f"🎯 Seuil de test: {analyseur.seuil_pertinence}")
        
        # Données test avec score élevé garanti
        donnees_test = [
            {
                'entreprise': {
                    'nom': 'TEST ENTREPRISE',
                    'commune': 'Test Ville'
                },
                'donnees_thematiques': {
                    'recrutements': {
                        'mots_cles_trouves': ['recrutement', 'emploi', 'CDI'],
                        'pertinence': 2.5,  # Score élevé
                        'extraits_textuels': [
                            {
                                'titre': 'TEST ENTREPRISE recrute',
                                'description': 'Offre emploi CDI disponible',
                                'url': 'https://test.com'
                            },
                            {
                                'titre': 'Recrutement TEST ENTREPRISE',
                                'description': 'Nous recherchons candidats',
                                'url': 'https://test2.com'
                            }
                        ],
                        'urls': ['https://test.com', 'https://test2.com'],
                        'type': 'recherche_test'
                    }
                }
            }
        ]
        
        print("📊 Test avec données garanties...")
        resultats = analyseur.analyser_resultats(donnees_test)
        
        if resultats and len(resultats) > 0:
            entreprise = resultats[0]
            score = entreprise.get('score_global', 0)
            
            print(f"🏆 Score obtenu: {score:.3f}")
            
            if score > 0.0:
                print("🎉 ANALYSEUR FONCTIONNE avec données forcées!")
                return True
            else:
                print("❌ ANALYSEUR NE FONCTIONNE PAS même avec données forcées!")
                
                # Debug très détaillé
                analyse = entreprise.get('analyse_thematique', {})
                if 'recrutements' in analyse:
                    details = analyse['recrutements']
                    print(f"🔍 Détails recrutements:")
                    print(f"   trouve: {details.get('trouve', False)}")
                    print(f"   score: {details.get('score_pertinence', 0)}")
                    print(f"   sources: {details.get('sources', [])}")
                
                return False
        else:
            print("❌ Aucun résultat retourné")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test minimal: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test complet d'intégration"""
    print("🚀 TEST DIRECT D'INTÉGRATION")
    print("=" * 80)
    
    # Test 1: Pipeline complet
    pipeline_ok = test_pipeline_complet()
    
    # Test 2: Analyseur minimal si pipeline échoue
    if not pipeline_ok:
        print("\n" + "="*80)
        analyseur_ok = test_analyseur_minimal()
        
        if analyseur_ok:
            print("\n💡 DIAGNOSTIC:")
            print("   ✅ L'analyseur fonctionne")
            print("   ❌ Le problème vient des données de recherche")
            print("   🔧 Solution: Adapter le format des données")
        else:
            print("\n💡 DIAGNOSTIC:")
            print("   ❌ L'analyseur lui-même ne fonctionne pas")
            print("   🔧 Solution: Corriger le code de l'analyseur")
    else:
        print("\n🎉 SYSTÈME FONCTIONNEL!")
        print("Le problème doit être ailleurs dans votre script principal")

if __name__ == "__main__":
    main()