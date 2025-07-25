#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de comparaison entre micro-entreprises et vraies entreprises
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, "scripts")

def comparer_resultats():
    """Comparaison des deux approches"""
    print("🔬 COMPARAISON MICRO-ENTREPRISES VS VRAIES ENTREPRISES")
    print("=" * 70)
    
    # Test 1: Micro-entreprises (votre fichier actuel)
    print("\n1️⃣ TEST AVEC MICRO-ENTREPRISES")
    print("-" * 40)
    print("📁 Fichier: entreprises_base.xlsx")
    print("🏢 Type: Personnes physiques, micro-entreprises")
    print("🔍 Résultat attendu: Très peu de résultats pertinents")
    
    # Test 2: Vraies entreprises
    print("\n2️⃣ TEST AVEC VRAIES ENTREPRISES")
    print("-" * 40)
    print("📁 Fichier: entreprises_test_reelles.xlsx")
    print("🏢 Type: Grandes entreprises françaises")
    print("🔍 Résultat attendu: Résultats très pertinents")
    
    print("\n💡 POUR LANCER LES TESTS:")
    print("\n# Test 1 (micro-entreprises):")
    print("# Modifiez run_echantillon.py:")
    print('# fichier_excel = "data/input/entreprises_base.xlsx"')
    print("# python run_echantillon.py")
    
    print("\n# Test 2 (vraies entreprises):")
    print("# Modifiez run_echantillon.py:")
    print('# fichier_excel = "data/input/entreprises_test_reelles.xlsx"')
    print("# python run_echantillon.py")
    
    print("\n📊 MÉTRIQUES À COMPARER:")
    print("   • Taux de validation des résultats")
    print("   • Nombre d'entreprises avec résultats")
    print("   • Pertinence du contenu trouvé")
    print("   • Adéquation avec les thématiques")
    print("   • Qualité des rapports générés")

if __name__ == "__main__":
    comparer_resultats()
