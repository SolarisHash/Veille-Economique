#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de logging détaillé pour diagnostic de la veille économique
À intégrer dans vos modules existants
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

class StatutTraitement(Enum):
    SUCCES = "succès"
    ECHEC = "échec"
    PARTIEL = "partiel"
    ERREUR = "erreur"

@dataclass
class LogEntreprise:
    """Log détaillé pour une entreprise"""
    nom: str
    siret: str
    commune: str
    
    # Statuts par étape
    extraction_ok: bool = False
    recherche_web_ok: bool = False
    analyse_thematique_ok: bool = False
    
    # Détails recherche web
    requetes_generees: List[str] = None
    moteurs_testes: List[str] = None
    moteur_reussi: str = ""
    nb_resultats_bruts: int = 0
    nb_resultats_valides: int = 0
    
    # Détails analyse thématique
    thematiques_detectees: List[str] = None
    score_global: float = 0.0
    
    # Erreurs
    erreurs: List[str] = None
    avertissements: List[str] = None
    
    def __post_init__(self):
        if self.requetes_generees is None:
            self.requetes_generees = []
        if self.moteurs_testes is None:
            self.moteurs_testes = []
        if self.thematiques_detectees is None:
            self.thematiques_detectees = []
        if self.erreurs is None:
            self.erreurs = []
        if self.avertissements is None:
            self.avertissements = []

