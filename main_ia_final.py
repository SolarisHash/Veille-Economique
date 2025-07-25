#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal avec IA + Correction Qualité FONCTIONNEL
Version finale intégrée
"""

from datetime import timedelta
import os
import sys
from pathlib import Path
sys.path.insert(0, "scripts")

# Imports nécessaires
from scripts.extracteur_donnees import ExtracteurDonnees
from scripts.recherche_web import RechercheWeb
from scripts.analyseur_thematiques import AnalyseurThematiques
from scripts.generateur_rapports import GenerateurRapports
from scripts.diagnostic_logger import DiagnosticLogger

# Nouveaux modules IA
from ai_validation_module import AIValidationModule
from data_quality_fixer import DataQualityFixer

def main():
    """Version finale fonctionnelle avec IA"""
    print("🚀 VEILLE ÉCONOMIQUE - VERSION IA FINALE")
    print("=" * 60)
    
    fichier_excel = "data/input/entreprises_test_reelles.xlsx"
    if not os.path.exists(fichier_excel):
        fichier_excel = "data/input/entreprises_base.xlsx"
    
    if not os.path.exists(fichier_excel):
        print("❌ Fichier Excel manquant")
        return
    
    # Configuration
    nb_entreprises = 10
    logger = DiagnosticLogger()
    
    try:
        print(f"🎯 Analyse de {nb_entreprises} entreprises avec IA + Correction Qualité")
        
        # 1. Extraction
        extracteur = ExtracteurDonnees(fichier_excel)
        entreprises = extracteur.extraire_echantillon(nb_entreprises)
        print(f"✅ {len(entreprises)} entreprises extraites")
        
        # 2. Recherche web
        recherche = RechercheWeb(timedelta(days=180))
        resultats_bruts = []
        
        for i, entreprise in enumerate(entreprises, 1):
            nom = logger.log_entreprise_debut(entreprise)
            print(f"  🏢 {i}/{len(entreprises)}: {nom}")
            
            try:
                resultats = recherche.rechercher_entreprise(entreprise, logger=logger)
                resultats_bruts.append(resultats)
                logger.log_extraction_resultats(nom, True)
            except Exception as e:
                logger.log_extraction_resultats(nom, False, str(e))
                resultats_bruts.append({'entreprise': entreprise, 'donnees_thematiques': {}})
        
        # 3. Analyse avec IA + Correction Qualité
        thematiques = ['evenements', 'recrutements', 'vie_entreprise', 'innovations']
        analyseur = AnalyseurThematiques(thematiques)
        
        # Intégration IA automatique
        ai_module = AIValidationModule()
        ai_module.integrate_with_existing_analyzer(analyseur)
        
        donnees_enrichies = analyseur.analyser_resultats(resultats_bruts, logger=logger)
        
        # 4. Rapports
        generateur = GenerateurRapports()
        rapports = generateur.generer_tous_rapports(donnees_enrichies)
        
        # 5. Diagnostic
        print(logger.generer_rapport_final())
        
        print("\n🎉 ANALYSE TERMINÉE AVEC SUCCÈS!")
        print("Consultez les rapports dans data/output/")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
