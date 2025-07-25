#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug des vraies données que votre système passe à l'IA
"""

import os
import sys
import json
from pathlib import Path
sys.path.insert(0, "scripts")

from scripts.extracteur_donnees import ExtracteurDonnees
from scripts.recherche_web import RechercheWeb
from datetime import timedelta

def debug_vraies_donnees():
    """Debug des vraies données générées par votre système"""
    print("🔍 DEBUG DES VRAIES DONNÉES DE VOTRE SYSTÈME")
    print("=" * 60)
    
    # 1. Extraction d'une vraie entreprise
    fichier_excel = "data/input/entreprises_test_reelles.xlsx"
    if not os.path.exists(fichier_excel):
        fichier_excel = "data/input/entreprises_base.xlsx"
    
    if not os.path.exists(fichier_excel):
        print("❌ Aucun fichier Excel trouvé")
        return
    
    try:
        # Extraction
        print("📊 ÉTAPE 1: Extraction d'une entreprise")
        extracteur = ExtracteurDonnees(fichier_excel)
        entreprises = extracteur.extraire_echantillon(1)  # Juste 1 entreprise
        
        if not entreprises:
            print("❌ Aucune entreprise extraite")
            return
        
        entreprise = entreprises[0]
        print(f"✅ Entreprise sélectionnée: {entreprise['nom']} ({entreprise['commune']})")
        
        # Recherche web
        print("\n🔍 ÉTAPE 2: Recherche web pour cette entreprise")
        recherche = RechercheWeb(timedelta(days=180))
        resultats = recherche.rechercher_entreprise(entreprise)
        
        donnees_thematiques = resultats.get('donnees_thematiques', {})
        print(f"📊 Thématiques trouvées: {list(donnees_thematiques.keys())}")
        
        # Analyse détaillée des données
        print("\n📋 ÉTAPE 3: Analyse détaillée des données")
        print("=" * 50)
        
        total_extraits = 0
        for thematique, donnees in donnees_thematiques.items():
            if isinstance(donnees, dict):
                extraits = donnees.get('extraits_textuels', [])
                if extraits:
                    print(f"\n🎯 THÉMATIQUE: {thematique}")
                    print(f"   📊 Nombre d'extraits: {len(extraits)}")
                    
                    # Affichage des 3 premiers extraits
                    for i, extrait in enumerate(extraits[:3], 1):
                        print(f"\n   📄 Extrait {i}:")
                        
                        if isinstance(extrait, dict):
                            titre = extrait.get('titre', 'N/A')
                            description = extrait.get('description', 'N/A')
                            url = extrait.get('url', 'N/A')
                            
                            print(f"      🏷️  Titre: {titre}")
                            print(f"      📝 Description: {description[:100]}...")
                            print(f"      🔗 URL: {url}")
                            
                            # ÉVALUATION QUALITÉ
                            qualite = evaluer_qualite_extrait(extrait, entreprise['nom'])
                            print(f"      📊 Qualité: {qualite}")
                            
                        elif isinstance(extrait, str):
                            print(f"      📄 Contenu: {extrait[:100]}...")
                            print(f"      ⚠️  Format: String au lieu de Dict")
                        else:
                            print(f"      ❌ Format inattendu: {type(extrait)}")
                        
                        total_extraits += 1
        
        print(f"\n📊 RÉSUMÉ GLOBAL:")
        print(f"   🏢 Entreprise: {entreprise['nom']}")
        print(f"   🎯 Thématiques: {len(donnees_thematiques)}")
        print(f"   📄 Total extraits: {total_extraits}")
        
        if total_extraits == 0:
            print(f"   ❌ PROBLÈME: Aucun extrait trouvé!")
            print(f"   💡 L'IA n'a rien à valider")
        else:
            print(f"   ✅ Données disponibles pour l'IA")
            
            # Test de validation IA sur les vraies données
            print(f"\n🤖 ÉTAPE 4: Test IA sur vraies données")
            tester_ia_sur_vraies_donnees(entreprise, donnees_thematiques)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

def evaluer_qualite_extrait(extrait, nom_entreprise):
    """Évaluation de la qualité d'un extrait"""
    if not isinstance(extrait, dict):
        return "❌ MAUVAISE (format incorrect)"
    
    titre = extrait.get('titre', '')
    description = extrait.get('description', '')
    url = extrait.get('url', '')
    
    # Critères de qualité
    score_qualite = 0
    problemes = []
    
    # 1. Mention de l'entreprise
    nom_lower = nom_entreprise.lower()
    if nom_lower in titre.lower() or nom_lower in description.lower():
        score_qualite += 3
    else:
        problemes.append("Nom entreprise absent")
    
    # 2. Contenu substantiel
    if len(titre) > 10 and len(description) > 20:
        score_qualite += 2
    else:
        problemes.append("Contenu trop court")
    
    # 3. URL valide
    if url and url.startswith('http'):
        score_qualite += 1
    else:
        problemes.append("URL manquante/invalide")
    
    # 4. Détection faux positifs
    texte_complet = f"{titre} {description} {url}".lower()
    faux_positifs = ['wordreference', 'dictionary', 'definition', 'forum', 'wikipedia']
    
    for fp in faux_positifs:
        if fp in texte_complet:
            score_qualite -= 5
            problemes.append(f"Faux positif détecté: {fp}")
    
    # Évaluation finale
    if score_qualite >= 5:
        return "✅ EXCELLENTE"
    elif score_qualite >= 3:
        return "🟡 CORRECTE"
    elif score_qualite >= 1:
        return f"⚠️ FAIBLE ({', '.join(problemes)})"
    else:
        return f"❌ MAUVAISE ({', '.join(problemes)})"

