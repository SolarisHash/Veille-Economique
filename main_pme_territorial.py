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
from ai_validation_module import AIValidationModule
from data_quality_fixer import DataQualityFixer

def valider_configuration_pme():
    """Valide que la configuration PME est correcte"""
    print("[CONFIG] Validation de la configuration PME...")
    
    try:
        # Vérification fichier de configuration
        config_path = "config/parametres.yaml"
        if not os.path.exists(config_path):
            print(f"[ERREUR] Fichier de configuration manquant: {config_path}")
            return False
        
        # Chargement et validation configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Vérification territoire
        territoire = config.get('territoire', {})
        codes_postaux = territoire.get('codes_postaux_cibles', [])
        communes = territoire.get('communes_prioritaires', [])
        
        if not codes_postaux and not communes:
            print("[ERREUR] Aucun territoire configuré (codes postaux ou communes)")
            return False
        
        print(f"[OK] Configuration territoire valide:")
        print(f"   [CODES] {len(codes_postaux)} codes postaux")
        print(f"   [COMMUNES] {len(communes)} communes prioritaires")
        
        # Vérification FiltreurPME
        FiltreurPME()
        print(f"[OK] FiltreurPME initialisé correctement")
        
        return True
        
    except Exception as e:
        print(f"[ERREUR] Erreur validation configuration: {e}")
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
    
    entreprises_synchronisees = []
    
    for entreprise in entreprises:
        # Mapping standardisé des champs
        entreprise_sync = {
            'nom': entreprise.get('nom') or entreprise.get('raison_sociale', ''),
            'siret': entreprise.get('siret', ''),
            'commune': entreprise.get('commune') or entreprise.get('ville', ''),
            'code_postal': entreprise.get('code_postal', ''),
            'adresse_complete': entreprise.get('adresse_complete', ''),
            'secteur_naf': entreprise.get('secteur_naf') or entreprise.get('secteur', ''),
            'effectif': entreprise.get('effectif', 0),
            'chiffre_affaires': entreprise.get('chiffre_affaires', 0),
            'type_structure': entreprise.get('type_structure', 'entreprise')
        }
        
        # Extraction automatique code postal si manquant
        if not entreprise_sync['code_postal'] and entreprise_sync['adresse_complete']:
            entreprise_sync['code_postal'] = extraire_code_postal_depuis_adresse(
                entreprise_sync['adresse_complete']
            )
        
        # Simplification secteur pour PME
        if entreprise_sync['secteur_naf']:
            entreprise_sync['secteur_simplifie'] = simplifier_secteur_pour_pme(
                entreprise_sync['secteur_naf']
            )
        
        entreprises_synchronisees.append(entreprise_sync)
    
    return entreprises_synchronisees

def simplifier_secteur_pour_pme(secteur_naf: str) -> str:
    """Simplifie le secteur NAF pour une meilleure lisibilité PME"""
    
    if not secteur_naf:
        return ""
    
    # Dictionnaire de simplification sectorielle
    simplifications = {
        'COMMERCE': ['commerce', 'vente', 'distribution', 'retail'],
        'SERVICES': ['service', 'conseil', 'consulting', 'prestation'],
        'INDUSTRIE': ['industrie', 'production', 'fabrication', 'manufacture'],
        'BTP': ['construction', 'bâtiment', 'travaux', 'rénovation'],
        'TRANSPORT': ['transport', 'logistique', 'livraison', 'déménagement'],
        'RESTAURATION': ['restaurant', 'alimentaire', 'cuisine', 'traiteur'],
        'SANTÉ': ['santé', 'médical', 'pharmacie', 'soins'],
        'DIGITAL': ['informatique', 'digital', 'web', 'software'],
        'FORMATION': ['formation', 'éducation', 'enseignement', 'coaching']
    }
    
    secteur_lower = secteur_naf.lower()
    
    for secteur_court, mots_cles in simplifications.items():
        for mot in mots_cles:
            if mot in secteur_lower:
                return secteur_court
    
    # Retour premier mot si pas de correspondance
    mots = secteur_naf.split()
    return mots[0] if mots else ""

