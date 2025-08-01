#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal pour la veille économique PME territoriale - VERSION CORRIGÉE
Analyse ciblée des PME sur un territoire spécifique avec codes postaux
"""

import os
import sys
import traceback
from datetime import timedelta
from typing import List, Dict
import pandas as pd
import yaml
from pathlib import Path

# Ajout du dossier scripts au path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from scripts.analyseur_thematiques import AnalyseurThematiques
from scripts.extracteur_donnees import ExtracteurDonnees
from scripts.filtreur_pme import FiltreurPME
from scripts.generateur_rapports import GenerateurRapports
from scripts.recherche_web import RechercheWeb
from scripts.diagnostic_logger import DiagnosticLogger

def valider_configuration_pme():
    """Valide que la configuration PME est correcte"""
    print("🔍 Validation de la configuration PME...")
    
    try:
        # Vérification fichier de configuration
        config_path = "config/parametres.yaml"
        if not os.path.exists(config_path):
            print(f"❌ Fichier de configuration manquant: {config_path}")
            return False
        
        # Chargement et validation configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Vérification territoire
        territoire = config.get('territoire', {})
        codes_postaux = territoire.get('codes_postaux_cibles', [])
        communes = territoire.get('communes_prioritaires', [])
        
        if not codes_postaux and not communes:
            print("❌ Aucun territoire configuré (codes postaux ou communes)")
            return False
        
        print(f"✅ Configuration territoire valide:")
        print(f"   📮 {len(codes_postaux)} codes postaux")
        print(f"   🏘️ {len(communes)} communes prioritaires")
        
        # Vérification FiltreurPME
        filtreur = FiltreurPME(config_path)
        print(f"✅ FiltreurPME initialisé correctement")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur validation configuration: {e}")
        return False


def extraire_code_postal_depuis_adresse(adresse: str) -> str:
    """Extraction du code postal depuis l'adresse complète"""
    import re
    
    if not adresse:
        return ""
    
    # Recherche pattern code postal français (5 chiffres)
    match = re.search(r'\b(\d{5})\b', adresse)
    return match.group(1) if match else ""


def synchroniser_donnees_entreprises(entreprises: List[Dict]) -> List[Dict]:
    """Synchronise et enrichit les données d'entreprises pour la compatibilité PME"""
    print("🔄 Synchronisation des données d'entreprises...")
    
    entreprises_synchronisees = []
    
    for entreprise in entreprises:
        # Copie de l'entreprise
        entreprise_sync = entreprise.copy()
        
        # ✅ AJOUT : Code postal détecté si manquant
        if 'code_postal_detecte' not in entreprise_sync:
            adresse = entreprise_sync.get('adresse_complete', '')
            code_postal = extraire_code_postal_depuis_adresse(adresse)
            entreprise_sync['code_postal_detecte'] = code_postal
            
            if code_postal:
                print(f"   📮 Code postal détecté: {entreprise_sync['nom'][:30]} → {code_postal}")
        
        # ✅ AJOUT : Nom commercial si pertinent
        nom = entreprise_sync.get('nom', '')
        enseigne = entreprise_sync.get('enseigne', '')
        
        if enseigne and enseigne != nom:
            entreprise_sync['nom_commercial'] = enseigne
        elif any(mot in nom.upper() for mot in ['BOULANGERIE', 'RESTAURANT', 'CAFE', 'GARAGE', 'COIFFURE']):
            entreprise_sync['nom_commercial'] = nom
        
        # ✅ AJOUT : Secteur simplifié
        secteur_naf = entreprise_sync.get('secteur_naf', '').lower()
        entreprise_sync['secteur_simplifie'] = simplifier_secteur_pour_pme(secteur_naf)
        
        entreprises_synchronisees.append(entreprise_sync)
    
    print(f"✅ {len(entreprises_synchronisees)} entreprises synchronisées")
    return entreprises_synchronisees


