#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour analyser les données réelles (noms anonymisés)
"""

import os
import sys
import shutil
from pathlib import Path

# Ajout du dossier scripts au path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from main import VeilleEconomique

def main():
    """Lancement avec données réelles anonymisées"""
    print("🏢 ANALYSE AVEC DONNÉES RÉELLES ANONYMISÉES")
    print("=" * 60)
    
    # ✅ UTILISATION DE VOS VRAIES DONNÉES
    fichier_excel = "data/input/entreprises_base.xlsx"
    nb_entreprises = 20
    
    # Vérifications préalables
    if not os.path.exists(fichier_excel):
        print(f"❌ ERREUR: Fichier manquant")
        print(f"📁 Veuillez placer votre fichier Excel dans: {fichier_excel}")
        return False
    
    print(f"✅ Fichier trouvé: {fichier_excel}")
    print(f"🎯 Analyse de {nb_entreprises} entreprises réelles (noms anonymisés)")
    print("🔍 Stratégie: Recherche par COMMUNE + SECTEUR NAF")
    
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
    
    try:
        print(f"\n🚀 Démarrage analyse...")
        print("⚠️  Les recherches vont prendre du temps (vraies recherches par secteur)")
        print()
        
        veille = VeilleEconomique()
        resultats = veille.traiter_echantillon(fichier_excel, nb_entreprises)
        
        print()
        print("🎯 ANALYSE TERMINÉE!")
        
        if isinstance(resultats, dict):
            print("📂 Rapports générés:")
            for type_rapport, chemin in resultats.items():
                if not chemin.startswith("ERREUR"):
                    print(f"   📄 {type_rapport}: {chemin}")
        else:
            print(f"📄 Rapport Excel: {resultats}")
        
        print()
        print("🔍 MAINTENANT VÉRIFIEZ:")
        print("1. 📊 Les entreprises sont recherchées par COMMUNE + SECTEUR")
        print("2. 🎯 Les thématiques correspondent aux secteurs NAF")
        print("3. 🔗 Les résultats mentionnent vos communes réelles")
        print("4. 📈 Les scores sont réalistes (0.3-0.7)")
        print("5. 📋 Le contenu est pertinent pour chaque secteur")
        
        print()
        print("💡 EXEMPLES DE RECHERCHES EFFECTUÉES:")
        print("   - 'Bussy-Saint-Georges transport voyageurs recrutement'")
        print("   - 'Jossigny santé humaine événement'")
        print("   - 'Chalifert services personnels entreprise'")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        print()
        print("🔧 Solutions possibles:")
        print("1. Vérifiez votre connexion internet")
        print("2. Essayez avec moins d'entreprises")
        print("3. Consultez les logs pour plus de détails")
        
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ Analyse réussie avec données réelles!")
        print("🎉 Vos entreprises anonymisées ont été analysées par secteur!")
    else:
        print("\n❌ Analyse échouée - consultez les erreurs ci-dessus")
        sys.exit(1)