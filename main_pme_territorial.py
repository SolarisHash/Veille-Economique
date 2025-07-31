from datetime import timedelta
from typing import List, Dict
import pandas as pd
import yaml


from scripts.analyseur_thematiques import AnalyseurThematiques
from scripts.extracteur_donnees import ExtracteurDonnees
from scripts.filtreur_pme import FiltreurPME
from scripts.generateur_rapports import GenerateurRapports
from scripts.recherche_web import RechercheWeb


def debug_seuils_utilises():
    """Debug pour identifier tous les seuils utilisés"""
    print("🔍 SEUILS DE CONFIANCE UTILISÉS:")
    
    # 1. Configuration YAML
    try:
        with open("config/parametres.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        print(f"📋 Config YAML:")
        print(f"   score_entreprise_minimum: {config.get('validation', {}).get('score_entreprise_minimum', 'N/A')}")
        print(f"   validation_minimum: {config.get('seuils_pme', {}).get('validation_minimum', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur lecture config: {e}")
    
    # 2. Module IA
    try:
        from ai_validation_module import AIValidationModule
        ai_module = AIValidationModule()
        print(f"🤖 Module IA initialisé")
    except Exception as e:
        print(f"❌ Erreur module IA: {e}")
    
    # 3. Recherche Web
    try:
        from scripts.recherche_web import RechercheWeb
        from datetime import timedelta
        recherche = RechercheWeb(timedelta(days=180))
        print(f"🔍 Module recherche initialisé")
    except Exception as e:
        print(f"❌ Erreur recherche web: {e}")


def nettoyer_donnee_texte(valeur):
    """Nettoyage sécurisé des données textuelles"""
    if pd.isna(valeur) or not isinstance(valeur, str):
        return ""
    return str(valeur).lower().strip()


def main_pme_territorial():
    """Version adaptée PME avec codes postaux"""

    print("🎯 VEILLE ÉCONOMIQUE PME - TERRITOIRE SPÉCIFIQUE")
    print("=" * 70)
    
    fichier_excel = "data/input/entreprises_base.xlsx"
    nb_entreprises = 100
    
    try:
        # 1. ✅ Extraction avec filtrage PME territorial
        extracteur = ExtracteurDonnees(fichier_excel)
        toutes_entreprises = extracteur.extraire_echantillon(nb_entreprises * 3)  # Plus large
        
        # 2. ✅ NOUVEAU : Filtrage territorial
        filtreur = FiltreurPME()
        entreprises_territoire = filtreur.filtrer_par_territoire(toutes_entreprises)
        
        if len(entreprises_territoire) == 0:
            print("❌ AUCUNE ENTREPRISE dans votre territoire !")
            print("Vérifiez vos codes postaux dans config/parametres.yaml")
            return
        
        # 3. ✅ NOUVEAU : Filtrage PME recherchables
        pme_recherchables = filtreur.filtrer_pme_recherchables(entreprises_territoire)
        
        # Limitation au nombre final souhaité
        entreprises_finales = pme_recherchables[:nb_entreprises]
        
        print(f"\n📊 SÉLECTION FINALE:")
        print(f"   🌍 Territoire: {len(entreprises_territoire)} entreprises")
        print(f"   🏢 PME recherchables: {len(pme_recherchables)}")
        print(f"   🎯 Échantillon final: {len(entreprises_finales)}")
        
        # 4. ✅ Recherche web adaptée PME
        recherche = RechercheWeb(timedelta(days=180))
        
        # Remplacer la méthode de construction de requêtes
        recherche.construire_requetes_intelligentes = recherche.construire_requetes_pme_territoriales
        
        resultats_bruts = []
        for entreprise in entreprises_finales:
            resultats = recherche.rechercher_entreprise(entreprise)
            resultats_bruts.append(resultats)
        
        # 5. ✅ Analyse avec seuils PME
        analyseur = AnalyseurThematiques(['recrutements', 'evenements', 'innovations', 'vie_entreprise'])
        
        # Adaptation seuils pour PME
        analyseur.seuil_pertinence = 0.25  # Plus permissif
        
        donnees_enrichies = analyseur.analyser_resultats(resultats_bruts)
        
        # 6. ✅ Rapports
        generateur = GenerateurRapports()
        rapports = generateur.generer_tous_rapports(donnees_enrichies)
        
        print(f"\n🎉 ANALYSE PME TERRITORIALE TERMINÉE !")
        print(f"📊 Consultez vos rapports dans data/output/")
        
        return rapports
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    print("🏢 MODIFICATION PME + CODES POSTAUX")
    print("Instructions d'implémentation:")
    print()
    print("1️⃣ Créez/modifiez config/parametres.yaml avec vos codes postaux")
    print("2️⃣ Ajoutez FiltreurPME dans extracteur_donnees.py") 
    print("3️⃣ Modifiez recherche_web.py avec requêtes PME territoriales")
    print("4️⃣ Adaptez les seuils dans ai_validation_module.py (0.7 → 0.3)")
    print("5️⃣ Testez avec main_pme_territorial()")

    debug_seuils_utilises()
    main_pme_territorial()