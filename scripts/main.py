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
            "logs",
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
        """Traitement d'un échantillon d'entreprises avec génération de tous les rapports"""
        print(f"🚀 Démarrage analyse échantillon ({nb_entreprises} entreprises)")
        print("=" * 70)
        
        try:
            # 1. Extraction des données
            print("\n📊 ÉTAPE 1/5 - EXTRACTION DES DONNÉES")
            print("-" * 40)
            extracteur = ExtracteurDonnees(fichier_excel)
            entreprises = extracteur.extraire_echantillon(nb_entreprises)
            print(f"✅ {len(entreprises)} entreprises extraites avec succès")
            
            # 2. Recherche web pour chaque entreprise
            print("\n🔍 ÉTAPE 2/5 - RECHERCHE WEB")
            print("-" * 40)
            recherche = RechercheWeb(self.periode_recherche)
            resultats_bruts = []
            
            for i, entreprise in enumerate(entreprises, 1):
                print(f"\n🏢 Entreprise {i}/{len(entreprises)}: {entreprise['nom']} ({entreprise['commune']})")
                resultats = recherche.rechercher_entreprise(entreprise)
                resultats_bruts.append(resultats)
                
                # Affichage résumé des résultats
                sources_trouvees = len(resultats.get('donnees_thematiques', {}))
                print(f"   ✅ {sources_trouvees} sources analysées")
                
            print(f"\n✅ Recherche terminée pour {len(resultats_bruts)} entreprises")
            
            # 3. Analyse thématique
            print("\n🔬 ÉTAPE 3/5 - ANALYSE THÉMATIQUE")
            print("-" * 40)
            analyseur = AnalyseurThematiques(self.config['thematiques'])
            donnees_enrichies = analyseur.analyser_resultats(resultats_bruts)
            
            # Statistiques d'analyse
            entreprises_actives = len([e for e in donnees_enrichies if e.get('score_global', 0) > 0.3])
            print(f"✅ {entreprises_actives}/{len(donnees_enrichies)} entreprises avec activité détectée")
            
            # 4. Génération du rapport d'analyse
            print("\n📊 ÉTAPE 4/5 - GÉNÉRATION RAPPORT ANALYSE")
            print("-" * 40)
            rapport_analyse = analyseur.generer_rapport_analyse(donnees_enrichies)
            self._afficher_resume_analyse(rapport_analyse)
            
            # 5. Génération de tous les rapports
            print("\n📄 ÉTAPE 5/5 - GÉNÉRATION RAPPORTS COMPLETS")
            print("-" * 40)
            generateur = GenerateurRapports()
            rapports_generes = generateur.generer_tous_rapports(donnees_enrichies)
            
            # Affichage des rapports générés
            print("\n🎯 RAPPORTS GÉNÉRÉS:")
            print("=" * 50)
            for type_rapport, chemin_fichier in rapports_generes.items():
                emoji = self._get_emoji_rapport(type_rapport)
                nom_rapport = self._get_nom_rapport(type_rapport)
                print(f"{emoji} {nom_rapport}")
                print(f"   📁 {chemin_fichier}")
                
            # Résumé final
            print("\n✅ ANALYSE TERMINÉE AVEC SUCCÈS!")
            print("=" * 50)
            self._afficher_resume_final(donnees_enrichies, rapports_generes)
            
            return rapports_generes
            
        except Exception as e:
            print(f"\n❌ ERREUR LORS DU TRAITEMENT: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
    def _afficher_resume_analyse(self, rapport_analyse):
        """Affichage du résumé d'analyse"""
        print(f"📊 Entreprises analysées: {rapport_analyse['nb_entreprises_analysees']}")
        print(f"🏆 Top 3 entreprises actives:")
        
        for i, (nom, score) in enumerate(rapport_analyse['entreprises_plus_actives'][:3], 1):
            print(f"   {i}. {nom} (Score: {score:.2f})")
            
        print(f"\n📈 Répartition par thématique:")
        for thematique, stats in rapport_analyse['statistiques_thematiques'].items():
            nom_thematique = thematique.replace('_', ' ').title()
            print(f"   • {nom_thematique}: {stats['nb_entreprises']} entreprises ({stats['pourcentage']:.1f}%)")
            
    def _afficher_resume_final(self, donnees_enrichies, rapports_generes):
        """Affichage du résumé final"""
        # Statistiques globales
        score_moyen = sum(e.get('score_global', 0) for e in donnees_enrichies) / len(donnees_enrichies)
        entreprises_actives = len([e for e in donnees_enrichies if e.get('score_global', 0) > 0.5])
        communes = len(set(e.get('commune', '') for e in donnees_enrichies))
        
        print(f"📊 Score moyen d'activité: {score_moyen:.2f}/1.0")
        print(f"🏢 Entreprises très actives: {entreprises_actives}/{len(donnees_enrichies)}")
        print(f"🏘️  Communes représentées: {communes}")
        
        # Thématiques les plus actives
        compteur_thematiques = {}
        for entreprise in donnees_enrichies:
            for thematique in entreprise.get('thematiques_principales', []):
                compteur_thematiques[thematique] = compteur_thematiques.get(thematique, 0) + 1
                
        if compteur_thematiques:
            thematiques_top = sorted(compteur_thematiques.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"\n🎯 Thématiques les plus actives:")
            for thematique, count in thematiques_top:
                nom_thematique = thematique.replace('_', ' ').title()
                print(f"   • {nom_thematique}: {count} entreprises")
                
        # Rappel des fichiers générés
        print(f"\n📂 Consultez les rapports dans le dossier: data/output/")
        print(f"💡 Conseil: Commencez par ouvrir le rapport HTML pour une vue d'ensemble")
        
    def _get_emoji_rapport(self, type_rapport):
        """Emoji pour chaque type de rapport"""
        emojis = {
            'excel': '📊',
            'html': '🌐',
            'json': '📄',
            'alertes': '🚨'
        }
        return emojis.get(type_rapport, '📋')
        
    def _get_nom_rapport(self, type_rapport):
        """Nom lisible pour chaque type de rapport"""
        noms = {
            'excel': 'Rapport Excel complet avec données enrichies',
            'html': 'Rapport HTML interactif avec visualisations',
            'json': 'Export JSON pour intégrations tierces',
            'alertes': 'Alertes ciblées par commune (JSON)'
        }
        return noms.get(type_rapport, f'Rapport {type_rapport}')
        
    def traiter_toutes_entreprises(self, fichier_excel):
        """Traitement de toutes les entreprises (mode production)"""
        print("🏭 Démarrage analyse complète")
        print("⚠️  Cette fonctionnalité sera disponible après validation de l'échantillon")
        
        # Vérification que l'échantillon a été validé
        if not self._echantillon_valide():
            print("❌ Veuillez d'abord valider l'échantillon avec run_echantillon.py")
            return
            
        # Code pour traitement complet à implémenter
        pass
        
    def _echantillon_valide(self):
        """Vérification que l'échantillon a été validé"""
        # Recherche de fichiers de résultats récents
        dossier_output = Path("data/output")
        if not dossier_output.exists():
            return False
            
        # Recherche de fichiers Excel récents (dernières 24h)
        for fichier in dossier_output.glob("veille_economique_*.xlsx"):
            age_fichier = datetime.now() - datetime.fromtimestamp(fichier.stat().st_mtime)
            if age_fichier < timedelta(days=1):
                return True
                
        return False
        
    def generer_rapport_synthese(self):
        """Génération du rapport de synthèse par commune"""
        print("📊 Génération rapport synthétique")
        print("⚠️  Cette fonctionnalité sera disponible après plusieurs analyses")
        pass

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🏢 SYSTÈME DE VEILLE ÉCONOMIQUE TERRITORIALE")
    print("=" * 70)
    
    # Initialisation
    veille = VeilleEconomique()
    
    # Vérification fichier Excel
    fichier_entreprises = "data/input/entreprises_base.xlsx"
    if not os.path.exists(fichier_entreprises):
        print(f"❌ Fichier manquant: {fichier_entreprises}")
        print("📁 Veuillez placer votre fichier Excel dans data/input/")
        print("💡 Le fichier doit contenir les colonnes requises:")
        print("   - SIRET, Nom courant/Dénomination, Commune, etc.")
        return
    
    # Traitement échantillon test
    try:
        print(f"📂 Fichier source: {fichier_entreprises}")
        print(f"🎯 Mode: Test échantillon (10 entreprises)")
        print()
        
        rapports = veille.traiter_echantillon(fichier_entreprises, nb_entreprises=10)
        
        if rapports:
            print("\n🎉 PROCHAINES ÉTAPES:")
            print("1. 📊 Ouvrez le rapport HTML pour une vue d'ensemble")
            print("2. 📋 Vérifiez les données dans le fichier Excel")
            print("3. 🔧 Ajustez les paramètres si nécessaire (config/parametres.yaml)")
            print("4. 🚀 Lancez l'analyse complète sur toutes les entreprises")
        else:
            print("\n❌ Échec du traitement - consultez les erreurs ci-dessus")
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()