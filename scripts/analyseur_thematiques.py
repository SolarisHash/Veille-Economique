#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'analyse thématique des données de veille économique
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import yaml
from collections import defaultdict, Counter

class AnalyseurThematiques:
    """Analyseur thématique pour classifier les informations trouvées"""
    
    def __init__(self, thematiques_config: List[str]):
        """Initialisation de l'analyseur"""
        self.thematiques = thematiques_config
        self.config = self._charger_config_mots_cles()
        self.seuil_pertinence = 0.3
        self.periode_recente = timedelta(days=30)
        
    def _charger_config_mots_cles(self) -> Dict:
        """Chargement de la configuration des mots-clés"""
        try:
            with open('config/parametres.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('mots_cles', {})
        except FileNotFoundError:
            return self._config_mots_cles_defaut()
            
    def _config_mots_cles_defaut(self) -> Dict:
        """Configuration par défaut des mots-clés"""
        return {
            'evenements': ['porte ouverte', 'conférence', 'salon', 'événement'],
            'recrutements': ['recrutement', 'embauche', 'offre emploi', 'CDI'],
            'vie_entreprise': ['ouverture', 'développement', 'partenariat'],
            'innovations': ['innovation', 'nouveau produit', 'R&D'],
            'exportations': ['export', 'international', 'étranger'],
            'aides_subventions': ['subvention', 'aide', 'financement'],
            'fondation_sponsor': ['fondation', 'sponsor', 'mécénat']
        }
        
    def analyser_resultats(self, resultats_bruts: List[Dict]) -> List[Dict]:
        """Analyse thématique des résultats de recherche"""
        print("🔬 Analyse thématique des résultats")
        
        entreprises_enrichies = []
        
        for i, resultat in enumerate(resultats_bruts, 1):
            print(f"  📊 Analyse {i}/{len(resultats_bruts)}: {resultat['entreprise']['nom']}")
            
            entreprise_enrichie = self._analyser_entreprise(resultat)
            entreprises_enrichies.append(entreprise_enrichie)
            
        print(f"✅ Analyse terminée pour {len(entreprises_enrichies)} entreprises")
        return entreprises_enrichies
        
    def _analyser_entreprise(self, resultat: Dict) -> Dict:
        """Analyse thématique pour une entreprise"""
        entreprise = resultat['entreprise'].copy()
        
        # Initialisation des résultats thématiques
        resultats_thematiques = {
            thematique: {
                'trouve': False,
                'score_pertinence': 0.0,
                'sources': [],
                'details': [],
                'derniere_mention': None
            }
            for thematique in self.thematiques
        }
        
        # Analyse des données par source
        for source, donnees in resultat.get('donnees_thematiques', {}).items():
            if isinstance(donnees, dict):
                self._analyser_source(donnees, source, resultats_thematiques)
                
        # Calcul des scores finaux
        for thematique in resultats_thematiques:
            self._calculer_score_final(resultats_thematiques[thematique])
            
        # Ajout des résultats à l'entreprise
        entreprise['analyse_thematique'] = resultats_thematiques
        entreprise['score_global'] = self._calculer_score_global(resultats_thematiques)
        entreprise['thematiques_principales'] = self._identifier_thematiques_principales(resultats_thematiques)
        entreprise['date_analyse'] = datetime.now().isoformat()
        
        return entreprise
        
    def _analyser_source(self, donnees: Dict, source: str, resultats_thematiques: Dict):
        """Analyse d'une source de données"""
        for thematique, info in donnees.items():
            if thematique in resultats_thematiques:
                
                # Calcul du score de pertinence
                score = self._calculer_score_pertinence(info, source)
                
                if score > self.seuil_pertinence:
                    resultats_thematiques[thematique]['trouve'] = True
                    resultats_thematiques[thematique]['score_pertinence'] = max(
                        resultats_thematiques[thematique]['score_pertinence'], score
                    )
                    
                    # Ajout de la source
                    if source not in resultats_thematiques[thematique]['sources']:
                        resultats_thematiques[thematique]['sources'].append(source)
                        
                    # Ajout des détails
                    detail = {
                        'source': source,
                        'score': score,
                        'informations': self._extraire_informations(info),
                        'timestamp': datetime.now().isoformat()
                    }
                    resultats_thematiques[thematique]['details'].append(detail)
                    
    def _calculer_score_pertinence(self, info: Dict, source: str) -> float:
        """Calcul du score de pertinence d'une information"""
        score_base = 0.0
        
        # Score basé sur le nombre de mots-clés trouvés
        if 'mots_cles_trouves' in info:
            nb_mots_cles = len(info['mots_cles_trouves'])
            score_base = min(nb_mots_cles * 0.2, 1.0)
            
        # Score basé sur la pertinence définie
        if 'pertinence' in info:
            score_base = max(score_base, info['pertinence'])
            
        # Score basé sur la probabilité (pour les simulations)
        if 'probabilite' in info:
            score_base = max(score_base, info['probabilite'])
            
        # Bonus selon la source
        bonus_source = self._get_bonus_source(source)
        
        # Bonus pour les informations récentes
        bonus_recence = self._get_bonus_recence(info)
        
        score_final = min(score_base + bonus_source + bonus_recence, 1.0)
        return score_final
        
    def _get_bonus_source(self, source: str) -> float:
        """Bonus selon la fiabilité de la source"""
        bonus = {
            'site_officiel': 0.3,
            'presse_locale': 0.2,
            'web_general': 0.1,
            'reseaux_sociaux': 0.05
        }
        return bonus.get(source, 0.0)
        
    def _get_bonus_recence(self, info: Dict) -> float:
        """Bonus pour les informations récentes"""
        # Pour l'instant, bonus fixe - à améliorer avec vraies dates
        return 0.1
        
    def _extraire_informations(self, info: Dict) -> Dict:
        """Extraction des informations pertinentes"""
        informations = {}
        
        # Mots-clés trouvés
        if 'mots_cles_trouves' in info:
            informations['mots_cles'] = info['mots_cles_trouves']
            
        # URL source
        if 'url' in info:
            informations['url'] = info['url']
            
        # Type d'information
        if 'type' in info:
            informations['type'] = info['type']
            
        # Extrait de contenu
        if 'extrait' in info:
            informations['extrait'] = info['extrait'][:200] + '...'
            
        return informations
        
    def _calculer_score_final(self, resultat_thematique: Dict):
        """Calcul du score final pour une thématique"""
        if not resultat_thematique['trouve']:
            return
            
        # Bonus pour sources multiples
        nb_sources = len(resultat_thematique['sources'])
        bonus_sources = min(nb_sources * 0.1, 0.3)
        
        # Ajustement du score
        resultat_thematique['score_pertinence'] = min(
            resultat_thematique['score_pertinence'] + bonus_sources, 1.0
        )
        
        # Détermination du niveau de confiance
        score = resultat_thematique['score_pertinence']
        if score >= 0.8:
            resultat_thematique['niveau_confiance'] = 'Élevé'
        elif score >= 0.5:
            resultat_thematique['niveau_confiance'] = 'Moyen'
        else:
            resultat_thematique['niveau_confiance'] = 'Faible'
            
    def _calculer_score_global(self, resultats_thematiques: Dict) -> float:
        """Calcul du score global d'activité de l'entreprise"""
        scores = [
            res['score_pertinence'] for res in resultats_thematiques.values()
            if res['trouve']
        ]
        
        if not scores:
            return 0.0
            
        # Moyenne pondérée avec bonus pour diversité thématique
        score_moyen = sum(scores) / len(scores)
        bonus_diversite = len(scores) * 0.05
        
        return min(score_moyen + bonus_diversite, 1.0)
        
    def _identifier_thematiques_principales(self, resultats_thematiques: Dict) -> List[str]:
        """Identification des thématiques principales"""
        thematiques_trouvees = [
            (thematique, res['score_pertinence'])
            for thematique, res in resultats_thematiques.items()
            if res['trouve']
        ]
        
        # Tri par score décroissant
        thematiques_trouvees.sort(key=lambda x: x[1], reverse=True)
        
        # Retour des 3 principales
        return [thematique for thematique, _ in thematiques_trouvees[:3]]
        
    def generer_rapport_analyse(self, entreprises_enrichies: List[Dict]) -> Dict:
        """Génération d'un rapport d'analyse global"""
        rapport = {
            'timestamp': datetime.now().isoformat(),
            'nb_entreprises_analysees': len(entreprises_enrichies),
            'statistiques_thematiques': {},
            'entreprises_plus_actives': [],
            'resume_par_commune': {}
        }
        
        # Statistiques par thématique
        for thematique in self.thematiques:
            nb_entreprises = sum(
                1 for entreprise in entreprises_enrichies
                if entreprise['analyse_thematique'][thematique]['trouve']
            )
            
            rapport['statistiques_thematiques'][thematique] = {
                'nb_entreprises': nb_entreprises,
                'pourcentage': (nb_entreprises / len(entreprises_enrichies)) * 100
            }
            
        # Entreprises les plus actives
        entreprises_scores = [
            (entreprise['nom'], entreprise['score_global'])
            for entreprise in entreprises_enrichies
        ]
        entreprises_scores.sort(key=lambda x: x[1], reverse=True)
        rapport['entreprises_plus_actives'] = entreprises_scores[:5]
        
        # Résumé par commune
        communes = defaultdict(list)
        for entreprise in entreprises_enrichies:
            communes[entreprise['commune']].append(entreprise)
            
        for commune, entreprises in communes.items():
            rapport['resume_par_commune'][commune] = {
                'nb_entreprises': len(entreprises),
                'score_moyen': sum(e['score_global'] for e in entreprises) / len(entreprises),
                'thematiques_dominantes': self._analyser_thematiques_commune(entreprises)
            }
            
        return rapport
        
    def _analyser_thematiques_commune(self, entreprises: List[Dict]) -> List[str]:
        """Analyse des thématiques dominantes par commune"""
        compteur_thematiques = Counter()
        
        for entreprise in entreprises:
            for thematique in entreprise['thematiques_principales']:
                compteur_thematiques[thematique] += 1
                
        return [thematique for thematique, _ in compteur_thematiques.most_common(3)]