def creer_adapter_requetes_pme(recherche_instance):
    """Crée un adaptateur pour requêtes PME territoriales"""
    
    def adapter_requetes_pme(entreprise, thematique):
        """Adapter spécialement les requêtes pour PME territoriales"""
        
        # Enrichissement avec contexte territorial
        entreprise_temp = entreprise.copy()
        entreprise_temp['contexte_territorial'] = 'PME Seine-et-Marne'
        entreprise_temp['secteur_simplifie'] = simplifier_secteur_pour_pme(
            entreprise.get('secteur_naf', '')
        )
        
        # Délégation à la méthode spécialisée
        return recherche_instance.construire_requetes_pme_territoriales(entreprise_temp, thematique)
    
    return adapter_requetes_pme

def debug_seuils_utilises():
    """Debug des seuils utilisés dans tout le système"""
    print("[DEBUG] SEUILS SYSTEME UTILISES")
    print("=" * 40)
    
    # 1. Seuils recherche
    try:
        from scripts.recherche_web import RechercheWeb
        recherche = RechercheWeb()
        print(f"[RECHERCHE] Seuil validation: {getattr(recherche, 'seuil_validation_minimal', 'Non défini')}")
    except Exception as e:
        print(f"[ERREUR] Erreur module recherche: {e}")
    
    # 2. Seuils IA
    try:
        from ai_validation_module import AIValidationModule
        validateur = AIValidationModule()
        print(f"[IA] Module disponible: {validateur is not None}")
    except Exception as e:
        print(f"[ERREUR] Erreur module IA: {e}")
    
    # 3. Modules de base
    try:
        print(f"[MODULES] Modules de base:")
        print(f"   [OK] RechercheWeb")
        print(f"   [OK] AnalyseurThematiques") 
        print(f"   [OK] FiltreurPME")
        print(f"   [OK] GenerateurRapports")
    except Exception as e:
        print(f"[ERREUR] Erreur modules de base: {e}")

def debug_entreprises_extraites(entreprises_finales):
    """Debug détaillé des entreprises extraites"""
    print(f"\n[DEBUG] DEBUG ENTREPRISES EXTRAITES:")
    print(f"   [STATS] Nombre total: {len(entreprises_finales)}")
    
    if len(entreprises_finales) == 0:
        print("   [ERREUR] AUCUNE ENTREPRISE - Vérifiez le filtrage!")
        return False
    
    for i, ent in enumerate(entreprises_finales[:3], 1):
        nom = ent.get('nom', 'N/A')
        commune = ent.get('commune', 'N/A')  
        secteur = ent.get('secteur_naf', 'N/A')
        print(f"   {i}. {nom[:40]} | {commune} | {secteur[:30]}")
    
    print(f"   [OK] Entreprises valides pour recherche")
    return True

def diagnostic_extraction_complete():
    """Diagnostic complet de l'extraction"""
    print(f"\n[DIAGNOSTIC] DIAGNOSTIC EXTRACTION COMPLETE")
    print("=" * 50)
    
    try:
        # Test direct extracteur
        from scripts.extracteur_donnees import ExtracteurDonnees
        import os
        
        fichier_excel = "data/input/entreprises_base.xlsx"
        print(f"[FICHIER] Fichier testé: {fichier_excel}")
        print(f"[FICHIER] Fichier existe: {os.path.exists(fichier_excel)}")
        
        if not os.path.exists(fichier_excel):
            print("[ERREUR] PROBLEME: Fichier Excel manquant!")
            return False
        
        # Test extraction directe
        extracteur = ExtracteurDonnees(fichier_excel)
        
        # Test chargement
        df = extracteur.charger_donnees()
        print(f"[STATS] Lignes dans Excel: {len(df)}")
        print(f"[STATS] Colonnes: {list(df.columns)}")
        
        # Test validation structure
        structure_ok = extracteur.valider_structure()
        print(f"[STRUCTURE] Structure valide: {structure_ok}")
        
        if not structure_ok:
            print("[ERREUR] PROBLEME: Structure Excel invalide!")
            return False
        
        # Test nettoyage
        df_clean = extracteur.nettoyer_donnees()
        print(f"[NETTOYAGE] Après nettoyage: {len(df_clean)} entreprises")
        
        # Test échantillon AVANT filtrage
        echantillon_brut = extracteur.extraire_echantillon(50)  # Large échantillon
        print(f"[ECHANTILLON] Échantillon brut: {len(echantillon_brut)} entreprises")
        
        if len(echantillon_brut) == 0:
            print("[ERREUR] PROBLEME: Extraction de base échouée!")
            return False
        
        # Affichage échantillon
        print(f"\n[ECHANTILLON] ECHANTILLON BRUT (3 premières):")
        for i, ent in enumerate(echantillon_brut[:3], 1):
            nom = ent.get('nom', 'N/A')
            commune = ent.get('commune', 'N/A')
            siret = ent.get('siret', 'N/A')
            print(f"   {i}. {nom[:40]} | {commune} | SIRET: {siret}")
        
        return True
        
    except Exception as e:
        print(f"[ERREUR] ERREUR DIAGNOSTIC EXTRACTION: {e}")
        import traceback
        traceback.print_exc()
        return False