class DiagnosticLogger:
    """Logger de diagnostic pour la veille économique"""
    
    def __init__(self):
        self.logs_entreprises = []
        self.statistiques_globales = {
            'debut_traitement': datetime.now(),
            'fin_traitement': None,
            'duree_totale': None,
            
            # Compteurs par étape
            'extraction_reussie': 0,
            'extraction_echouee': 0,
            'recherche_reussie': 0,
            'recherche_echouee': 0,
            'analyse_reussie': 0,
            'analyse_echouee': 0,
            
            # Statistiques recherche web
            'moteurs_utilises': {},
            'requetes_totales': 0,
            'resultats_bruts_totaux': 0,
            'resultats_valides_totaux': 0,
            'taux_validation': 0.0,
            
            # Statistiques thématiques
            'thematiques_stats': {},
            'entreprises_sans_resultats': 0,
            'entreprises_avec_resultats': 0,
            
            # Problèmes identifiés
            'problemes_frequents': {},
            'entreprises_problematiques': []
        }
        
        # Création du dossier de logs
        Path("logs/diagnostic").mkdir(parents=True, exist_ok=True)
    
    def log_entreprise_debut(self, entreprise: Dict) -> str:
        """Début du traitement d'une entreprise"""
        nom = entreprise.get('nom', 'Inconnu')
        siret = entreprise.get('siret', 'Inconnu')
        commune = entreprise.get('commune', 'Inconnue')
        
        log_entreprise = LogEntreprise(
            nom=nom,
            siret=siret,
            commune=commune
        )
        
        self.logs_entreprises.append(log_entreprise)
        return nom
    
    def log_extraction_resultats(self, nom_entreprise: str, succes: bool, erreur: str = ""):
        """Log des résultats d'extraction"""
        log_entreprise = self._get_log_entreprise(nom_entreprise)
        if log_entreprise:
            log_entreprise.extraction_ok = succes
            if erreur:
                log_entreprise.erreurs.append(f"Extraction: {erreur}")
            
            if succes:
                self.statistiques_globales['extraction_reussie'] += 1
            else:
                self.statistiques_globales['extraction_echouee'] += 1
    
    def log_recherche_web(self, nom_entreprise: str, requetes: List[str], moteurs_testes: List[str], 
                         moteur_reussi: str, nb_bruts: int, nb_valides: int, erreurs: List[str] = None):
        """Log détaillé de la recherche web"""
        log_entreprise = self._get_log_entreprise(nom_entreprise)
        if log_entreprise:
            log_entreprise.requetes_generees = requetes.copy()
            log_entreprise.moteurs_testes = moteurs_testes.copy()
            log_entreprise.moteur_reussi = moteur_reussi
            log_entreprise.nb_resultats_bruts = nb_bruts
            log_entreprise.nb_resultats_valides = nb_valides
            log_entreprise.recherche_web_ok = nb_valides > 0
            
            if erreurs:
                log_entreprise.erreurs.extend([f"Recherche: {e}" for e in erreurs])
            
            # Statistiques globales
            self.statistiques_globales['requetes_totales'] += len(requetes)
            self.statistiques_globales['resultats_bruts_totaux'] += nb_bruts
            self.statistiques_globales['resultats_valides_totaux'] += nb_valides
            
            # Comptage moteurs
            for moteur in moteurs_testes:
                self.statistiques_globales['moteurs_utilises'][moteur] = \
                    self.statistiques_globales['moteurs_utilises'].get(moteur, 0) + 1
            
            if nb_valides > 0:
                self.statistiques_globales['recherche_reussie'] += 1
            else:
                self.statistiques_globales['recherche_echouee'] += 1
                self.statistiques_globales['entreprises_problematiques'].append(nom_entreprise)
    
    def log_analyse_thematique(self, nom_entreprise: str, thematiques: List[str], score: float, 
                              details: Dict = None, erreurs: List[str] = None):
        """Log de l'analyse thématique"""
        log_entreprise = self._get_log_entreprise(nom_entreprise)
        if log_entreprise:
            log_entreprise.thematiques_detectees = thematiques.copy()
            log_entreprise.score_global = score
            log_entreprise.analyse_thematique_ok = len(thematiques) > 0
            
            if erreurs:
                log_entreprise.erreurs.extend([f"Analyse: {e}" for e in erreurs])
            
            # Statistiques globales
            for thematique in thematiques:
                self.statistiques_globales['thematiques_stats'][thematique] = \
                    self.statistiques_globales['thematiques_stats'].get(thematique, 0) + 1
            
            if len(thematiques) > 0:
                self.statistiques_globales['analyse_reussie'] += 1
                self.statistiques_globales['entreprises_avec_resultats'] += 1
            else:
                self.statistiques_globales['analyse_echouee'] += 1
                self.statistiques_globales['entreprises_sans_resultats'] += 1
    
    def log_probleme(self, nom_entreprise: str, type_probleme: str, description: str):
        """Log d'un problème spécifique"""
        log_entreprise = self._get_log_entreprise(nom_entreprise)
        if log_entreprise:
            log_entreprise.avertissements.append(f"{type_probleme}: {description}")
        
        # Comptage des problèmes fréquents
        self.statistiques_globales['problemes_frequents'][type_probleme] = \
            self.statistiques_globales['problemes_frequents'].get(type_probleme, 0) + 1
    
    def finaliser_diagnostics(self):
        """Finalise les statistiques et génère le rapport final"""
        self.statistiques_globales['fin_traitement'] = datetime.now()
        self.statistiques_globales['duree_totale'] = str(
            self.statistiques_globales['fin_traitement'] - self.statistiques_globales['debut_traitement']
        )
        
        # Calculs finaux
        total_requetes = self.statistiques_globales['requetes_totales']
        resultats_bruts = self.statistiques_globales['resultats_bruts_totaux']
        resultats_valides = self.statistiques_globales['resultats_valides_totaux']
        
        if resultats_bruts > 0:
            self.statistiques_globales['taux_validation'] = (resultats_valides / resultats_bruts) * 100
    
    def generer_rapport_final(self) -> str:
        """Génère le rapport de diagnostic final"""
        self.finaliser_diagnostics()
        
        rapport = []
        rapport.append("=" * 80)
        rapport.append("🔍 RAPPORT DE DIAGNOSTIC - VEILLE ÉCONOMIQUE")
        rapport.append("=" * 80)
        
        # Résumé général
        rapport.append("\n📊 RÉSUMÉ GÉNÉRAL:")
        rapport.append(f"   ⏰ Durée totale: {self.statistiques_globales['duree_totale']}")
        rapport.append(f"   🏢 Entreprises traitées: {len(self.logs_entreprises)}")
        rapport.append(f"   ✅ Avec résultats: {self.statistiques_globales['entreprises_avec_resultats']}")
        rapport.append(f"   ❌ Sans résultats: {self.statistiques_globales['entreprises_sans_resultats']}")
        
        # Statistiques par étape
        rapport.append("\n🔄 STATISTIQUES PAR ÉTAPE:")
        rapport.append("📥 Extraction:")
        rapport.append(f"   ✅ Réussies: {self.statistiques_globales['extraction_reussie']}")
        rapport.append(f"   ❌ Échouées: {self.statistiques_globales['extraction_echouee']}")
        
        rapport.append("🔍 Recherche Web:")
        rapport.append(f"   ✅ Réussies: {self.statistiques_globales['recherche_reussie']}")
        rapport.append(f"   ❌ Échouées: {self.statistiques_globales['recherche_echouee']}")
        rapport.append(f"   📊 Requêtes totales: {self.statistiques_globales['requetes_totales']}")
        rapport.append(f"   📄 Résultats bruts: {self.statistiques_globales['resultats_bruts_totaux']}")
        rapport.append(f"   ✅ Résultats valides: {self.statistiques_globales['resultats_valides_totaux']}")
        rapport.append(f"   📈 Taux validation: {self.statistiques_globales['taux_validation']:.1f}%")
        
        rapport.append("🎯 Analyse Thématique:")
        rapport.append(f"   ✅ Réussies: {self.statistiques_globales['analyse_reussie']}")
        rapport.append(f"   ❌ Échouées: {self.statistiques_globales['analyse_echouee']}")
        
        # Moteurs de recherche
        rapport.append("\n🌐 PERFORMANCES MOTEURS DE RECHERCHE:")
        for moteur, count in self.statistiques_globales['moteurs_utilises'].items():
            rapport.append(f"   {moteur}: {count} utilisations")
        
        # Thématiques détectées
        rapport.append("\n🎯 THÉMATIQUES DÉTECTÉES:")
        if self.statistiques_globales['thematiques_stats']:
            for thematique, count in sorted(self.statistiques_globales['thematiques_stats'].items(), 
                                          key=lambda x: x[1], reverse=True):
                pourcentage = (count / len(self.logs_entreprises)) * 100
                rapport.append(f"   {thematique}: {count} entreprises ({pourcentage:.1f}%)")
        else:
            rapport.append("   ⚠️ Aucune thématique détectée")
        
        # Problèmes fréquents
        rapport.append("\n⚠️ PROBLÈMES IDENTIFIÉS:")
        if self.statistiques_globales['problemes_frequents']:
            for probleme, count in sorted(self.statistiques_globales['problemes_frequents'].items(), 
                                        key=lambda x: x[1], reverse=True):
                rapport.append(f"   {probleme}: {count} occurrences")
        else:
            rapport.append("   ✅ Aucun problème majeur identifié")
        
        # Top entreprises problématiques
        rapport.append("\n🚨 ENTREPRISES PROBLÉMATIQUES:")
        entreprises_prob = self.statistiques_globales['entreprises_problematiques'][:5]
        if entreprises_prob:
            for entreprise in entreprises_prob:
                log_ent = self._get_log_entreprise(entreprise)
                if log_ent:
                    rapport.append(f"   • {entreprise}: {len(log_ent.erreurs)} erreurs")
        else:
            rapport.append("   ✅ Aucune entreprise particulièrement problématique")
        
        # Détails par entreprise (échantillon)
        rapport.append("\n📋 DÉTAIL ÉCHANTILLON ENTREPRISES:")
        for i, log_ent in enumerate(self.logs_entreprises[:5], 1):
            rapport.append(f"\n   {i}. {log_ent.nom} ({log_ent.commune})")
            rapport.append(f"      📥 Extraction: {'✅' if log_ent.extraction_ok else '❌'}")
            rapport.append(f"      🔍 Recherche: {'✅' if log_ent.recherche_web_ok else '❌'}")
            rapport.append(f"      🎯 Analyse: {'✅' if log_ent.analyse_thematique_ok else '❌'}")
            
            if log_ent.requetes_generees:
                rapport.append(f"      📝 Requêtes: {len(log_ent.requetes_generees)}")
                rapport.append(f"         Exemple: '{log_ent.requetes_generees[0][:60]}...'")
            
            rapport.append(f"      📊 Résultats: {log_ent.nb_resultats_bruts} bruts → {log_ent.nb_resultats_valides} valides")
            rapport.append(f"      🏆 Score: {log_ent.score_global:.2f}")
            rapport.append(f"      🎯 Thématiques: {', '.join(log_ent.thematiques_detectees) if log_ent.thematiques_detectees else 'Aucune'}")
            
            if log_ent.erreurs:
                rapport.append(f"      ❌ Erreurs: {len(log_ent.erreurs)}")
                for erreur in log_ent.erreurs[:2]:
                    rapport.append(f"         • {erreur}")
        
        # Recommandations
        rapport.append("\n💡 RECOMMANDATIONS:")
        
        # Analyse automatique des problèmes
        taux_reussite = (self.statistiques_globales['entreprises_avec_resultats'] / len(self.logs_entreprises)) * 100
        
        if taux_reussite < 20:
            rapport.append("   🚨 CRITIQUE: Très peu d'entreprises détectées")
            rapport.append("      → Vérifiez la validation de pertinence (trop stricte ?)")
            rapport.append("      → Adaptez les mots-clés aux PME locales")
            rapport.append("      → Testez manuellement quelques requêtes")
        elif taux_reussite < 50:
            rapport.append("   ⚠️ FAIBLE: Détection insuffisante")
            rapport.append("      → Élargissez les sources de recherche") 
            rapport.append("      → Assouplissez les critères de validation")
            rapport.append("      → Enrichissez les mots-clés thématiques")
        elif taux_reussite > 80:
            rapport.append("   🤔 ÉLEVÉ: Possibles faux positifs")
            rapport.append("      → Vérifiez manuellement quelques résultats")
            rapport.append("      → Renforcez la validation de pertinence")
            rapport.append("      → Analysez les scores 1.0 (suspects)")
        else:
            rapport.append("   ✅ CORRECT: Taux de détection raisonnable")
            rapport.append("      → Continuez l'optimisation progressive")
        
        # Recommandations spécifiques selon les erreurs
        if self.statistiques_globales['taux_validation'] < 20:
            rapport.append("   📊 Taux validation très faible:")
            rapport.append("      → Beaucoup de résultats non pertinents trouvés")
            rapport.append("      → Améliorez les requêtes de recherche")
            rapport.append("      → Ciblez mieux les sources locales")
        
        # Moteurs de recherche
        moteurs_stats = self.statistiques_globales['moteurs_utilises']
        if 'simulation' in moteurs_stats and moteurs_stats['simulation'] > len(self.logs_entreprises) * 0.5:
            rapport.append("   🌐 Trop de fallbacks simulation:")
            rapport.append("      → Problème de connexion aux moteurs de recherche")
            rapport.append("      → Vérifiez votre connexion internet")
            rapport.append("      → Testez les moteurs individuellement")
        
        rapport.append("\n" + "=" * 80)
        rapport.append("📄 Log détaillé sauvegardé dans: logs/diagnostic/")
        rapport.append("=" * 80)
        
        # Sauvegarde du rapport
        rapport_text = "\n".join(rapport)
        self._sauvegarder_logs(rapport_text)
        
        return rapport_text
    
    def _get_log_entreprise(self, nom_entreprise: str) -> LogEntreprise:
        """Récupère le log d'une entreprise par son nom"""
        for log_ent in self.logs_entreprises:
            if log_ent.nom == nom_entreprise:
                return log_ent
        return None
    
    def _sauvegarder_logs(self, rapport_text: str):
        """Sauvegarde les logs détaillés"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Rapport texte
        rapport_file = f"logs/diagnostic/rapport_{timestamp}.txt"
        with open(rapport_file, 'w', encoding='utf-8') as f:
            f.write(rapport_text)
        
        # Données JSON détaillées
        logs_data = {
            'statistiques_globales': {
                k: (v.isoformat() if isinstance(v, datetime) else v) 
                for k, v in self.statistiques_globales.items()
            },
            'logs_entreprises': [asdict(log_ent) for log_ent in self.logs_entreprises]
        }
        
        logs_file = f"logs/diagnostic/logs_detailles_{timestamp}.json"
        with open(logs_file, 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, ensure_ascii=False, indent=2)

# INTÉGRATION DANS VOS MODULES EXISTANTS

# ===== MODIFICATION DE VOTRE MAIN.PY =====
def modifier_main_avec_logging():
    """Code à ajouter dans votre main.py"""
    code_integration = '''
# Ajoutez en haut de votre main.py
from scripts.diagnostic_logger import DiagnosticLogger

class VeilleEconomique:
    def __init__(self, config_path="config/parametres.yaml"):
        # Votre code existant...
        
        # ✅ AJOUT DU LOGGER
        self.logger = DiagnosticLogger()
    
    def traiter_echantillon(self, fichier_excel, nb_entreprises=10):
        """Version avec logging détaillé"""
        try:
            print("🔍 Démarrage avec diagnostic détaillé activé")
            
            # 1. Extraction des données
            extracteur = ExtracteurDonnees(fichier_excel)
            entreprises = extracteur.extraire_echantillon(nb_entreprises)
            
            # 2. Recherche web avec logging
            recherche = RechercheWeb(self.periode_recherche)
            resultats_bruts = []
            
            for entreprise in entreprises:
                nom_entreprise = self.logger.log_entreprise_debut(entreprise)
                
                try:
                    resultats = recherche.rechercher_entreprise(entreprise, logger=self.logger)
                    resultats_bruts.append(resultats)
                    
                except Exception as e:
                    self.logger.log_extraction_resultats(nom_entreprise, False, str(e))
                    continue
            
            # 3. Analyse thématique avec logging
            analyseur = AnalyseurThematiques(self.config['thematiques'])
            donnees_enrichies = analyseur.analyser_resultats(resultats_bruts, logger=self.logger)
            
            # 4. Génération des rapports
            generateur = GenerateurRapports()
            rapports_generes = generateur.generer_tous_rapports(donnees_enrichies)
            
            # ✅ GÉNÉRATION DU RAPPORT DE DIAGNOSTIC
            rapport_diagnostic = self.logger.generer_rapport_final()
            print("\\n" + rapport_diagnostic)
            
            return rapports_generes
            
        except Exception as e:
            print(f"❌ ERREUR TRAITEMENT: {str(e)}")
            # Génération du rapport même en cas d'erreur
            rapport_diagnostic = self.logger.generer_rapport_final()
            print("\\n" + rapport_diagnostic)
            return None
'''
    return code_integration

# ===== MODIFICATION DE RECHERCHE_WEB.PY =====
def modifier_recherche_web_avec_logging():
    """Modifications à apporter dans recherche_web.py"""
    code_modification = '''
# Dans votre classe RechercheWeb, modifiez la méthode rechercher_entreprise:

def rechercher_entreprise(self, entreprise: Dict, logger=None) -> Dict:
    """Recherche complète avec logging détaillé"""
    nom_entreprise = entreprise['nom']
    
    # Variables de tracking
    requetes_generees = []
    moteurs_testes = []
    moteur_reussi = ""
    resultats_bruts_count = 0
    resultats_valides_count = 0
    erreurs_recherche = []
    
    resultats = {
        'entreprise': entreprise,
        'timestamp': datetime.now().isoformat(),
        'sources_analysees': [],
        'donnees_thematiques': {},
        'erreurs': []
    }
    
    try:
        # 1. Site web officiel
        if entreprise.get('site_web'):
            try:
                donnees_site = self._analyser_site_officiel(entreprise['site_web'])
                if donnees_site:
                    resultats['donnees_thematiques']['site_officiel'] = donnees_site
                    if logger:
                        logger.log_probleme(nom_entreprise, "Site officiel", "Analysé avec succès")
            except Exception as e:
                erreurs_recherche.append(f"Site officiel: {str(e)}")
        
        # 2. Recherche web générale avec tracking
        try:
            # Génération des requêtes avec logging
            for thematique in ['recrutements', 'evenements', 'innovations', 'vie_entreprise']:
                requetes_thematique = self._construire_requetes_intelligentes(
                    nom_entreprise, entreprise['commune'], thematique
                )
                requetes_generees.extend(requetes_thematique)
                
                # Tentative de recherche avec tracking des moteurs
                for requete in requetes_thematique[:1]:  # 1 requête par thématique
                    resultats_moteur = None
                    
                    # Test des différents moteurs
                    for nom_moteur in ['bing', 'yandex', 'duckduckgo']:
                        moteurs_testes.append(nom_moteur)
                        
                        try:
                            if nom_moteur == 'bing':
                                resultats_moteur = self._rechercher_bing(requete)
                            elif nom_moteur == 'yandex':
                                resultats_moteur = self._rechercher_yandex(requete)
                            else:
                                resultats_moteur = self._rechercher_duckduckgo(requete)
                            
                            if resultats_moteur:
                                moteur_reussi = nom_moteur
                                resultats_bruts_count += len(resultats_moteur)
                                
                                # Validation des résultats
                                resultats_valides = self._valider_pertinence_resultats(
                                    resultats_moteur, nom_entreprise, entreprise['commune'], thematique
                                )
                                resultats_valides_count += len(resultats_valides)
                                
                                if resultats_valides:
                                    resultats['donnees_thematiques'][thematique] = {
                                        'mots_cles_trouves': [thematique],
                                        'urls': [r['url'] for r in resultats_valides if r.get('url')],
                                        'pertinence': len(resultats_valides) * 0.3,
                                        'extraits_textuels': resultats_valides,
                                        'type': f'recherche_{nom_moteur}'
                                    }
                                break  # Moteur réussi, passer à la thématique suivante
                                
                        except Exception as e:
                            erreurs_recherche.append(f"{nom_moteur}: {str(e)}")
                            continue
        
        except Exception as e:
            erreurs_recherche.append(f"Recherche générale: {str(e)}")
        
        # Logging des résultats de recherche
        if logger:
            logger.log_recherche_web(
                nom_entreprise=nom_entreprise,
                requetes=requetes_generees,
                moteurs_testes=moteurs_testes,
                moteur_reussi=moteur_reussi,
                nb_bruts=resultats_bruts_count,
                nb_valides=resultats_valides_count,
                erreurs=erreurs_recherche
            )
        
        return resultats
        
    except Exception as e:
        if logger:
            logger.log_extraction_resultats(nom_entreprise, False, str(e))
        resultats['erreurs'].append(f"Erreur générale: {str(e)}")
        return resultats
'''
    return code_modification

if __name__ == "__main__":
    print("🔍 Système de Diagnostic Détaillé - Veille Économique")
    print("Intégrez ce système dans vos modules pour un diagnostic complet!")