def simplifier_secteur_pour_pme(secteur_naf: str) -> str:
    """Simplification du secteur NAF pour les PME locales"""
    if not secteur_naf:
        return ""
    
    secteur_lower = secteur_naf.lower()
    
    # Mapping spécifique PME françaises
    mappings_pme = {
        'boulangerie': 'boulangerie',
        'restaurant': 'restaurant', 
        'coiffure': 'coiffeur',
        'garage': 'garage',
        'pharmacie': 'pharmacie',
        'construction': 'construction',
        'plomberie': 'plombier',
        'électricité': 'électricien',
        'maçonnerie': 'maçon',
        'commerce de détail': 'magasin',
        'transport': 'transport',
        'conseil': 'conseil',
        'informatique': 'informatique',
        'immobilier': 'immobilier',
        'location': 'location'
    }
    
    for secteur_long, secteur_court in mappings_pme.items():
        if secteur_long in secteur_lower:
            return secteur_court
    
    # Fallback : premier mot significatif
    mots = secteur_naf.split()
    return mots[0] if mots else ""


def creer_adapter_requetes_pme(recherche_instance):
    """Crée un adaptateur pour les requêtes PME territoriales"""
    
    def adapter_requetes_pme(nom_entreprise, commune, thematique):
        """Adaptateur de signature pour les requêtes PME"""
        # Construction d'un dict entreprise temporaire
        entreprise_temp = {
            'nom': nom_entreprise,
            'commune': commune,
            'code_postal_detecte': '',
            'secteur_naf': '',
            'secteur_simplifie': '',
            'nom_commercial': None,
            'adresse_complete': f"{commune}"
        }
        
        # Appel de la vraie méthode PME
        return recherche_instance.construire_requetes_pme_territoriales(entreprise_temp, thematique)
    
    return adapter_requetes_pme