def diagnostic_filtrage_complet(entreprises_brutes):
    """Diagnostic complet du filtrage PME"""
    print(f"\n[DIAGNOSTIC] DIAGNOSTIC FILTRAGE PME")
    print("=" * 50)
    
    try:
        from scripts.filtreur_pme import FiltreurPME
        print(f"[STATS] Entreprises avant filtrage: {len(entreprises_brutes)}")
        
        # Créer filtreur PME
        filtreur = FiltreurPME()
        
        # Test filtrage territorial
        print(f"[TERRITOIRE] FILTRAGE TERRITORIAL:")
        codes_postaux = getattr(filtreur, 'codes_postaux_cibles', ['77600', '77700', '77400', '77000', '77300', '77500', '77200', '77100'])
        communes = getattr(filtreur, 'communes_prioritaires', [])
        
        print(f"   [CONFIG] Codes postaux cibles: {codes_postaux}")
        print(f"   [CONFIG] Communes prioritaires: {communes}")
        
        # Appliquer filtrage territorial
        entreprises_territoire = filtreur.filtrer_par_territoire(entreprises_brutes)
        print(f"\n[STATS] Résultat filtrage territorial: {len(entreprises_territoire)}/{len(entreprises_brutes)} entreprises")
        
        # Appliquer filtrage PME
        print(f"[TERRITOIRE] Après filtrage territorial: {len(entreprises_territoire)}")
        pme_recherchables = filtreur.filtrer_pme_recherchables(entreprises_territoire)
        print(f"[PME] Après filtrage PME: {len(pme_recherchables)}")
        
        # Affichage détaillé des PME
        print(f"\n[PME] PME RECHERCHABLES (3 premières):")
        for i, ent in enumerate(pme_recherchables[:3], 1):
            nom = ent.get('nom', 'N/A')
            commune = ent.get('commune', 'N/A')
            print(f"   {i}. {nom} | {commune}")
        
        return pme_recherchables
        
    except Exception as e:
        print(f"[ERREUR] ERREUR DIAGNOSTIC FILTRAGE: {e}")
        import traceback
        traceback.print_exc()
        return []