def tester_ia_sur_vraies_donnees(entreprise, donnees_thematiques):
    """Test de l'IA sur les vraies données"""
    try:
        from ai_validation_module import AIValidationModule
        
        ai_module = AIValidationModule()
        
        validations_reussies = 0
        validations_totales = 0
        
        for thematique, donnees in donnees_thematiques.items():
            if isinstance(donnees, dict):
                extraits = donnees.get('extraits_textuels', [])
                
                for extrait in extraits[:2]:  # Test sur 2 premiers extraits
                    validations_totales += 1
                    
                    # Normalisation pour l'IA
                    if isinstance(extrait, dict):
                        resultat_test = extrait
                    else:
                        resultat_test = {
                            'titre': str(extrait),
                            'description': '',
                            'url': ''
                        }
                    
                    print(f"\n   🧪 Test IA: {thematique}")
                    print(f"      📋 Titre: {resultat_test.get('titre', '')[:50]}...")
                    
                    # Validation IA
                    validation = ai_module.validate_search_result(entreprise, resultat_test, thematique)
                    
                    if validation.is_relevant:
                        validations_reussies += 1
                        print(f"      ✅ ACCEPTÉ (confiance: {validation.confidence_score:.2f})")
                    else:
                        print(f"      ❌ REJETÉ: {validation.explanation[:80]}...")
        
        print(f"\n📊 RÉSULTAT TEST IA:")
        print(f"   🎯 Validations réussies: {validations_reussies}/{validations_totales}")
        
        if validations_reussies == 0:
            print(f"   🚨 PROBLÈME: L'IA rejette tout!")
            print(f"   💡 Cause probable: Données de mauvaise qualité")
        else:
            print(f"   ✅ L'IA fonctionne partiellement")
            
    except Exception as e:
        print(f"   ❌ Erreur test IA: {e}")

def analyser_problemes_donnees():
    """Analyse des problèmes courants dans les données"""
    print("\n🔍 ANALYSE DES PROBLÈMES COURANTS")
    print("=" * 50)
    
    problemes_courants = [
        "📄 Format des extraits incorrect (string au lieu de dict)",
        "🏷️  Titres vides ou trop courts",
        "📝 Descriptions manquantes",
        "🔗 URLs invalides ou manquantes",
        "🏢 Nom d'entreprise absent du contenu",
        "🎯 Thématiques mal alignées avec le contenu",
        "❌ Faux positifs (forums, dictionnaires)",
        "📊 Données trop génériques"
    ]
    
    print("Problèmes fréquents qui font que l'IA rejette:")
    for probleme in problemes_courants:
        print(f"  • {probleme}")
    
    print(f"\n💡 SOLUTIONS:")
    print(f"  1. 🔧 Améliorer la qualité de recherche web")
    print(f"  2. 🎯 Validation pré-IA des données")
    print(f"  3. 📋 Normalisation du format des extraits")
    print(f"  4. ⚡ Mode fallback si données insuffisantes")

def main():
    """Debug complet"""
    print("🚀 DEBUG COMPLET DES VRAIES DONNÉES")
    print("=" * 70)
    
    debug_vraies_donnees()
    analyser_problemes_donnees()
    
    print(f"\n🎯 PROCHAINES ÉTAPES:")
    print(f"1. 📊 Identifiez la qualité de vos données réelles")
    print(f"2. 🔧 Corrigez les problèmes de format si nécessaire")
    print(f"3. 🤖 Ajustez l'IA selon la qualité réelle")
    print(f"4. ⚡ Utilisez le fallback si données trop pauvres")

if __name__ == "__main__":
    main()