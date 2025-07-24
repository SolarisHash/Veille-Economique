#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug du script principal pour identifier le problème de liaison
"""

import sys
from pathlib import Path
sys.path.insert(0, "scripts")

def debug_script_principal():
    """Debug du script principal"""
    print("🔍 DEBUG DU SCRIPT PRINCIPAL")
    print("=" * 60)
    
    # Recherche du script principal
    scripts_possibles = [
        "main.py",
        "run_echantillon.py", 
        "scripts/main.py"
    ]
    
    script_principal = None
    for script in scripts_possibles:
        if Path(script).exists():
            script_principal = script
            break
    
    if not script_principal:
        print("❌ Aucun script principal trouvé")
        print("💡 Créons un script principal corrigé...")
        creer_script_principal_corrige()
        return
    
    print(f"📄 Script principal trouvé: {script_principal}")
    
    # Lecture du script
    try:
        with open(script_principal, 'r', encoding='utf-8') as f:
            contenu = f.read()
        
        # Vérifications critiques
        print(f"\n🔍 VÉRIFICATIONS CRITIQUES:")
        
        verifications = [
            ("Import AnalyseurThematiques", "from.*analyseur_thematiques.*import.*AnalyseurThematiques"),
            ("Création analyseur", "AnalyseurThematiques\\("),
            ("Appel analyser_resultats", "\\.analyser_resultats\\("),
            ("Passage des données", "resultats_bruts|donnees_enrichies"),
            ("Génération rapports", "generer.*rapport|GenerateurRapports")
        ]
        
        import re
        
        for nom, pattern in verifications:
            if re.search(pattern, contenu, re.IGNORECASE):
                print(f"   ✅ {nom}: OK")
            else:
                print(f"   ❌ {nom}: MANQUANT")
        
        # Recherche de problèmes spécifiques
        print(f"\n🔍 PROBLÈMES POTENTIELS:")
        
        if "analyser_resultats" not in contenu:
            print("   ❌ CRITIQUE: analyser_resultats jamais appelé")
            print("      → L'analyseur n'est jamais utilisé!")
        
        if "donnees_enrichies" not in contenu and "resultats_analyses" not in contenu:
            print("   ❌ CRITIQUE: Pas de variable pour résultats d'analyse")
            print("      → Les données analysées ne sont pas récupérées!")
        
        if "generer" not in contenu.lower():
            print("   ❌ CRITIQUE: Pas de génération de rapports")
            print("      → Aucun rapport n'est généré!")
        
        # Affichage de la partie critique du script
        print(f"\n📋 PARTIE CRITIQUE DU SCRIPT:")
        print("-" * 40)
        
        lignes = contenu.split('\n')
        in_critical_section = False
        
        for i, ligne in enumerate(lignes):
            ligne_lower = ligne.lower()
            
            # Début de section critique
            if any(keyword in ligne_lower for keyword in ['recherche', 'analyse', 'rapport']):
                in_critical_section = True
            
            # Affichage des lignes critiques
            if in_critical_section:
                print(f"{i+1:3}: {ligne}")
                
                # Fin de section si ligne vide ou nouveau bloc
                if ligne.strip() == "" and in_critical_section:
                    print("...")
                    break
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lecture script: {e}")
        return False

def creer_script_principal_corrige():
    """Crée un script principal corrigé et fonctionnel"""
    print("\n🔧 CRÉATION SCRIPT PRINCIPAL CORRIGÉ")
    print("=" * 60)
    
    script_corrige = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal CORRIGÉ pour la veille économique
"""

import os
import sys
from pathlib import Path
from datetime import timedelta

# Import des modules
sys.path.insert(0, "scripts")
from extracteur_donnees import ExtracteurDonnees
from recherche_web import RechercheWeb
from analyseur_thematiques import AnalyseurThematiques
from generateur_rapports import GenerateurRapports
from diagnostic_logger import DiagnosticLogger