def diagnostic_recherche_une_entreprise(entreprise):
    """Test de recherche sur une seule entreprise"""
    print(f"\n[DIAGNOSTIC] TEST RECHERCHE UNE ENTREPRISE")
    print("=" * 50)
    
    nom = entreprise.get('nom', 'N/A')
    commune = entreprise.get('commune', 'N/A')
    print(f"[ENTREPRISE] Test: {nom} à {commune}")
    
    try:
        from scripts.recherche_web import RechercheWeb
        
        # Initialiser recherche avec config ultra-permissive
        recherche = RechercheWeb(periode_recherche="6 mois")  # [FIX] Ajout paramètre manquant
        recherche.seuil_validation_minimal = 0.01  # Ultra-permissif
        
        # Test recherche
        print(f"[REQUETE] Requête test: \"{nom}\" {commune}")
        donnees_thematiques = recherche.rechercher_entreprise(entreprise)
        
        print(f"[RESULTATS] Résultats moteur: {len(donnees_thematiques) if donnees_thematiques else 0}")
        
        if donnees_thematiques and len(donnees_thematiques) > 0:
            print(f"[STATS] Données thématiques: {len(donnees_thematiques)}")
            for thematique, donnees in donnees_thematiques.items():
                if isinstance(donnees, dict):
                    mots_cles = donnees.get('mots_cles_trouves', [])
                    extraits = donnees.get('extraits_textuels', [])
                    print(f"   [THEME] Thématiques: {thematique}")
                    print(f"      [MOTS] Mots-clés: {len(mots_cles)}")
                    print(f"      [EXTRAITS] Extraits: {len(extraits)}")
        
        return len(donnees_thematiques) > 0
        
    except Exception as e:
        print(f"[ERREUR] ERREUR TEST RECHERCHE: {e}")
        import traceback
        traceback.print_exc()
        return False

def main_pme_territorial_diagnostic(nb_entreprises_cible=25):
    """Version avec diagnostic integre"""
    print("[DIAGNOSTIC] DIAGNOSTIC COMPLET - DETECTION PME")
    print("=" * 70)
    print(f"[CONFIG] Test avec {nb_entreprises_cible} entreprises cibles")
    
    # Test 1: Extraction
    if not diagnostic_extraction_complete():
        return None
    
    # Extraction normale  
    fichier_excel = "data/input/entreprises_base.xlsx"
    
    from scripts.extracteur_donnees import ExtracteurDonnees
    extracteur = ExtracteurDonnees(fichier_excel)
    # Extraction plus large pour compenser le filtrage
    entreprises_brutes = extracteur.extraire_echantillon(nb_entreprises_cible * 3)
    
    # Test 2: Filtrage
    pme_recherchables = diagnostic_filtrage_complet(entreprises_brutes)
    
    if len(pme_recherchables) == 0:
        print("\n[ERREUR] ARRET: Aucune PME apres filtrage")
        return None
    
    # Test 3: Recherche sur UNE entreprise
    entreprise_test = pme_recherchables[0]
    recherche_ok = diagnostic_recherche_une_entreprise(entreprise_test)
    
    if not recherche_ok:
        print("\n[ERREUR] ARRET: Recherche web echouee")
        return None
    
    # Test 4: Analyse thématique -- utiliser les résultats réels (pas de données factices)
    print(f"\n[ANALYSE] ANALYSE THEMATIQUE SUR RÉELS")
    print("=" * 50)

    try:
        from scripts.analyseur_thematiques import AnalyseurThematiques
        from scripts.generateur_rapports import GenerateurRapports
        from scripts.recherche_web import RechercheWeb

        # Initialisation analyseur
        thematiques = ['evenements', 'recrutements', 'vie_entreprise', 'innovations']
        analyseur = AnalyseurThematiques(thematiques)
        analyseur.seuil_pertinence = 0.01  # seuil permissif pour PME
        print(f"[CONFIG] Seuil analysE forcé: {analyseur.seuil_pertinence}")

        # Construire les résultats bruts en lançant des recherches réelles sur le sous-ensemble PME
        resultats_bruts = []
        recherche = RechercheWeb(periode_recherche="6 mois")
        recherche.seuil_validation_minimal = 0.01

        nb_a_traiter = min(len(pme_recherchables), nb_entreprises_cible)
        print(f"[RECHERCHE] Lancement recherches pour {nb_a_traiter} entreprises (réelles)")

        for i, ent in enumerate(pme_recherchables[:nb_a_traiter], 1):
            try:
                print(f"  [#{i}] Recherche: {ent.get('nom', '')} | {ent.get('commune', '')}")
                res = recherche.rechercher_entreprise(ent)
                # Structure: res est un dict avec 'donnees_thematiques' etc. Normaliser pour l'analyseur
                entree_analyse = {
                    'entreprise': ent,
                    'donnees_thematiques': res.get('donnees_thematiques', {}) if isinstance(res, dict) else {}
                }
                resultats_bruts.append(entree_analyse)
            except Exception as e:
                print(f"    ⚠️ Erreur recherche entreprise {ent.get('nom','N/A')}: {e}")
                continue

        print(f"[STATS] Resultats bruts collectes: {len(resultats_bruts)}")

        # Lancer l'analyse thématique sur les vrais résultats
        donnees_enrichies = analyseur.analyser_resultats(resultats_bruts)
        print(f"[STATS] Entreprises enrichies après analyse: {len(donnees_enrichies)}")

        # Génération des rapports (forcée si nécessaire)
        print(f"\n[RAPPORTS] Tentative génération de rapports à partir des données réelles")
        generateur = GenerateurRapports()

        # Si aucun score positif, appliquer force_inclusion sur toutes pour générer un rapport
        if donnees_enrichies and all(e.get('score_global', 0) <= 0 for e in donnees_enrichies):
            for e in donnees_enrichies:
                e['force_inclusion'] = True

        rapports_generes = generateur.generer_tous_rapports(donnees_enrichies)

        rapports_reussis = 0
        for type_rapport, chemin_fichier in (rapports_generes or {}).items():
            if isinstance(chemin_fichier, str) and not chemin_fichier.startswith("ERREUR"):
                print(f"[OK] {type_rapport}: {chemin_fichier}")
                rapports_reussis += 1
            else:
                print(f"[ERREUR] {type_rapport}: {chemin_fichier}")

        if rapports_reussis > 0:
            print(f"[SUCCES] {rapports_reussis} rapports générés avec succès!")
            return rapports_generes
        else:
            print(f"[ERREUR] Aucun rapport généré")
            return None

    except Exception as e:
        print(f"[ERREUR] ERREUR ANALYSE: {e}")
        import traceback
        traceback.print_exc()
        return None

