#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test avec des entreprises réelles pour validation
"""

import pandas as pd
from pathlib import Path

def creer_fichier_test():
    """Création d'un fichier de test avec entreprises réelles"""
    
    # Entreprises réelles pour test
    entreprises_test = [
        {
            'SIRET': '12345678901234',
            'Nom courant/Dénomination': 'Carrefour',
            'Commune': 'Paris',
            'Secteur_NAF': 'Commerce de détail',
            'Site_Web': 'https://www.carrefour.fr'
        },
        {
            'SIRET': '23456789012345', 
            'Nom courant/Dénomination': 'SNCF',
            'Commune': 'Lyon',
            'Secteur_NAF': 'Transport ferroviaire',
            'Site_Web': 'https://www.sncf.com'
        },
        {
            'SIRET': '34567890123456',
            'Nom courant/Dénomination': 'Michelin',
            'Commune': 'Clermont-Ferrand', 
            'Secteur_NAF': 'Fabrication de pneumatiques',
            'Site_Web': 'https://www.michelin.fr'
        },
        {
            'SIRET': '45678901234567',
            'Nom courant/Dénomination': 'Orange',
            'Commune': 'Marseille',
            'Secteur_NAF': 'Télécommunications',
            'Site_Web': 'https://www.orange.fr'
        },
        {
            'SIRET': '56789012345678',
            'Nom courant/Dénomination': 'Airbus',
            'Commune': 'Toulouse',
            'Secteur_NAF': 'Construction aéronautique',
            'Site_Web': 'https://www.airbus.com'
        }
    ]
    
    # Ajout des colonnes manquantes
    for entreprise in entreprises_test:
        entreprise.update({
            'Enseigne': '',
            'Adresse - complément dʼadresse': '',
            'Adresse - numéro et voie': '',
            'Adresse - distribution postale': '',
            'Adresse - CP et commune': f"75000 {entreprise['Commune'].upper()}",
            'Code NAF': '4711F',
            'Libellé NAF': entreprise['Secteur_NAF'],
            'Genre': 'Société',
            'Nom': 'Directeur',
            'Prénom': 'Le',
            'Site Web établissement': entreprise['Site_Web']
        })
    
    # Création du DataFrame
    df = pd.DataFrame(entreprises_test)
    
    # Sauvegarde
    Path("data/input").mkdir(parents=True, exist_ok=True)
    fichier_test = "data/input/entreprises_test.xlsx"
    df.to_excel(fichier_test, index=False)
    
    print(f"✅ Fichier de test créé: {fichier_test}")
    print(f"📊 {len(entreprises_test)} entreprises réelles")
    print("\n🚀 Lancez maintenant:")
    print("   python scripts/main.py")
    print("   (modifiez main.py pour utiliser entreprises_test.xlsx)")
    
    return fichier_test

if __name__ == "__main__":
    creer_fichier_test()