def debug_seuils_utilises():
    """Debug pour identifier tous les seuils utilisés"""
    print("🔍 SEUILS DE CONFIANCE UTILISÉS:")
    
    # 1. Configuration YAML
    try:
        with open("config/parametres.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        print(f"📋 Config YAML:")
        validation_config = config.get('validation', {})
        seuils_pme_config = config.get('seuils_pme', {})
        
        print(f"   score_entreprise_minimum: {validation_config.get('score_entreprise_minimum', 'N/A')}")
        print(f"   validation_minimum: {seuils_pme_config.get('validation_minimum', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur lecture config: {e}")
    
    # 2. Module IA (optionnel)
    try:
        from ai_validation_module import AIValidationModule
        print(f"🤖 Module IA disponible")
    except ImportError:
        print(f"⚠️ Module IA non disponible (optionnel)")
    except Exception as e:
        print(f"❌ Erreur module IA: {e}")
    
    # 3. Modules de base
    try:
        print(f"🔍 Modules de base:")
        print(f"   ✅ RechercheWeb")
        print(f"   ✅ AnalyseurThematiques") 
        print(f"   ✅ FiltreurPME")
        print(f"   ✅ GenerateurRapports")
    except Exception as e:
        print(f"❌ Erreur modules de base: {e}")


def main_pme_territorial():
    """Version adaptée PME avec codes postaux - CORRIGÉE"""

    print("🎯 VEILLE ÉCONOMIQUE PME - TERRITOIRE SPÉCIFIQUE")
    print("=" * 70)
    
    # ✅ VALIDATION PRÉALABLE
    if not valider_configuration_pme():
        print("❌ Configuration invalide - arrêt du traitement")
        return None
    
    # Configuration
    fichier_excel = "data/input/entreprises_base.xlsx"
    nb_entreprises = 100
    
    # Vérification fichier source
    if not os.path.exists(fichier_excel):
        print(f"❌ Fichier source manquant: {fichier_excel}")
        print("📁 Veuillez placer votre fichier Excel dans data/input/")
        return None
    
    # Initialisation du logger
    logger = DiagnosticLogger()
    
    try:
        print(f"📂 Fichier source: {fichier_excel}")
        print(f"🎯 Analyse de {nb_entreprises} entreprises PME")
        print()
        
        # ✅ ÉTAPE 1: Extraction avec filtrage PME territorial
        print("📊 ÉTAPE 1/5 - EXTRACTION ET FILTRAGE PME")
        print("-" * 50)
        
        extracteur = ExtracteurDonnees(fichier_excel)
        toutes_entreprises = extracteur.extraire_echantillon(nb_entreprises * 3)  # Plus large pour compenser le filtrage
        
        print(f"✅ {len(toutes_entreprises)} entreprises extraites du fichier")
        
        # ✅ FILTRAGE TERRITORIAL
        filtreur = FiltreurPME()
        entreprises_territoire = filtreur.filtrer_par_territoire(toutes_entreprises)
        
        if len(entreprises_territoire) == 0:
            print("❌ AUCUNE ENTREPRISE dans votre territoire !")
            print("💡 Vérifiez vos codes postaux dans config/parametres.yaml")
            return None
        
        print(f"🌍 {len(entreprises_territoire)} entreprises dans le territoire")
        
        # ✅ FILTRAGE PME RECHERCHABLES
        pme_recherchables = filtreur.filtrer_pme_recherchables(entreprises_territoire)
        
        if len(pme_recherchables) == 0:
            print("❌ AUCUNE PME recherchable détectée !")
            print("💡 Critères de filtrage peut-être trop stricts")
            return None
        
        print(f"🏢 {len(pme_recherchables)} PME recherchables identifiées")
        
        # Limitation au nombre final souhaité
        entreprises_finales = pme_recherchables[:nb_entreprises]
        
        # ✅ SYNCHRONISATION DES DONNÉES
        entreprises_finales = synchroniser_donnees_entreprises(entreprises_finales)
        
        print(f"\n📊 SÉLECTION FINALE:")
        print(f"   🌍 Territoire: {len(entreprises_territoire)} entreprises")
        print(f"   🏢 PME recherchables: {len(pme_recherchables)}")
        print(f"   🎯 Échantillon final: {len(entreprises_finales)}")
        
        # ✅ ÉTAPE 2: Recherche web adaptée PME
        print(f"\n🔍 ÉTAPE 2/5 - RECHERCHE WEB PME TERRITORIALE")
        print("-" * 50)
        
        recherche = RechercheWeb(timedelta(days=180))
        
        # ✅ CORRECTION CRITIQUE: Adapter les requêtes PME
        adapter_requetes = creer_adapter_requetes_pme(recherche)
        recherche.construire_requetes_intelligentes = adapter_requetes
        print("✅ Adaptateur de requêtes PME configuré")
        
        resultats_bruts = []
        
        for i, entreprise in enumerate(entreprises_finales, 1):
            nom_entreprise = logger.log_entreprise_debut(entreprise)
            print(f"  🏢 {i}/{len(entreprises_finales)}: {nom_entreprise} ({entreprise.get('commune', 'N/A')})")
            
            try:
                resultats = recherche.rechercher_entreprise(entreprise, logger=logger)
                resultats_bruts.append(resultats)
                
                # Log succès
                sources_trouvees = len(resultats.get('donnees_thematiques', {}))
                logger.log_extraction_resultats(nom_entreprise, True)
                print(f"     ✅ {sources_trouvees} sources analysées")
                
            except Exception as e:
                logger.log_extraction_resultats(nom_entreprise, False, str(e))
                print(f"     ❌ Erreur: {str(e)}")
                
                # Résultat vide pour continuer
                resultats_bruts.append({
                    'entreprise': entreprise,
                    'donnees_thematiques': {},
                    'erreurs': [str(e)]
                })
                continue
        
        print(f"\n✅ Recherche terminée pour {len(resultats_bruts)} entreprises")
        
        # ✅ ÉTAPE 3: Analyse avec seuils PME
        print(f"\n🔬 ÉTAPE 3/5 - ANALYSE THÉMATIQUE PME")
        print("-" * 50)
        
        thematiques = ['recrutements', 'evenements', 'innovations', 'vie_entreprise']
        analyseur = AnalyseurThematiques(thematiques)
        
        # ✅ ADAPTATION SEUILS POUR PME
        analyseur.seuil_pertinence = 0.25  # Plus permissif que 0.5
        print(f"🔧 Seuils PME adaptés: pertinence = {analyseur.seuil_pertinence}")
        
        donnees_enrichies = analyseur.analyser_resultats(resultats_bruts, logger=logger)
        
        # Statistiques d'analyse
        entreprises_actives = [e for e in donnees_enrichies if e.get('score_global', 0) > 0.2]
        entreprises_tres_actives = [e for e in donnees_enrichies if e.get('score_global', 0) > 0.5]
        
        print(f"✅ Analyse PME terminée:")
        print(f"   📊 Entreprises analysées: {len(donnees_enrichies)}")
        print(f"   🎯 PME actives (>0.2): {len(entreprises_actives)}")
        print(f"   🏆 PME très actives (>0.5): {len(entreprises_tres_actives)}")
        
        # ✅ ÉTAPE 4: Génération des rapports
        print(f"\n📊 ÉTAPE 4/5 - GÉNÉRATION RAPPORTS PME")
        print("-" * 50)
        
        generateur = GenerateurRapports()
        rapports = generateur.generer_tous_rapports(donnees_enrichies)
        
        # Affichage des rapports générés
        rapports_reussis = 0
        print("🎯 RAPPORTS PME GÉNÉRÉS:")
        
        for type_rapport, chemin_fichier in rapports.items():
            emoji = {"excel": "📊", "html": "🌐", "json": "📄", "alertes": "🚨"}.get(type_rapport, "📋")
            
            if not chemin_fichier.startswith("ERREUR"):
                print(f"   {emoji} {type_rapport.upper()}: {chemin_fichier}")
                rapports_reussis += 1
            else:
                print(f"   ❌ {type_rapport.upper()}: {chemin_fichier}")
        
        print(f"✅ {rapports_reussis}/{len(rapports)} rapports PME générés")
        
        # ✅ ÉTAPE 5: Diagnostic final
        print(f"\n📋 ÉTAPE 5/5 - DIAGNOSTIC PME TERRITORIAL")
        print("-" * 50)
        
        rapport_diagnostic = logger.generer_rapport_final()
        print(rapport_diagnostic)
        
        # ✅ RÉSUMÉ FINAL PME
        print(f"\n🎉 ANALYSE PME TERRITORIALE TERMINÉE !")
        print("=" * 70)
        
        print(f"📊 RÉSULTATS PME:")
        print(f"   🏘️ Territoire analysé: {len(set(e.get('commune', '') for e in entreprises_finales))} communes")
        print(f"   🏢 PME traitées: {len(entreprises_finales)}")
        print(f"   🎯 PME avec activité détectée: {len(entreprises_actives)}")
        print(f"   📄 Rapports générés: {rapports_reussis}")
        
        if len(entreprises_actives) > 0:
            print(f"\n🏆 TOP PME ACTIVES:")
            top_pme = sorted(entreprises_actives, key=lambda x: x.get('score_global', 0), reverse=True)[:5]
            
            for i, pme in enumerate(top_pme, 1):
                nom = pme.get('nom', 'N/A')
                commune = pme.get('commune', 'N/A')
                score = pme.get('score_global', 0)
                themes = pme.get('thematiques_principales', [])
                
                print(f"   {i}. {nom[:40]} ({commune})")
                print(f"      Score: {score:.3f} | Thématiques: {', '.join(themes)}")
        
        print(f"\n📂 CONSULTEZ VOS RAPPORTS PME:")
        print(f"   📁 Dossier: data/output/")
        print(f"   💡 Conseil: Ouvrez le rapport HTML pour une vue d'ensemble territoriale")
        
        return rapports
        
    except Exception as e:
        print(f"\n❌ ERREUR TRAITEMENT PME: {str(e)}")
        print("=" * 50)
        
        # Diagnostic d'erreur
        try:
            if 'logger' in locals():
                print("\n🔍 DIAGNOSTIC D'ERREUR:")
                rapport_diagnostic = logger.generer_rapport_final()
                print(rapport_diagnostic)
        except Exception as diag_error:
            print(f"❌ Diagnostic impossible: {diag_error}")
        
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🏢 VEILLE ÉCONOMIQUE PME TERRITORIALE - VERSION CORRIGÉE")
    print("=" * 70)
    print("Lancement de l'analyse PME avec codes postaux...")
    print()
    
    try:
        # ✅ DEBUG PRÉALABLE
        debug_seuils_utilises()
        print()
        
        # ✅ EXÉCUTION PRINCIPALE
        rapports = main_pme_territorial()
        
        if rapports:
            print("\n✅ ANALYSE PME RÉUSSIE ! 🎉")
            print("🎯 Vos PME territoriales ont été analysées avec succès !")
            print()
            print("🔍 PROCHAINES ÉTAPES:")
            print("1. 📊 Consultez le rapport Excel pour les données détaillées")
            print("2. 🌐 Ouvrez le rapport HTML pour la visualisation territoriale")
            print("3. 🔧 Ajustez les paramètres si nécessaire dans config/parametres.yaml")
            print("4. 🚀 Relancez l'analyse pour un suivi périodique")
        else:
            print("\n❌ ANALYSE PME ÉCHOUÉE")
            print("💡 Consultez les messages d'erreur ci-dessus pour identifier le problème")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Analyse PME interrompue par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
        traceback.print_exc()
        sys.exit(1)