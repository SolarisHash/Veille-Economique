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
        self.seuil_pertinence = 0.2
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
        
    def analyser_resultats(self, resultats_bruts: List[Dict], logger=None) -> List[Dict]:
        """Analyse thématique avec logging détaillé"""
        print("🔬 Analyse thématique des résultats")
        
        entreprises_enrichies = []
        
        for i, resultat in enumerate(resultats_bruts, 1):
            nom_entreprise = resultat['entreprise']['nom']
            print(f"  📊 Analyse {i}/{len(resultats_bruts)}: {nom_entreprise}")
            
            try:
                entreprise_enrichie = self._analyser_entreprise(resultat)
                entreprises_enrichies.append(entreprise_enrichie)
                
                # ✅ LOGGING ANALYSE THÉMATIQUE
                if logger:
                    thematiques_detectees = entreprise_enrichie.get('thematiques_principales', [])
                    score_global = entreprise_enrichie.get('score_global', 0.0)
                    
                    logger.log_analyse_thematique(
                        nom_entreprise=nom_entreprise,
                        thematiques=thematiques_detectees,
                        score=score_global
                    )
                    
                    # Logging de problèmes spécifiques
                    if score_global == 1.0:
                        logger.log_probleme(nom_entreprise, "Score suspect", "Score parfait 1.0 - possible faux positif")
                    elif score_global == 0.0:
                        logger.log_probleme(nom_entreprise, "Aucune détection", "Aucune thématique détectée")
                
            except Exception as e:
                print(f"    ❌ Erreur analyse {nom_entreprise}: {e}")
                if logger:
                    logger.log_analyse_thematique(nom_entreprise, [], 0.0, erreurs=[str(e)])
                continue
        
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
        """Analyse d'une source de données avec capture complète des informations"""
        print(f"    🔍 Analyse source: {source}")
        
        for thematique, info in donnees.items():
            if thematique in resultats_thematiques:
                print(f"      🎯 Analyse thématique: {thematique}")
                
                # Calcul du score de pertinence
                score = self._calculer_score_pertinence(info, source)
                print(f"         💯 Score calculé: {score:.2f}")
                
                if score > self.seuil_pertinence:
                    print(f"         ✅ Score > seuil ({self.seuil_pertinence})")
                    
                    resultats_thematiques[thematique]['trouve'] = True
                    resultats_thematiques[thematique]['score_pertinence'] = max(
                        resultats_thematiques[thematique]['score_pertinence'], score
                    )
                    
                    # Ajout de la source
                    if source not in resultats_thematiques[thematique]['sources']:
                        resultats_thematiques[thematique]['sources'].append(source)
                        
                    # ✅ EXTRACTION COMPLÈTE DES INFORMATIONS
                    informations_extraites = self._extraire_informations_completes(info, source)
                    
                    # Ajout des détails avec TOUTES les informations
                    detail = {
                        'source': source,
                        'score': score,
                        'informations': informations_extraites,  # ← INFORMATIONS COMPLÈTES
                        'timestamp': datetime.now().isoformat(),
                        'raw_data': info  # ← DONNÉES BRUTES pour debug
                    }
                    resultats_thematiques[thematique]['details'].append(detail)
                    
                    print(f"         📊 Informations extraites: {len(informations_extraites)} clés")
                    print(f"         📋 Détails ajoutés: {list(informations_extraites.keys())}")
                else:
                    print(f"         ⚪ Score trop faible ({score:.2f} <= {self.seuil_pertinence})")
    
    def _extraire_informations_completes(self, info: Dict, source: str) -> Dict:
        """Extraction COMPLÈTE des informations avec tous les détails textuels"""
        informations = {
            'source': source,
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Mots-clés trouvés
        if 'mots_cles_trouves' in info:
            informations['mots_cles'] = info['mots_cles_trouves']
            print(f"           🔑 Mots-clés: {info['mots_cles_trouves']}")
        
        # 2. URL source
        if 'url' in info:
            informations['url'] = info['url']
            print(f"           🔗 URL: {info['url']}")
        
        # 3. Type d'information
        if 'type' in info:
            informations['type'] = info['type']
        
        # 4. ✅ EXTRAITS TEXTUELS (le plus important!)
        if 'extraits_textuels' in info:
            informations['extraits_textuels'] = info['extraits_textuels']
            print(f"           📄 Extraits textuels: {len(info['extraits_textuels'])}")
            
            # Debug des extraits
            for i, extrait in enumerate(info['extraits_textuels'][:2]):
                titre = extrait.get('titre', 'Sans titre')
                description = extrait.get('description', 'Sans description')
                print(f"              {i+1}. {titre[:40]} - {description[:60]}...")
        
        # 5. ✅ EXTRAITS CONTEXTUELS (site officiel)
        if 'extraits_contextuels' in info:
            informations['extraits_contextuels'] = info['extraits_contextuels']
            print(f"           🎯 Extraits contextuels: {len(info['extraits_contextuels'])}")
            
            for i, extrait in enumerate(info['extraits_contextuels'][:2]):
                mot_cle = extrait.get('mot_cle', 'N/A')
                contexte = extrait.get('contexte', 'N/A')
                print(f"              {i+1}. [{mot_cle}] {contexte[:50]}...")
        
        # 6. ✅ RÉSUMÉ DE CONTENU
        if 'resume_contenu' in info:
            informations['resume_contenu'] = info['resume_contenu']
            print(f"           📝 Résumé: {info['resume_contenu'][:60]}...")
        
        # 7. ✅ URLS COLLECTÉES
        urls_collectees = []
        if 'urls' in info:
            urls_collectees.extend(info['urls'])
        if 'url' in info:
            urls_collectees.append(info['url'])
        
        if urls_collectees:
            informations['urls_sources'] = list(set(urls_collectees))  # Dédupliqué
            print(f"           🌐 URLs: {len(urls_collectees)} collectées")
        
        # 8. ✅ PERTINENCE ET MÉTADONNÉES
        if 'pertinence' in info:
            informations['score_pertinence'] = info['pertinence']
        
        # 9. ✅ TOUS LES AUTRES CHAMPS DISPONIBLES
        for cle, valeur in info.items():
            if cle not in informations and cle not in ['raw_data']:
                informations[cle] = valeur
        
        print(f"           ✅ Total informations extraites: {len(informations)} champs")
        return informations
                    
    def _calculer_score_pertinence(self, info: Dict, source: str) -> float:
        """Calcul du score de pertinence avec validation stricte"""
        score_base = 0.0
        
        # Score basé sur le nombre de mots-clés trouvés
        if 'mots_cles_trouves' in info:
            nb_mots_cles = len(info['mots_cles_trouves'])
            # Score plus conservateur
            score_base = min(nb_mots_cles * 0.15, 0.6)  # Maximum 0.6 au lieu de 1.0
            
        # Score basé sur la pertinence définie
        if 'pertinence' in info:
            score_base = max(score_base, info['pertinence'])
            
        # ✅ VALIDATION ANTI-FAUX POSITIFS
        if 'extraits_textuels' in info:
            score_validite = self._valider_qualite_extraits(info['extraits_textuels'])
            score_base *= score_validite  # Réduction si extraits peu pertinents
            
        # Bonus selon la source (réduits)
        bonus_source = self._get_bonus_source_realiste(source)
        
        # Bonus pour les informations récentes (réduit)
        bonus_recence = self._get_bonus_recence(info) * 0.5  # Divisé par 2
        
        score_final = min(score_base + bonus_source + bonus_recence, 0.8)  # Maximum 0.8
        return score_final
    
    def _valider_qualite_extraits(self, extraits_textuels: List[Dict]) -> float:
        """Validation de la qualité des extraits trouvés"""
        if not extraits_textuels:
            return 0.1
        
        score_qualite = 1.0
        
        for extrait in extraits_textuels:
            titre = extrait.get('titre', '').lower()
            description = extrait.get('description', '').lower()
            url = extrait.get('url', '').lower()
            
            contenu = f"{titre} {description} {url}"
            
            # Pénalités pour contenu non pertinent
            penalites = [
                ('forum.wordreference.com', -0.8),  # Forums linguistiques
                ('wikipedia.org', -0.3),            # Wikipédia généraliste
                ('dictionary', -0.6),               # Dictionnaires
                ('translation', -0.6),              # Traductions
                ('grammar', -0.7),                  # Grammaire
                ('linguistique', -0.7),             # Linguistique
                ('definition', -0.5),               # Définitions
                ('much or many', -0.9),             # Discussions grammaticales
                ('is/are', -0.9),                   # Questions grammaticales
            ]
            
            for terme_penalite, reduction in penalites:
                if terme_penalite in contenu:
                    score_qualite += reduction
                    print(f"         ⚠️  Pénalité {terme_penalite}: {reduction}")
            
            # Bonus pour contenu pertinent
            bonus = [
                ('.fr', 0.1),                       # Sites français
                ('entreprise', 0.1),                # Contexte entreprise
                ('emploi', 0.2),                    # Emploi
                ('recrutement', 0.2),               # Recrutement
                ('innovation', 0.15),               # Innovation
                ('développement', 0.1),             # Développement
                ('économie', 0.1),                  # Économie
            ]
            
            for terme_bonus, augmentation in bonus:
                if terme_bonus in contenu:
                    score_qualite += augmentation
        
        # Score final entre 0.1 et 1.0
        return max(0.1, min(score_qualite, 1.0))
    
    def _get_bonus_source_realiste(self, source: str) -> float:
        """Bonus réduits selon la fiabilité de la source"""
        bonus = {
            'site_officiel': 0.2,      # Réduit de 0.3 à 0.2
            'presse_locale': 0.15,     # Réduit de 0.2 à 0.15
            'web_general': 0.05,       # Réduit de 0.1 à 0.05
            'enrichissement_insee': 0.1 # Nouveau: données INSEE enrichies
        }
        return bonus.get(source, 0.0)
    
    def _calculer_score_global(self, resultats_thematiques: Dict) -> float:
        """Calcul du score global avec pondération réaliste"""
        scores_valides = []
        
        for thematique, res in resultats_thematiques.items():
            if res['trouve'] and res['score_pertinence'] > 0.3:  # Seuil plus élevé
                scores_valides.append(res['score_pertinence'])
        
        if not scores_valides:
            return 0.0
            
        # Moyenne pondérée plus conservative
        score_moyen = sum(scores_valides) / len(scores_valides)
        
        # Bonus diversité réduit
        bonus_diversite = min(len(scores_valides) * 0.02, 0.1)  # Maximum 0.1
        
        # Score final plus réaliste
        score_final = min(score_moyen + bonus_diversite, 0.8)  # Maximum 0.8
        
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