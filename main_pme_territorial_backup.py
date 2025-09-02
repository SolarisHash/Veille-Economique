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


def debug_entreprises_extraites(entreprises_finales):
    """✅ NOUVEAU: Debug détaillé des entreprises extraites"""
    print(f"\n🔍 DEBUG ENTREPRISES EXTRAITES:")
    print(f"   📊 Nombre total: {len(entreprises_finales)}")
    
    if len(entreprises_finales) == 0:
        print("   ❌ AUCUNE ENTREPRISE - Vérifiez le filtrage!")
        return False
    
    for i, ent in enumerate(entreprises_finales[:3], 1):
        nom = ent.get('nom', 'N/A')
        commune = ent.get('commune', 'N/A')  
        secteur = ent.get('secteur_naf', 'N/A')
        print(f"   {i}. {nom[:40]} | {commune} | {secteur[:30]}")
    
    print(f"   ✅ Entreprises valides pour recherche")
    return True


def diagnostic_extraction_complete():
    """Diagnostic complet de l'extraction"""
    print(f"\n🔍 DIAGNOSTIC EXTRACTION COMPLÈTE")
    print("=" * 50)
    
    try:
        # Test direct extracteur
        from scripts.extracteur_donnees import ExtracteurDonnees
        import os
        
        fichier_excel = "data/input/entreprises_base.xlsx"
        print(f"📂 Fichier testé: {fichier_excel}")
        print(f"📂 Fichier existe: {os.path.exists(fichier_excel)}")
        
        if not os.path.exists(fichier_excel):
            print("❌ PROBLÈME: Fichier Excel manquant!")
            return False
        
        # Test extraction directe
        extracteur = ExtracteurDonnees(fichier_excel)
        
        # Test chargement
        df = extracteur.charger_donnees()
        print(f"📊 Lignes dans Excel: {len(df)}")
        print(f"📊 Colonnes: {list(df.columns)}")
        
        # Test validation structure
        structure_ok = extracteur.valider_structure()
        print(f"📋 Structure valide: {structure_ok}")
        
        if not structure_ok:
            print("❌ PROBLÈME: Structure Excel invalide!")
            return False
        
        # Test nettoyage
        df_clean = extracteur.nettoyer_donnees()
        print(f"🧹 Après nettoyage: {len(df_clean)} entreprises")
        
        # Test échantillon AVANT filtrage
        echantillon_brut = extracteur.extraire_echantillon(50)  # Large échantillon
        print(f"📥 Échantillon brut: {len(echantillon_brut)} entreprises")
        
        if len(echantillon_brut) == 0:
            print("❌ PROBLÈME: Extraction de base échouée!")
            return False
        
        # Affichage échantillon
        print(f"\n📋 ÉCHANTILLON BRUT (3 premières):")
        for i, ent in enumerate(echantillon_brut[:3], 1):
            nom = ent.get('nom', 'N/A')
            commune = ent.get('commune', 'N/A')
            siret = ent.get('siret', 'N/A')
            print(f"   {i}. {nom[:40]} | {commune} | SIRET: {siret}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR DIAGNOSTIC EXTRACTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def diagnostic_filtrage_complet(entreprises_brutes):
    """Diagnostic complet du filtrage PME"""
    print(f"\n🔍 DIAGNOSTIC FILTRAGE PME")
    print("=" * 50)
    
    try:
        from scripts.filtreur_pme import FiltreurPME
        
        print(f"📊 Entreprises avant filtrage: {len(entreprises_brutes)}")
        
        # Test filtrage par territoire
        filtreur = FiltreurPME()
        entreprises_territoire = filtreur.filtrer_par_territoire(entreprises_brutes)
        print(f"🌍 Après filtrage territorial: {len(entreprises_territoire)}")
        
        if len(entreprises_territoire) == 0:
            print("❌ PROBLÈME: Filtrage territorial élimine tout!")
            print("🔧 Solution: Vérifiez codes postaux dans parametres.yaml")
            
            # Debug territoire
            print("\n🔍 DEBUG TERRITOIRE:")
            for i, ent in enumerate(entreprises_brutes[:5], 1):
                adresse = ent.get('adresse_complete', '')
                commune = ent.get('commune', '')
                print(f"   {i}. {commune} | Adresse: {adresse[:50]}...")
            
            return []
        
        # Test filtrage PME recherchables  
        pme_recherchables = filtreur.filtrer_pme_recherchables(entreprises_territoire)
        print(f"🏢 Après filtrage PME: {len(pme_recherchables)}")
        
        if len(pme_recherchables) == 0:
            print("❌ PROBLÈME: Filtrage PME élimine tout!")
            print("🔧 Solution: Critères PME trop stricts")
            
            # Debug critères PME
            print("\n🔍 DEBUG CRITÈRES PME:")
            for i, ent in enumerate(entreprises_territoire[:5], 1):
                nom = ent.get('nom', '')
                print(f"   {i}. {nom}")
            
            return []
        
        print(f"\n📋 PME RECHERCHABLES (3 premières):")
        for i, ent in enumerate(pme_recherchables[:3], 1):
            nom = ent.get('nom', 'N/A')
            commune = ent.get('commune', 'N/A')
            print(f"   {i}. {nom[:40]} | {commune}")
        
        return pme_recherchables
        
    except Exception as e:
        print(f"❌ ERREUR DIAGNOSTIC FILTRAGE: {e}")
        import traceback
        traceback.print_exc()
        return []


def diagnostic_recherche_une_entreprise(entreprise):
    """Test de recherche sur UNE seule entreprise"""
    print(f"\n🔍 TEST RECHERCHE UNE ENTREPRISE")
    print("=" * 50)
    
    nom = entreprise.get('nom', '')
    commune = entreprise.get('commune', '')
    
    print(f"🏢 Test: {nom} à {commune}")
    
    try:
        from scripts.recherche_web import RechercheWeb
        from datetime import timedelta
        
        recherche = RechercheWeb(timedelta(days=180))
        
        # Test une requête basique
        requete_test = f'"{nom}" {commune}'
        print(f"🔍 Requête test: {requete_test}")
        
        # Test moteur de recherche direct
        resultats_moteur = recherche._rechercher_moteur(requete_test)
        print(f"🌐 Résultats moteur: {len(resultats_moteur) if resultats_moteur else 0}")
        
        if resultats_moteur:
            print("   📄 Premier résultat:")
            premier = resultats_moteur[0]
            print(f"      Titre: {premier.get('titre', '')[:50]}...")
            print(f"      URL: {premier.get('url', '')}")
        
        # Test recherche complète
        resultats_complets = recherche.rechercher_entreprise(entreprise)
        donnees_thematiques = resultats_complets.get('donnees_thematiques', {})
        
        print(f"📊 Données thématiques: {len(donnees_thematiques)}")
        if donnees_thematiques:
            print(f"   🎯 Thématiques: {list(donnees_thematiques.keys())}")
            
            # Détail première thématique
            premiere_theme = list(donnees_thematiques.keys())[0]
            premiere_donnee = donnees_thematiques[premiere_theme]
            print(f"   📋 Détail {premiere_theme}: {type(premiere_donnee)}")
            
            if isinstance(premiere_donnee, dict):
                extraits = premiere_donnee.get('extraits_textuels', [])
                print(f"      📄 Extraits: {len(extraits)}")
        
        return len(donnees_thematiques) > 0
        
    except Exception as e:
        print(f"❌ ERREUR TEST RECHERCHE: {e}")
        import traceback
        traceback.print_exc()
        return False


def main_pme_territorial_diagnostic():
    """Version avec diagnostic integre"""
    print("[DIAGNOSTIC] DIAGNOSTIC COMPLET - DETECTION PME")
    print("=" * 70)
    
    # Test 1: Extraction
    if not diagnostic_extraction_complete():
        return None
    
    # Extraction normale  
    fichier_excel = "data/input/entreprises_base.xlsx"
    nb_entreprises = 5  # [OK] REDUIT pour diagnostic
    
    from scripts.extracteur_donnees import ExtracteurDonnees
    extracteur = ExtracteurDonnees(fichier_excel)
    entreprises_brutes = extracteur.extraire_echantillon(nb_entreprises * 3)
    
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
    
    # Test 4: Analyse thematique
    print(f"\n[ANALYSE] TEST ANALYSE THEMATIQUE")
    print("=" * 50)
    
    try:
        from scripts.analyseur_thematiques import AnalyseurThematiques
        
        # Forcer seuils ultra-permissifs
        thematiques = ['evenements', 'recrutements', 'vie_entreprise', 'innovations']
        analyseur = AnalyseurThematiques(thematiques)
        
        # ✅ FORCER seuil ultra-bas
        analyseur.seuil_pertinence = 0.01  # ULTRA-ULTRA-BAS
        print(f"🔧 Seuil forcé: {analyseur.seuil_pertinence}")
        
        # Test sur données factices
        resultats_test = [{
            'entreprise': entreprise_test,
            'donnees_thematiques': {
                'recrutements': {
                    'mots_cles_trouves': ['test'],
                    'extraits_textuels': [{'titre': 'Test', 'description': 'Test'}],
                    'pertinence': 0.5
                }
            }
        }]
        
        donnees_enrichies = analyseur.analyser_resultats(resultats_test)
        
        print(f"📊 Entreprises enrichies: {len(donnees_enrichies)}")
        if donnees_enrichies:
            entreprise_enrichie = donnees_enrichies[0]
            score_global = entreprise_enrichie.get('score_global', 0)
            thematiques_principales = entreprise_enrichie.get('thematiques_principales', [])
            
            print(f"   🏆 Score global: {score_global}")
            print(f"   🎯 Thématiques: {thematiques_principales}")
            
            if score_global > 0:
                print("✅ ANALYSE THÉMATIQUE FONCTIONNE")
            else:
                print("❌ PROBLÈME: Score global = 0")
        
    except Exception as e:
        print(f"❌ ERREUR ANALYSE: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎯 DIAGNOSTIC TERMINÉ")
    print("Consultez les messages ci-dessus pour identifier le problème exact")
    
    return None


def main_pme_territorial():
    """Programme principal - Lance le diagnostic complet"""
    
    print("� VEILLE PME SEINE-ET-MARNE")
    print("=" * 50)
    print("🔧 Mode diagnostic activé")
    print()
    
    # Lancer le diagnostic complet
    return main_pme_territorial_diagnostic()


if __name__ == "__main__":
    
    # ✅ VALIDATION PRÉALABLE
    if not valider_configuration_pme():
        print("❌ Configuration invalide - arrêt du traitement")
        return None
    
    # Configuration
    fichier_excel = "data/input/entreprises_base.xlsx"
    nb_entreprises = 5
    
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
        
        # DEBUG TEMPORAIRE
        print(f"🔍 DEBUG: {len(entreprises_finales)} entreprises extraites")
        for i, ent in enumerate(entreprises_finales[:3]):
            print(f"  {i+1}. {ent.get('nom', 'N/A')} - {ent.get('commune', 'N/A')}")
        
        # ✅ AJOUT DEBUG CRITIQUE
        if not debug_entreprises_extraites(entreprises_finales):
            print("❌ ARRÊT: Aucune entreprise à analyser")
            return None
        
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
        entreprises_avec_donnees = 0  # ✅ Compteur debug
        
        for i, entreprise in enumerate(entreprises_finales, 1):
            nom_entreprise = logger.log_entreprise_debut(entreprise)
            print(f"  🏢 {i}/{len(entreprises_finales)}: {nom_entreprise} ({entreprise.get('commune', 'N/A')})")
            
            try:
                # ✅ RECHERCHE avec fallback forcé
                resultats = recherche.rechercher_entreprise(entreprise, logger=logger)
                
                # ✅ DEBUG CRITIQUE
                nb_thematiques = len(resultats.get('donnees_thematiques', {}))
                print(f"     📊 Résultat: {nb_thematiques} thématiques trouvées")
                
                if nb_thematiques > 0:
                    entreprises_avec_donnees += 1
                    print(f"     ✅ DONNÉES TROUVÉES: {list(resultats.get('donnees_thematiques', {}).keys())}")
                else:
                    print(f"     ⚠️ AUCUNE DONNÉE - FORCER un résultat minimum")
                    # ✅ FORCER au minimum 1 résultat
                    resultats['donnees_thematiques'] = recherche._forcer_resultats_minimum_pme(entreprise)
                    entreprises_avec_donnees += 1
                
                resultats_bruts.append(resultats)
                logger.log_extraction_resultats(nom_entreprise, True)
                
            except Exception as e:
                logger.log_extraction_resultats(nom_entreprise, False, str(e))
                print(f"     ❌ Erreur: {str(e)}")
                
                # ✅ FORCER un résultat même en cas d'erreur
                resultat_erreur = {
                    'entreprise': entreprise,
                    'donnees_thematiques': recherche._forcer_resultats_minimum_pme(entreprise),
                    'erreurs': [str(e)]
                }
                resultats_bruts.append(resultat_erreur)
                entreprises_avec_donnees += 1
                continue
        
        # ✅ AJOUT DEBUG FINAL RECHERCHE
        print(f"\n📊 RÉSUMÉ RECHERCHE:")
        print(f"   🏢 Entreprises traitées: {len(resultats_bruts)}")
        print(f"   ✅ Avec données: {entreprises_avec_donnees}")
        print(f"   📈 Taux de succès: {(entreprises_avec_donnees/len(resultats_bruts)*100):.1f}%")
        
        if entreprises_avec_donnees == 0:
            print("❌ ERREUR CRITIQUE: Aucune donnée trouvée pour aucune entreprise")
            print("🔧 Vérifiez les seuils de validation dans analyseur_thematiques.py")
            return None
        
        print(f"\n✅ Recherche terminée pour {len(resultats_bruts)} entreprises")

        # Correction de qualité des données avant analyse
        fixer = DataQualityFixer()
        for resultat in resultats_bruts:
            entreprise_r = resultat.get('entreprise', {})
            donnees_thematiques = resultat.get('donnees_thematiques', {})
            if donnees_thematiques:
                resultat['donnees_thematiques'] = fixer.corriger_donnees_thematiques(
                    entreprise_r,
                    donnees_thematiques
                )
        
        # ✅ ÉTAPE 3: Analyse avec seuils PME + VALIDATION IA
        print(f"\n🔬 ÉTAPE 3/5 - ANALYSE THÉMATIQUE PME + VALIDATION IA")
        print("-" * 50)
        
        thematiques = ['recrutements', 'evenements', 'innovations', 'vie_entreprise']
        analyseur = AnalyseurThematiques(thematiques)
        
        # ✅ FORCER seuils ultra-permissifs
        analyseur.seuil_pertinence = 0.05  # ✅ ULTRA-BAS
        print(f"🔧 Seuils PME ultra-permissifs: pertinence = {analyseur.seuil_pertinence}")
        
        # ✅ VALIDATION IA AVANT L'ANALYSE
        print("🤖 Activation de la validation IA anti-faux positifs...")
        
        try:
            from ai_validation_module import AIValidationModule
            ai_validator = AIValidationModule()
            
            resultats_valides_ia = []
            total_faux_positifs = 0
            
            for resultat in resultats_bruts:
                entreprise = resultat.get('entreprise', {})
                donnees_thematiques = resultat.get('donnees_thematiques', {})
                
                if donnees_thematiques:
                    nom = entreprise.get('nom', 'N/A')
                    print(f"🔍 Validation IA: {nom}")
                    
                    # ✅ VALIDATION IA DES RÉSULTATS
                    donnees_validees = ai_validator.batch_validate_results(
                        entreprise, 
                        donnees_thematiques
                    )
                    
                    # Comptage faux positifs éliminés
                    nb_avant = sum(len(data.get('extraits_textuels', [])) for data in donnees_thematiques.values() if isinstance(data, dict))
                    nb_apres = sum(len(data) for data in donnees_validees.values())
                    total_faux_positifs += (nb_avant - nb_apres)
                    
                    # Mise à jour avec données validées
                    resultat_valide = resultat.copy()
                    resultat_valide['donnees_thematiques'] = donnees_validees
                    resultat_valide['validation_ia_appliquee'] = True
                    resultats_valides_ia.append(resultat_valide)
                else:
                    resultats_valides_ia.append(resultat)
            
            print(f"✅ Validation IA terminée: {total_faux_positifs} faux positifs éliminés")
            
            # Utiliser les résultats validés par l'IA
            resultats_bruts = resultats_valides_ia
            
        except Exception as e:
            print(f"❌ Erreur validation IA: {e}")
            print("➡️ Analyse sans validation IA")
        
        # ✅ ADAPTATION SEUILS POUR PME
        analyseur.seuil_pertinence = 0.15  # TRÈS permissif pour PME
        print(f"🔧 Seuils PME ultra-permissifs: pertinence = {analyseur.seuil_pertinence}")
        
        # ✅ ANALYSE AVEC DONNÉES VALIDÉES
        donnees_enrichies = analyseur.analyser_resultats(resultats_bruts, logger=logger)
        
        # ✅ Statistiques PME avec seuils adaptés
        entreprises_actives = [e for e in donnees_enrichies if e.get('score_global', 0) > 0.05]  # ✅ ULTRA-BAS
        entreprises_tres_actives = [e for e in donnees_enrichies if e.get('score_global', 0) > 0.2]  # ✅ BAS
        
        print(f"✅ Analyse PME terminée (seuils adaptés):")
        print(f"   📊 Entreprises analysées: {len(donnees_enrichies)}")
        print(f"   🎯 PME actives (>0.05): {len(entreprises_actives)}")  # ✅ SEUIL ADAPTÉ
        print(f"   🏆 PME très actives (>0.2): {len(entreprises_tres_actives)}")  # ✅ SEUIL ADAPTÉ
        
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
    print("[PME] VEILLE ECONOMIQUE PME TERRITORIALE - VERSION CORRIGEE")
    print("=" * 70)
    print("Lancement de l'analyse PME avec codes postaux...")
    print()
    
    try:
        # [OK] DEBUG PREALABLE
        debug_seuils_utilises()
        print()
        
        # [OK] EXECUTION PRINCIPALE
        rapports = main_pme_territorial()
        
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