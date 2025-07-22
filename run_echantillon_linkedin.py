#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse complète avec intégration LinkedIn
Version enrichie pour veille économique
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from main import VeilleEconomique

def main():
    print("🔗 VEILLE ÉCONOMIQUE + LINKEDIN")
    print("=" * 50)
    
    veille = VeilleEconomique()
    fichier_excel = "data/input/entreprises_base.xlsx"
    
    if not Path(fichier_excel).exists():
        print(f"❌ Fichier manquant: {fichier_excel}")
        return False
    
    print("🎯 PROCESSUS D'ANALYSE ENRICHI:")
    print("1. Extraction et analyse classique")
    print("2. Recherche profils LinkedIn")
    print("3. Génération script Tampermonkey")
    print("4. Collecte manuelle posts LinkedIn") 
    print("5. Enrichissement des rapports")
    print()
    
    try:
        # Lancement du processus enrichi
        rapports = veille.traiter_echantillon_avec_linkedin(
            fichier_excel, 
            nb_entreprises=10
        )
        
        if rapports:
            print("\n🎉 ANALYSE COMPLÈTE TERMINÉE !")
            print("\n📊 RAPPORTS GÉNÉRÉS:")
            for type_rapport, chemin in rapports.items():
                print(f"   📄 {type_rapport}: {chemin}")
            
            print("\n💡 NOUVEAUTÉS LINKEDIN:")
            print("   • Section LinkedIn dans les rapports Excel")
            print("   • Posts récents analysés par thématique")
            print("   • Enrichissement du scoring global")
            print("   • Identification des entreprises actives sur LinkedIn")
            
            return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Mission accomplie ! 🎯")
    else:
        print("\n❌ Échec de la mission")
        sys.exit(1)