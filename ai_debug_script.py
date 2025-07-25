#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug IA pour comprendre pourquoi elle rejette tout
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, "scripts")

from ai_validation_module import AIValidationModule

def debug_ia_reponses():
    """Debug détaillé des réponses IA"""
    print("🔍 DEBUG IA - ANALYSE DES REJETS")
    print("=" * 60)
    
    try:
        ai_module = AIValidationModule()
        
        # Exemples de vrais résultats de votre système
        exemples_test = [
            {
                'entreprise': {
                    'nom': 'CARREFOUR',
                    'commune': 'Boulogne-Billancourt',
                    'secteur_naf': 'Commerce de détail'
                },
                'resultat': {
                    'titre': 'CARREFOUR recrute 50 personnes en CDI à Boulogne-Billancourt',
                    'description': 'Le groupe Carrefour annonce le recrutement de 50 collaborateurs pour son magasin.',
                    'url': 'https://www.carrefour.fr/recrutement'
                },
                'theme': 'recrutements'
            },
            {
                'entreprise': {
                    'nom': 'MICHELIN',
                    'commune': 'Clermont-Ferrand',
                    'secteur_naf': 'Fabrication de pneumatiques'
                },
                'resultat': {
                    'titre': 'MICHELIN lance un nouveau pneu innovant',
                    'description': 'Michelin présente sa dernière innovation en matière de pneumatiques.',
                    'url': 'https://www.michelin.fr/innovation'
                },
                'theme': 'innovations'
            },
            {
                'entreprise': {
                    'nom': 'SANOFI',
                    'commune': 'Gentilly',
                    'secteur_naf': 'Industrie pharmaceutique'
                },
                'resultat': {
                    'titre': 'SANOFI organise une journée portes ouvertes',
                    'description': 'Sanofi invite le public à découvrir ses laboratoires lors d\'une journée spéciale.',
                    'url': 'https://www.sanofi.fr/evenements'
                },
                'theme': 'evenements'
            }
        ]
        
        print("🧪 TEST AVEC EXEMPLES PARFAITS:")
        print("-" * 40)
        
        for i, exemple in enumerate(exemples_test, 1):
            print(f"\n📊 Test {i}: {exemple['entreprise']['nom']} - {exemple['theme']}")
            print(f"   📋 Titre: {exemple['resultat']['titre']}")
            print(f"   📝 Description: {exemple['resultat']['description']}")
            
            # Validation IA avec debug
            validation = ai_module.validate_search_result(
                exemple['entreprise'], 
                exemple['resultat'], 
                exemple['theme']
            )
            
            print(f"\n   🤖 RÉPONSE IA:")
            print(f"      ✅ Pertinent: {validation.is_relevant}")
            print(f"      🎯 Confiance: {validation.confidence_score:.2f}")
            print(f"      💬 Explication: {validation.explanation}")
            print(f"      🏷️  Thèmes détectés: {validation.themes_detected}")
            
            if not validation.is_relevant:
                print(f"      ❌ PROBLÈME: L'IA rejette un exemple PARFAIT!")
                print(f"      📋 Détails extracted_info: {validation.extracted_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur debug: {e}")
        return False

def creer_ia_permissive():
    """Création d'une version IA permissive pour tester"""
    print("\n🔧 CRÉATION IA PERMISSIVE")
    print("=" * 40)
    
    # Prompt permissif pour test
    prompt_permissif = '''Tu es un expert en veille économique TRÈS PERMISSIF.

IMPORTANT: Ton objectif est d'ACCEPTER le maximum de résultats comme pertinents.

RÈGLES PERMISSIVES:
1. Si le nom de l'entreprise apparaît dans le titre OU description → PERTINENT
2. Si la thématique est mentionnée → PERTINENT  
3. En cas de doute → PERTINENT
4. Seuls les résultats CLAIREMENT hors-sujet (dictionnaires, forums linguistiques) → NON PERTINENT

EXEMPLES D'ACCEPTATION:
- "CARREFOUR recrute" → PERTINENT (nom + thématique)
- "Emploi chez CARREFOUR" → PERTINENT (thématique + nom)
- "CARREFOUR développement" → PERTINENT (nom + activité)

Réponds TOUJOURS en JSON valide:
{
  "is_relevant": true (par défaut),
  "confidence_score": 0.8 (élevé par défaut),
  "explanation": "Explication courte et positive",
  "extracted_info": {
    "key_facts": ["Nom entreprise mentionné", "Thématique présente"],
    "date_mentioned": null,
    "location_mentioned": "Commune si mentionnée"
  },
  "themes_detected": ["thématique_demandée"]
}'''
    
    # Sauvegarde du prompt permissif
    with open("prompt_permissif.txt", "w", encoding="utf-8") as f:
        f.write(prompt_permissif)
    
    print("✅ Prompt permissif sauvé dans: prompt_permissif.txt")
    print("💡 Utilisez ce prompt pour remplacer temporairement le prompt strict")

