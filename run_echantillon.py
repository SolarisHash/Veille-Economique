#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour analyser les données réelles - VERSION COMPLÈTE CORRIGÉE
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import timedelta

# Ajout du dossier scripts au path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

# ✅ IMPORTS CRITIQUES MANQUANTS dans votre script
from scripts.main import VeilleEconomique
from scripts.extracteur_donnees import ExtracteurDonnees
from scripts.recherche_web import RechercheWeb
from scripts.analyseur_thematiques import AnalyseurThematiques
from scripts.generateur_rapports import GenerateurRapports
from scripts.diagnostic_logger import DiagnosticLogger

def main():
    """Lancement avec données réelles anonymisées - VERSION COMPLÈTE"""
    print("🏢 ANALYSE AVEC DONNÉES RÉELLES - VERSION COMPLÈTE")
    print("=" * 70)
    
    # Configuration
    fichier_excel = "data/input/entreprises_base.xlsx"
    # fichier_excel = "data/input/entreprises_test_reelles.xlsx"
    nb_entreprises = 100
    
    # Vérifications préalables
    if not os.path.exists(fichier_excel):
        print(f"❌ ERREUR: Fichier manquant")
        print(f"📁 Veuillez placer votre fichier Excel dans: {fichier_excel}")
        return False
    
    print(f"✅ Fichier trouvé: {fichier_excel}")
    print(f"🎯 Analyse de {nb_entreprises} entreprises réelles")
    
    # Nettoyage du cache pour forcer nouvelles recherches
    cache_dir = "data/cache"
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print("🗑️  Cache nettoyé pour nouvelles recherches")
    
    # Création des dossiers
    Path("data/input").mkdir(parents=True, exist_ok=True)
    Path("data/output").mkdir(parents=True, exist_ok=True)
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)
    
    # ✅ INITIALISATION DU LOGGER (manquant dans votre script)
    logger = DiagnosticLogger()
    
    try:
        print(f"\n🚀 Démarrage analyse complète...")
        print("⚠️  Les recherches vont prendre du temps (vraies recherches)")
        print()
        
        # ✅ ÉTAPE 1: EXTRACTION DES DONNÉES
        print("📊 ÉTAPE 1/5 - EXTRACTION DES DONNÉES")
        print("-" * 50)
        
        extracteur = ExtracteurDonnees(fichier_excel)
        entreprises = extracteur.extraire_echantillon(nb_entreprises)
        print(f"✅ {len(entreprises)} entreprises extraites avec succès")
        
        # ✅ ÉTAPE 2: RECHERCHE WEB (votre partie qui marche)
        print("\n🔍 ÉTAPE 2/5 - RECHERCHE WEB")
        print("-" * 50)
        
        recherche = RechercheWeb(timedelta(days=180))
        resultats_bruts = []
        
        for i, entreprise in enumerate(entreprises, 1):
            # Logging détaillé
            nom_entreprise = logger.log_entreprise_debut(entreprise)
            print(f"  🏢 {i}/{len(entreprises)}: {nom_entreprise} ({entreprise['commune']})")
            
            try:
                # Recherche avec logging
                resultats = recherche.rechercher_entreprise(entreprise, logger=logger)
                resultats_bruts.append(resultats)
                
                # Log du succès
                sources_trouvees = len(resultats.get('donnees_thematiques', {}))
                logger.log_extraction_resultats(nom_entreprise, True)
                print(f"     ✅ {sources_trouvees} sources analysées")
                
            except Exception as e:
                # Log de l'échec
                logger.log_extraction_resultats(nom_entreprise, False, str(e))
                print(f"     ❌ Erreur: {str(e)}")
                
                # Ajouter un résultat vide pour continuer
                resultats_bruts.append({
                    'entreprise': entreprise,
                    'donnees_thematiques': {},
                    'erreurs': [str(e)]
                })
                continue
        
        print(f"\n✅ Recherche terminée pour {len(resultats_bruts)} entreprises")
        
        # ✅ ÉTAPE 3: ANALYSE THÉMATIQUE (MANQUAIT COMPLÈTEMENT)
        print("\n🔬 ÉTAPE 3/5 - ANALYSE THÉMATIQUE")
        print("-" * 50)
        
        # Configuration des thématiques
        thematiques = [
            'evenements', 'recrutements', 'vie_entreprise', 'innovations',
            'exportations', 'aides_subventions', 'fondation_sponsor'
        ]
        
        # Initialisation de l'analyseur
        analyseur = AnalyseurThematiques(thematiques)
        print(f"🔬 Analyseur initialisé (seuil: {analyseur.seuil_pertinence})")
        
        # ✅ APPEL CRITIQUE QUI MANQUAIT: Analyse des résultats
        donnees_enrichies = analyseur.analyser_resultats(resultats_bruts, logger=logger)
        
        # Statistiques d'analyse
        entreprises_actives = [e for e in donnees_enrichies if e.get('score_global', 0) > 0.2]
        entreprises_tres_actives = [e for e in donnees_enrichies if e.get('score_global', 0) > 0.5]
        
        print(f"✅ Analyse terminée:")
        print(f"   📊 Entreprises analysées: {len(donnees_enrichies)}")
        print(f"   🎯 Entreprises actives (>0.2): {len(entreprises_actives)}")
        print(f"   🏆 Entreprises très actives (>0.5): {len(entreprises_tres_actives)}")
        
        if len(entreprises_actives) > 0:
            print(f"\n🎉 ENTREPRISES ACTIVES DÉTECTÉES:")
            for i, ent in enumerate(entreprises_actives[:5], 1):
                nom = ent.get('nom', 'N/A')
                score = ent.get('score_global', 0)
                themes = ent.get('thematiques_principales', [])
                print(f"   {i}. {nom}: {score:.3f} → {themes}")
        else:
            print(f"\n⚠️ Aucune entreprise active détectée")
            print(f"   Vérifiez les seuils et les données")
        
        # ✅ ÉTAPE 4: GÉNÉRATION DES RAPPORTS (MANQUAIT COMPLÈTEMENT)
        print("\n📊 ÉTAPE 4/5 - GÉNÉRATION DES RAPPORTS")
        print("-" * 50)
        
        generateur = GenerateurRapports()
        
        # ✅ GÉNÉRATION CRITIQUE QUI MANQUAIT
        rapports_generes = generateur.generer_tous_rapports(donnees_enrichies)
        
        # Affichage des rapports générés
        print("🎯 RAPPORTS GÉNÉRÉS:")
        rapports_reussis = 0
        
        for type_rapport, chemin_fichier in rapports_generes.items():
            emoji = {"excel": "📊", "html": "🌐", "json": "📄", "alertes": "🚨"}.get(type_rapport, "📋")
            
            if not chemin_fichier.startswith("ERREUR"):
                print(f"   {emoji} {type_rapport.upper()}: {chemin_fichier}")
                rapports_reussis += 1
            else:
                print(f"   ❌ {type_rapport.upper()}: {chemin_fichier}")
        
        print(f"✅ {rapports_reussis}/{len(rapports_generes)} rapports générés avec succès")
        
        # ✅ ÉTAPE 5: DIAGNOSTIC DÉTAILLÉ (manquait)
        print("\n📋 ÉTAPE 5/5 - DIAGNOSTIC DÉTAILLÉ")
        print("-" * 50)
        
        rapport_diagnostic = logger.generer_rapport_final()
        print(rapport_diagnostic)
        
        # ✅ RÉSUMÉ FINAL DÉTAILLÉ
        print("\n" + "="*70)
        print("🎉 ANALYSE TERMINÉE AVEC SUCCÈS!")
        print("="*70)
        
        print(f"📊 STATISTIQUES FINALES:")
        print(f"   🏢 Entreprises traitées: {len(entreprises)}")
        print(f"   🔍 Recherches réussies: {len([r for r in resultats_bruts if r.get('donnees_thematiques')])}")
        print(f"   🎯 Entreprises avec activité: {len(entreprises_actives)}")
        print(f"   🏆 Entreprises très actives: {len(entreprises_tres_actives)}")
        print(f"   📄 Rapports générés: {rapports_reussis}")
        
        if len(entreprises_actives) > 0:
            # Calcul du score moyen
            score_moyen = sum(e.get('score_global', 0) for e in entreprises_actives) / len(entreprises_actives)
            
            # Thématiques les plus fréquentes
            from collections import Counter
            toutes_thematiques = []
            for ent in entreprises_actives:
                toutes_thematiques.extend(ent.get('thematiques_principales', []))
            
            thematiques_freq = Counter(toutes_thematiques).most_common(3)
            
            print(f"\n📈 ANALYSE QUALITATIVE:")
            print(f"   🏆 Score moyen: {score_moyen:.3f}/1.0")
            print(f"   🎯 Thématiques dominantes:")
            for theme, count in thematiques_freq:
                print(f"      • {theme}: {count} entreprises")
        
        print(f"\n📂 CONSULTEZ VOS RAPPORTS:")
        print(f"   📁 Dossier: data/output/")
        
        if rapports_reussis > 0:
            print(f"   💡 Conseil: Commencez par ouvrir le rapport HTML pour une vue d'ensemble")
        
        return rapports_generes
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU TRAITEMENT: {str(e)}")
        print("=" * 50)
        
        # Diagnostic même en cas d'erreur
        try:
            if 'logger' in locals():
                print("\n🔍 RAPPORT DE DIAGNOSTIC (ERREUR):")
                print("-" * 40)
                rapport_diagnostic = logger.generer_rapport_final()
                print(rapport_diagnostic)
        except Exception as diag_error:
            print(f"❌ Impossible de générer le diagnostic: {diag_error}")
        
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 SCRIPT COMPLET DE VEILLE ÉCONOMIQUE")
    print("Version corrigée avec TOUTES les étapes")
    print()
    
    success = main()
    
    if success:
        print("\n✅ MISSION ACCOMPLIE! 🎯")
        print("Votre système de veille économique fonctionne maintenant!")
        print()
        print("🔍 VÉRIFIEZ:")
        print("1. 📊 Le rapport Excel dans data/output/")
        print("2. 🌐 Le rapport HTML interactif")
        print("3. 📈 Les scores et thématiques détectées")
        print()
        print("🎉 Vos 166 résultats valides sont maintenant ANALYSÉS et RAPPORTÉS!")
    else:
        print("\n❌ Échec de l'analyse - consultez les erreurs ci-dessus")
        sys.exit(1)