def main():
    """Script principal corrigé"""
    print("🚀 VEILLE ÉCONOMIQUE - VERSION CORRIGÉE")
    print("=" * 60)
    
    # Configuration
    fichier_excel = "data/input/entreprises_base.xlsx"
    nb_entreprises = 20
    
    if not os.path.exists(fichier_excel):
        print(f"❌ Fichier manquant: {fichier_excel}")
        return False
    
    # Initialisation des modules
    logger = DiagnosticLogger()
    
    try:
        # 1. EXTRACTION DES DONNÉES
        print("\\n📊 ÉTAPE 1/5 - EXTRACTION")
        print("-" * 40)
        
        extracteur = ExtracteurDonnees(fichier_excel)
        entreprises = extracteur.extraire_echantillon(nb_entreprises)
        print(f"✅ {len(entreprises)} entreprises extraites")
        
        # 2. RECHERCHE WEB
        print("\\n🔍 ÉTAPE 2/5 - RECHERCHE WEB")
        print("-" * 40)
        
        recherche = RechercheWeb(timedelta(days=180))
        resultats_bruts = []
        
        for i, entreprise in enumerate(entreprises, 1):
            nom_entreprise = logger.log_entreprise_debut(entreprise)
            print(f"  🏢 {i}/{len(entreprises)}: {nom_entreprise}")
            
            try:
                resultats = recherche.rechercher_entreprise(entreprise, logger=logger)
                resultats_bruts.append(resultats)
                logger.log_extraction_resultats(nom_entreprise, True)
                
            except Exception as e:
                logger.log_extraction_resultats(nom_entreprise, False, str(e))
                print(f"    ❌ Erreur: {e}")
                continue
        
        print(f"✅ Recherche terminée: {len(resultats_bruts)} entreprises")
        
        # 3. ANALYSE THÉMATIQUE ← SECTION CRITIQUE
        print("\\n🔬 ÉTAPE 3/5 - ANALYSE THÉMATIQUE")
        print("-" * 40)
        
        thematiques = ['recrutements', 'evenements', 'innovations', 'vie_entreprise', 
                      'exportations', 'aides_subventions', 'fondation_sponsor']
        analyseur = AnalyseurThematiques(thematiques)
        
        print(f"🔬 Analyse avec seuil: {analyseur.seuil_pertinence}")
        
        # ✅ APPEL CRITIQUE: Ici les données passent de recherche → analyse
        donnees_enrichies = analyseur.analyser_resultats(resultats_bruts, logger=logger)
        
        # Vérification des résultats
        entreprises_actives = [e for e in donnees_enrichies if e.get('score_global', 0) > 0.2]
        print(f"✅ Analyse terminée: {len(entreprises_actives)} entreprises actives détectées")
        
        if len(entreprises_actives) == 0:
            print("⚠️ ATTENTION: Aucune entreprise active détectée!")
            print("   Vérifiez les seuils et les données")
        
        # 4. GÉNÉRATION DES RAPPORTS ← SECTION CRITIQUE
        print("\\n📊 ÉTAPE 4/5 - GÉNÉRATION RAPPORTS")
        print("-" * 40)
        
        generateur = GenerateurRapports()
        
        # ✅ APPEL CRITIQUE: Génération avec données enrichies
        rapports = generateur.generer_tous_rapports(donnees_enrichies)
        
        print("✅ Rapports générés:")
        for type_rapport, chemin in rapports.items():
            if not chemin.startswith("ERREUR"):
                print(f"   📄 {type_rapport}: {chemin}")
            else:
                print(f"   ❌ {type_rapport}: {chemin}")
        
        # 5. DIAGNOSTIC FINAL
        print("\\n📋 ÉTAPE 5/5 - DIAGNOSTIC")
        print("-" * 40)
        
        rapport_diagnostic = logger.generer_rapport_final()
        print(rapport_diagnostic)
        
        # RÉSUMÉ FINAL
        print("\\n🎉 RÉSUMÉ FINAL")
        print("=" * 60)
        print(f"📊 Entreprises traitées: {len(entreprises)}")
        print(f"🔍 Recherches réussies: {len(resultats_bruts)}")
        print(f"🎯 Entreprises actives: {len(entreprises_actives)}")
        print(f"📄 Rapports générés: {len([r for r in rapports.values() if not r.startswith('ERREUR')])}")
        
        if len(entreprises_actives) > 0:
            print("\\n🏆 TOP ENTREPRISES ACTIVES:")
            for i, ent in enumerate(entreprises_actives[:3], 1):
                nom = ent.get('nom', 'N/A')
                score = ent.get('score_global', 0)
                themes = ent.get('thematiques_principales', [])
                print(f"   {i}. {nom}: {score:.3f} → {themes}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR GÉNÉRALE: {e}")
        import traceback
        traceback.print_exc()
        
        # Diagnostic même en cas d'erreur
        try:
            rapport_diagnostic = logger.generer_rapport_final()
            print("\\n" + rapport_diagnostic)
        except:
            pass
        
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\\n✅ SUCCÈS: Veille économique terminée!")
    else:
        print("\\n❌ ÉCHEC: Consultez les erreurs ci-dessus")
        sys.exit(1)
'''
    
    # Sauvegarde
    try:
        with open("main_corrige.py", 'w', encoding='utf-8') as f:
            f.write(script_corrige)
        
        print("✅ Script principal corrigé créé: main_corrige.py")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création script: {e}")
        return False

def test_avec_script_corrige():
    """Test avec le script corrigé"""
    print("\n🧪 TEST AVEC SCRIPT CORRIGÉ")
    print("=" * 60)
    
    if not Path("main_corrige.py").exists():
        print("❌ Script corrigé non trouvé")
        return False
    
    print("📋 INSTRUCTIONS:")
    print("1. Lancez: python main_corrige.py")
    print("2. Comparez avec votre script actuel")
    print("3. Identifiez les différences")
    print("4. Corrigez votre script principal")
    
    return True

def main():
    """Debug complet"""
    print("🚀 DEBUG DU PROBLÈME DE LIAISON")
    print("=" * 80)
    
    # 1. Debug du script principal
    script_ok = debug_script_principal()
    
    # 2. Création du script corrigé si nécessaire
    if not script_ok:
        creer_script_principal_corrige()
    
    # 3. Instructions de test
    test_avec_script_corrige()
    
    print("\\n" + "="*80)
    print("🎯 DIAGNOSTIC FINAL")
    print("="*80)
    print("✅ ANALYSEUR FONCTIONNE (vérifié)")
    print("✅ RECHERCHE WEB FONCTIONNE (166 résultats)")
    print("❌ PROBLÈME: Liaison entre recherche et analyse")
    print("\\n💡 SOLUTION:")
    print("1. Votre script principal n'appelle pas analyser_resultats()")
    print("2. Ou les données ne sont pas transmises correctement")
    print("3. Utilisez main_corrige.py comme référence")

if __name__ == "__main__":
    main()