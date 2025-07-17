#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de lancement rapide pour test échantillon
Usage: python run_echantillon.py
"""

import os
import sys
from pathlib import Path

# Ajout du dossier scripts au path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from main import VeilleEconomique

def main():
    """Lancement rapide du test échantillon"""
    print("🚀 LANCEMENT RAPIDE - TEST ÉCHANTILLON")
    print("=" * 50)
    
    # Configuration
    fichier_excel = "data/input/entreprises_base.xlsx"
    nb_entreprises = 10
    
    # Vérifications préalables
    if not os.path.exists(fichier_excel):
        print(f"❌ ERREUR: Fichier manquant")
        print(f"📁 Veuillez placer votre fichier Excel dans: {fichier_excel}")
        print("💡 Le fichier doit contenir les colonnes requises:")
        print("   - SIRET, Nom courant/Dénomination, Commune, etc.")
        return False
        
    # Création des dossiers si nécessaire
    Path("data/input").mkdir(parents=True, exist_ok=True)
    Path("data/output").mkdir(parents=True, exist_ok=True)
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)
    
    try:
        # Lancement de l'analyse
        print(f"🔍 Analyse de {nb_entreprises} entreprises...")
        print(f"📊 Fichier source: {fichier_excel}")
        print()
        
        veille = VeilleEconomique()
        resultat = veille.traiter_echantillon(fichier_excel, nb_entreprises)
        
        print()
        print("🎯 ANALYSE TERMINÉE AVEC SUCCÈS!")
        print(f"📄 Rapport généré: {resultat}")
        print()
        print("📋 Prochaines étapes:")
        print("1. Vérifiez le fichier Excel de résultats")
        print("2. Validez la pertinence des informations")
        print("3. Ajustez les paramètres si nécessaire")
        print("4. Lancez l'analyse complète sur toutes les entreprises")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        print()
        print("🔧 Solutions possibles:")
        print("1. Vérifiez le format du fichier Excel")
        print("2. Assurez-vous que les colonnes requises sont présentes")
        print("3. Vérifiez votre connexion internet")
        print("4. Consultez les logs pour plus de détails")
        
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ Test terminé avec succès!")
    else:
        print("\n❌ Test échoué - consultez les messages d'erreur ci-dessus")
        sys.exit(1)