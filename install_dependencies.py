#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'installation des dépendances pour la recherche web améliorée
"""

import subprocess
import sys
import os

def installer_dependances():
    """Installation des dépendances nécessaires"""
    print("🔧 Installation des dépendances pour la recherche web améliorée")
    print("=" * 60)
    
    # Liste des packages à installer
    packages = [
        'duckduckgo-search>=3.9.0',  # Bibliothèque spécialisée
        'requests-html>=0.10.0',     # Pour le scraping JavaScript
        'fake-useragent>=1.4.0',     # Pour les User-Agents réalistes
        'httpx>=0.24.0',             # Client HTTP moderne
        'lxml>=4.9.0',               # Parser XML/HTML rapide
    ]
    
    print("📦 Packages à installer:")
    for package in packages:
        print(f"   - {package}")
    
    print("\n🚀 Installation en cours...")
    
    # Installation des packages
    for package in packages:
        try:
            print(f"   📥 Installation de {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package, "--upgrade"
            ])
            print(f"   ✅ {package} installé avec succès")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erreur installation {package}: {e}")
            continue
    
    print("\n🧪 Test des imports...")
    
    # Test des imports
    imports_test = [
        ('duckduckgo_search', 'DDGS'),
        ('requests_html', 'HTMLSession'),
        ('fake_useragent', 'UserAgent'),
        ('httpx', 'Client'),
        ('lxml', 'etree'),
    ]
    
    for module, classe in imports_test:
        try:
            exec(f"from {module} import {classe}")
            print(f"   ✅ {module} importé avec succès")
        except ImportError as e:
            print(f"   ⚠️  {module} non disponible: {e}")
    
    print("\n✅ Installation terminée!")
    print("\n💡 Conseils pour améliorer les recherches:")
    print("   - Utilisez un VPN pour éviter les blocages IP")
    print("   - Augmentez les délais entre requêtes si nécessaire")
    print("   - Testez avec un petit échantillon d'abord")
    
    return True

if __name__ == "__main__":
    try:
        installer_dependances()
    except Exception as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        sys.exit(1)