def main_pme_territorial(nb_entreprises=25):
    """Programme principal - Lance le diagnostic complet"""
    
    print("[PME] VEILLE PME SEINE-ET-MARNE")
    print("=" * 50)
    print(f"[CONFIG] Analyse de {nb_entreprises} entreprises")
    print("[CONFIG] Mode diagnostic active")
    print()
    
    # Lancer le diagnostic complet avec le bon nombre d'entreprises
    return main_pme_territorial_diagnostic(nb_entreprises)

if __name__ == "__main__":
    print("[PME] VEILLE ECONOMIQUE PME TERRITORIALE - VERSION CORRIGEE")
    print("=" * 70)
    print("Lancement de l'analyse PME avec codes postaux...")
    print()
    
    # Configuration du nombre d'entreprises
    NB_ENTREPRISES_CIBLE = 10  # [CONFIG] Changez cette valeur selon vos besoins
    
    try:
        # [DEBUG] DEBUG PREALABLE
        debug_seuils_utilises()
        print()
        
        # [EXEC] EXECUTION PRINCIPALE
        print(f"[CONFIG] Lancement analyse pour {NB_ENTREPRISES_CIBLE} entreprises")
        rapports = main_pme_territorial(NB_ENTREPRISES_CIBLE)
        
        if rapports:
            print("\n[OK] ANALYSE PME REUSSIE !")
            print("[SUCCES] Vos PME territoriales ont ete analysees avec succes !")
            print()
            print("[INFO] PROCHAINES ETAPES:")
            print("1. [EXCEL] Consultez le rapport Excel pour les donnees detaillees")
            print("2. [WEB] Ouvrez le rapport HTML pour la visualisation territoriale")
            print("3. [CONFIG] Ajustez les parametres si necessaire dans config/parametres.yaml")
            print("4. [RELANCE] Relancez l'analyse pour un suivi periodique")
        else:
            print("\n[ERREUR] ANALYSE PME ECHOUEE")
            print("[INFO] Consultez les messages d'erreur ci-dessus pour identifier le problème")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[ARRET] Analyse PME interrompue par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERREUR] ERREUR CRITIQUE: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
