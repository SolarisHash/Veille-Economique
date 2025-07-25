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
from scripts.diagnostic_logger import DiagnosticLogger



class VeilleEconomique:
    """Classe principale pour la veille économique"""
    
    def __init__(self, config_path="config/parametres.yaml"):
        """Initialisation du système de veille"""
        self.config = self._charger_config(config_path)
        self.periode_recherche = timedelta(days=180)  # 6 mois
        self.setup_directories()
        self.logger = DiagnosticLogger()

        
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
        """Traitement d'un échantillon d'entreprises avec logging détaillé"""
        print(f"🚀 Démarrage analyse échantillon ({nb_entreprises} entreprises)")
        print("🔍 Diagnostic détaillé activé")
        print("=" * 70)
        
        try:
            # 1. Extraction des données
            print("\n📊 ÉTAPE 1/5 - EXTRACTION DES DONNÉES")
            print("-" * 40)
            extracteur = ExtracteurDonnees(fichier_excel)
            entreprises = extracteur.extraire_echantillon(nb_entreprises)
            print(f"✅ {len(entreprises)} entreprises extraites avec succès")
            
            # 2. Recherche web pour chaque entreprise AVEC logging
            print("\n🔍 ÉTAPE 2/5 - RECHERCHE WEB")
            print("-" * 40)
            recherche = RechercheWeb(self.periode_recherche)
            resultats_bruts = []
            
            for i, entreprise in enumerate(entreprises, 1):
                # ✅ DÉBUT LOG ENTREPRISE
                nom_entreprise = self.logger.log_entreprise_debut(entreprise)
                
                print(f"\n🏢 Entreprise {i}/{len(entreprises)}: {nom_entreprise} ({entreprise['commune']})")
                
                try:
                    # Recherche avec logging intégré
                    resultats = recherche.rechercher_entreprise(entreprise, logger=self.logger)
                    resultats_bruts.append(resultats)
                    
                    # Log du succès d'extraction
                    sources_trouvees = len(resultats.get('donnees_thematiques', {}))
                    self.logger.log_extraction_resultats(nom_entreprise, True)
                    print(f"   ✅ {sources_trouvees} sources analysées")
                    
                except Exception as e:
                    # Log de l'échec
                    self.logger.log_extraction_resultats(nom_entreprise, False, str(e))
                    print(f"   ❌ Erreur: {str(e)}")
                    
                    # Ajouter un résultat vide pour continuer
                    resultats_bruts.append({
                        'entreprise': entreprise,
                        'donnees_thematiques': {},
                        'erreurs': [str(e)]
                    })
                    continue
            
            print(f"\n✅ Recherche terminée pour {len(resultats_bruts)} entreprises")
            
            # 3. Analyse thématique AVEC logging
            print("\n🔬 ÉTAPE 3/5 - ANALYSE THÉMATIQUE")
            print("-" * 40)
            analyseur = AnalyseurThematiques(self.config['thematiques'])
            donnees_enrichies = analyseur.analyser_resultats(resultats_bruts, logger=self.logger)
            
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
            
            # ✅ GÉNÉRATION DU RAPPORT DE DIAGNOSTIC DÉTAILLÉ
            print("\n" + "="*80)
            print("🔍 RAPPORT DE DIAGNOSTIC DÉTAILLÉ")
            print("="*80)
            
            rapport_diagnostic = self.logger.generer_rapport_final()
            print(rapport_diagnostic)
            
            # Résumé final
            print("\n✅ ANALYSE TERMINÉE AVEC SUCCÈS!")
            print("=" * 50)
            self._afficher_resume_final(donnees_enrichies, rapports_generes)
            
            return rapports_generes
            
        except Exception as e:
            print(f"\n❌ ERREUR LORS DU TRAITEMENT: {str(e)}")
            print("=" * 50)
            
            # ✅ GÉNÉRATION DU RAPPORT DE DIAGNOSTIC MÊME EN CAS D'ERREUR
            try:
                if hasattr(self, 'logger'):
                    print("\n🔍 RAPPORT DE DIAGNOSTIC (ERREUR):")
                    print("-" * 40)
                    rapport_diagnostic = self.logger.generer_rapport_final()
                    print(rapport_diagnostic)
            except Exception as diag_error:
                print(f"❌ Impossible de générer le diagnostic: {diag_error}")
            
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

    def traiter_echantillon_avec_linkedin(self, fichier_excel, nb_entreprises=10):
        """Version enrichie avec collecte LinkedIn optionnelle"""
        print(f"🚀 Démarrage analyse échantillon + LinkedIn ({nb_entreprises} entreprises)")
        
        try:
            # 1-3. Étapes classiques (extraction, recherche web, analyse)
            extracteur = ExtracteurDonnees(fichier_excel)
            entreprises = extracteur.extraire_echantillon(nb_entreprises)
            
            recherche = RechercheWeb(self.periode_recherche)
            resultats_bruts = []
            
            for entreprise in entreprises:
                resultats = recherche.rechercher_entreprise(entreprise)
                resultats_bruts.append(resultats)
            
            analyseur = AnalyseurThematiques(self.config['thematiques'])
            donnees_enrichies = analyseur.analyser_resultats(resultats_bruts)
            
            # 4. ✅ NOUVELLE ÉTAPE : Intégration LinkedIn
            print("\n🔗 ÉTAPE BONUS - INTÉGRATION LINKEDIN")
            print("-" * 40)
            
            choix = input("Voulez-vous préparer la collecte LinkedIn ? (y/N): ").lower()
            
            if choix in ['y', 'yes', 'oui']:
                success_linkedin = integrer_linkedin_veille(
                    entreprises=entreprises, 
                    max_entreprises=min(5, nb_entreprises)  # Limité pour test
                )
                
                if success_linkedin:
                    print("✅ Collecte LinkedIn préparée - suivez les instructions")
                    # Pause pour permettre à l'utilisateur de collecter
                    input("Appuyez sur Entrée après avoir collecté les données LinkedIn...")
                    
                    # 5. Intégration des données LinkedIn collectées
                    donnees_linkedin = self._charger_donnees_linkedin()
                    if donnees_linkedin:
                        donnees_enrichies = self._enrichir_avec_linkedin(donnees_enrichies, donnees_linkedin)
                        print(f"✅ {len(donnees_linkedin)} entreprises enrichies avec LinkedIn")
            
            # 5. Génération des rapports (comme avant)
            generateur = GenerateurRapports()
            rapports_generes = generateur.generer_tous_rapports(donnees_enrichies)
            
            return rapports_generes
            
        except Exception as e:
            print(f"❌ Erreur traitement avec LinkedIn: {e}")
            return None

    def _charger_donnees_linkedin(self):
        """Charge les données LinkedIn collectées"""
        try:
            donnees_linkedin = {}
            linkedin_dir = Path("data/linkedin/results")
            
            if linkedin_dir.exists():
                for fichier in linkedin_dir.glob("linkedin_*.json"):
                    try:
                        with open(fichier, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            company_name = data.get('company', {}).get('name')
                            if company_name:
                                donnees_linkedin[company_name] = data
                    except Exception as e:
                        print(f"⚠️ Erreur lecture {fichier}: {e}")
            
            return donnees_linkedin
        except Exception as e:
            print(f"❌ Erreur chargement LinkedIn: {e}")
            return {}

    def _enrichir_avec_linkedin(self, donnees_enrichies, donnees_linkedin):
        """Enrichit les données principales avec les posts LinkedIn"""
        try:
            for entreprise in donnees_enrichies:
                nom_entreprise = entreprise['nom']
                
                # Recherche correspondance (approximative)
                donnees_matching = None
                for nom_linkedin, data in donnees_linkedin.items():
                    if self._match_entreprise_linkedin(nom_entreprise, nom_linkedin):
                        donnees_matching = data
                        break
                
                if donnees_matching:
                    # Enrichissement avec données LinkedIn
                    entreprise['linkedin_data'] = {
                        'profil_entreprise': donnees_matching.get('company', {}),
                        'posts_recents': donnees_matching.get('posts', []),
                        'nombre_posts': len(donnees_matching.get('posts', [])),
                        'date_collecte': donnees_matching.get('extraction_metadata', {}).get('timestamp'),
                        'analyse_posts': self._analyser_posts_linkedin(donnees_matching.get('posts', []))
                    }
                    
                    # Mise à jour du score global avec bonus LinkedIn
                    if entreprise['linkedin_data']['nombre_posts'] > 0:
                        entreprise['score_global'] = min(
                            entreprise.get('score_global', 0) + 0.2,  # Bonus LinkedIn
                            1.0
                        )
                    
                    print(f"✅ {nom_entreprise} enrichi avec {len(donnees_matching.get('posts', []))} posts LinkedIn")
            
            return donnees_enrichies
            
        except Exception as e:
            print(f"❌ Erreur enrichissement LinkedIn: {e}")
            return donnees_enrichies

    def _match_entreprise_linkedin(self, nom_original, nom_linkedin):
        """Correspondance approximative entre noms d'entreprises"""
        # Normalisation des noms
        def normaliser(nom):
            return ''.join(c.lower() for c in nom if c.isalnum())
        
        nom1 = normaliser(nom_original)
        nom2 = normaliser(nom_linkedin)
        
        # Correspondance exacte
        if nom1 == nom2:
            return True
        
        # Correspondance partielle (mots en commun)
        mots1 = set(mot for mot in nom_original.lower().split() if len(mot) > 3)
        mots2 = set(mot for mot in nom_linkedin.lower().split() if len(mot) > 3)
        
        if mots1 and mots2:
            correspondance = len(mots1.intersection(mots2)) / len(mots1.union(mots2))
            return correspondance > 0.6
        
        return False

    def _analyser_posts_linkedin(self, posts):
        """Analyse thématique des posts LinkedIn"""
        try:
            if not posts:
                return {}
            
            analyse = {
                'themes_detectes': [],
                'engagement_moyen': 0,
                'types_contenu': {},
                'posts_pertinents': []
            }
            
            # Analyse par post
            for post in posts:
                texte = post.get('text', '').lower()
                
                # Détection thématique
                themes = []
                if any(mot in texte for mot in ['recrut', 'emploi', 'embauche', 'poste']):
                    themes.append('recrutements')
                if any(mot in texte for mot in ['innov', 'nouveau', 'lance', 'technologie']):
                    themes.append('innovations')
                if any(mot in texte for mot in ['événement', 'salon', 'conférence', 'rencontre']):
                    themes.append('evenements')
                if any(mot in texte for mot in ['partenariat', 'collaboration', 'développement']):
                    themes.append('vie_entreprise')
                
                if themes:
                    analyse['posts_pertinents'].append({
                        'texte': post.get('text', '')[:200] + '...',
                        'themes': themes,
                        'date': post.get('publish_date', ''),
                        'engagement': post.get('like_count', 0)
                    })
            
            # Synthèse
            tous_themes = []
            for post in analyse['posts_pertinents']:
                tous_themes.extend(post['themes'])
            
            from collections import Counter
            analyse['themes_detectes'] = [theme for theme, count in Counter(tous_themes).most_common(3)]
            
            return analyse
            
        except Exception as e:
            print(f"❌ Erreur analyse posts LinkedIn: {e}")
            return {}

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🏢 SYSTÈME DE VEILLE ÉCONOMIQUE TERRITORIALE")
    print("=" * 70)
    
    # Initialisation
    veille = VeilleEconomique()
    
    # Vérification fichier Excel
    fichier_entreprises = "data/input/entreprises_test.xlsx"
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