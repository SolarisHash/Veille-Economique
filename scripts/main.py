#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de veille économique territoriale
Analyse automatisée des entreprises selon 7 thématiques définies
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import json
import yaml
from pathlib import Path

# Import des modules du projet
from scripts.extracteur_donnees import ExtracteurDonnees
from scripts.recherche_web import RechercheWeb
from scripts.analyseur_thematiques import AnalyseurThematiques
from scripts.generateur_rapports import GenerateurRapports

class VeilleEconomique:
    """Classe principale pour la veille économique"""
    
    def __init__(self, config_path="config/parametres.yaml"):
        """Initialisation du système de veille"""
        self.config = self._charger_config(config_path)
        self.periode_recherche = timedelta(days=180)  # 6 mois
        self.setup_directories()
        
    def setup_directories(self):
        """Création de la structure des dossiers"""
        directories = [
            "data/input",
            "data/output", 
            "data/cache",
            "scripts",
            "config"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
    def _charger_config(self, config_path):
        """Chargement de la configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Fichier de configuration non trouvé: {config_path}")
            return self._config_defaut()
            
    def _config_defaut(self):
        """Configuration par défaut"""
        return {
            "echantillon_test": 10,
            "periode_mois": 6,
            "thematiques": [
                "evenements",
                "recrutements", 
                "vie_entreprise",
                "innovations",
                "exportations",
                "aides_subventions",
                "fondation_sponsor"
            ]
        }
        
    def traiter_echantillon(self, fichier_excel, nb_entreprises=10):
        """Traitement d'un échantillon d'entreprises"""
        print(f"🚀 Démarrage analyse échantillon ({nb_entreprises} entreprises)")
        
        # 1. Extraction des données
        extracteur = ExtracteurDonnees(fichier_excel)
        entreprises = extracteur.extraire_echantillon(nb_entreprises)
        print(f"✅ {len(entreprises)} entreprises extraites")
        
        # 2. Recherche web pour chaque entreprise
        recherche = RechercheWeb(self.periode_recherche)
        resultats_bruts = []
        
        for i, entreprise in enumerate(entreprises, 1):
            print(f"🔍 Recherche {i}/{len(entreprises)}: {entreprise['nom']}")
            resultats = recherche.rechercher_entreprise(entreprise)
            resultats_bruts.append(resultats)
            
        # 3. Analyse thématique
        analyseur = AnalyseurThematiques(self.config['thematiques'])
        donnees_enrichies = analyseur.analyser_resultats(resultats_bruts)
        
        # 4. Génération des rapports
        generateur = GenerateurRapports()
        fichier_sortie = generateur.generer_rapport_excel(donnees_enrichies)
        
        print(f"🎯 Analyse terminée - Résultats: {fichier_sortie}")
        return fichier_sortie
        
    def traiter_toutes_entreprises(self, fichier_excel):
        """Traitement de toutes les entreprises (mode production)"""
        print("🏭 Démarrage analyse complète")
        # À implémenter après validation de l'échantillon
        pass
        
    def generer_rapport_synthese(self):
        """Génération du rapport de synthèse par commune"""
        print("📊 Génération rapport synthétique")
        # À implémenter
        pass

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🏢 SYSTÈME DE VEILLE ÉCONOMIQUE TERRITORIALE")
    print("=" * 60)
    
    # Initialisation
    veille = VeilleEconomique()
    
    # Vérification fichier Excel
    fichier_entreprises = "data/input/entreprises_base.xlsx"
    if not os.path.exists(fichier_entreprises):
        print(f"❌ Fichier manquant: {fichier_entreprises}")
        print("📁 Veuillez placer votre fichier Excel dans data/input/")
        return
    
    # Traitement échantillon test
    try:
        resultat = veille.traiter_echantillon(fichier_entreprises, nb_entreprises=10)
        print(f"✅ Traitement terminé avec succès")
        print(f"📄 Fichier de résultats: {resultat}")
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()