def modifier_ai_module_permissif():
    """Instructions pour modifier temporairement le module IA"""
    print("\n🔧 MODIFICATION TEMPORAIRE DU MODULE IA")
    print("=" * 50)
    
    print("📝 ÉTAPE 1: Ouvrez ai_validation_module.py")
    print("📝 ÉTAPE 2: Trouvez la méthode _get_validation_system_prompt")
    print("📝 ÉTAPE 3: Remplacez tout le contenu du return par:")
    
    code_remplacement = '''
    def _get_validation_system_prompt(self) -> str:
        """Prompt système PERMISSIF pour test"""
        return """Tu es un expert en veille économique PERMISSIF.

OBJECTIF: ACCEPTER le maximum de résultats comme pertinents.

CRITÈRES PERMISSIFS:
1. Nom d'entreprise mentionné → ACCEPTER
2. Thématique mentionnée → ACCEPTER
3. Contexte professionnel → ACCEPTER
4. En cas de doute → ACCEPTER

REJETER SEULEMENT:
- Forums linguistiques (wordreference, etc.)
- Dictionnaires/définitions pures
- Contenu sans rapport avec l'entreprise

Réponds en JSON avec is_relevant: true par défaut:
{
  "is_relevant": true,
  "confidence_score": 0.7,
  "explanation": "Pertinent car [raison]",
  "extracted_info": {"key_facts": ["info trouvée"]},
  "themes_detected": ["thématique"]
}"""
'''
    
    print(code_remplacement)
    print("\n📝 ÉTAPE 4: Sauvegardez et relancez le test")

def test_simple_validation():
    """Test ultra-simple de validation"""
    print("\n🎯 TEST SIMPLE")
    print("=" * 30)
    
    try:
        ai_module = AIValidationModule()
        
        # Test minimal
        entreprise = {'nom': 'TEST', 'commune': 'Paris', 'secteur_naf': 'Test'}
        resultat = {'titre': 'TEST recrute', 'description': 'Offre emploi TEST', 'url': ''}
        
        validation = ai_module.validate_search_result(entreprise, resultat, 'recrutements')
        
        print(f"Pertinent: {validation.is_relevant}")
        print(f"Explication: {validation.explanation}")
        
        if validation.is_relevant:
            print("✅ IA fonctionne - elle accepte des résultats évidents")
        else:
            print("❌ IA trop stricte - elle rejette même l'évident")
            print("💡 Solution: Utilisez le prompt permissif ci-dessus")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Diagnostic complet"""
    print("🚀 DIAGNOSTIC COMPLET IA")
    print("=" * 70)
    
    # 1. Test avec exemples parfaits
    debug_success = debug_ia_reponses()
    
    # 2. Test simple
    test_simple_validation()
    
    # 3. Solution
    if not debug_success:
        print("\n💡 SOLUTION IMMÉDIATE:")
        print("1. L'IA rejette tout car prompts trop stricts")
        print("2. Modifiez temporairement le prompt (instructions ci-dessous)")
        print("3. Ou utilisez le mode fallback classique")
        
        creer_ia_permissive()
        modifier_ai_module_permissif()
    
    print("\n🎯 ACTIONS IMMÉDIATES:")
    print("1. Modifiez le prompt IA (instructions ci-dessus)")
    print("2. Ou lancez sans IA: python main_with_ai.py → mode 2")
    print("3. Une fois que ça marche, on ajustera la sélectivité")

if __name__ == "__main__":
    main()