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
        """Initialisation de l'analyseur avec TOUS les mots-clés"""
        self.thematiques = thematiques_config
        self.config = self._charger_config_mots_cles()
        self.seuil_pertinence = 0.5  # ✅ SEUIL ABAISSÉ
        self.periode_recente = timedelta(days=30)
        
        # ✅ AJOUT CRITIQUE : Définition des mots-clés thématiques
        self.thematiques_mots_cles = {
            'evenements': [
                'porte ouverte', 'portes ouvertes', 'conférence', 'salon', 'forum',
                'rencontre', 'événement', 'manifestation', 'colloque', 'séminaire',
                'découvrir', 'venez découvrir'
            ],
            'recrutements': [
                'recrutement', 'nous recrutons', 'embauche', 'recrute', 'offre emploi',
                'offres emploi', 'CDI', 'CDD', 'stage', 'alternance', 'apprentissage',
                'carrière', 'poste', 'cherchons', 'rejoindre notre équipe'
            ],
            'vie_entreprise': [
                'ouverture', 'fermeture', 'déménagement', 'implantation', 'développement',
                'expansion', 'partenariat', 'collaboration', 'fusion', 'acquisition',
                'restructuration', 'rachat'
            ],
            'innovations': [
                'amélioration', 'modernisation', 'innovation', 'développe', 'nouveau',
                'nouveau produit', 'nouveau service', 'lancement', 'brevets', 'R&D',
                'recherche développement', 'technologie', 'prototype'
            ],
            'exportations': [
                'export', 'exportation', 'international', 'étranger', 'marché international',
                'contrat export', 'développement international', 'commerce extérieur'
            ],
            'aides_subventions': [
                'subvention', 'aide', 'financement', 'soutien', 'crédit',
                'subventionné', 'aidé', 'prêt', 'investissement public', 'dispositif d\'aide'
            ],
            'fondation_sponsor': [
                'fondation', 'sponsor', 'sponsoring', 'mécénat', 'partenaire',
                'soutien', 'dons', 'charitable', 'solidarité', 'engagement social'
            ]
        }
            
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

    def _analyser_entreprise(self, resultat: Dict) -> Dict:
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
        
        # Analyse des données par thématique
        donnees_thematiques = resultat.get('donnees_thematiques', {})
        
        print(f"    📋 Données reçues pour {entreprise.get('nom', 'N/A')}: {list(donnees_thematiques.keys())}")
        
        for thematique, donnees in donnees_thematiques.items():
            if thematique in self.thematiques:
                print(f"    🎯 Analyse thématique directe: {thematique}")
                
                # ✅ INITIALISATION OBLIGATOIRE AU DÉBUT
                score = 0.0
                
                try:
                    # Gestion tous les cas possibles
                    if isinstance(donnees, dict):
                        print(f"         📊 Format dict détecté")
                        score = self._calculer_score_avec_vos_donnees(donnees, thematique)
                        
                    elif isinstance(donnees, list):
                        print(f"         📋 Format liste détecté: {len(donnees)} éléments")
                        if donnees:  # Liste non vide
                            donnees_converties = self._convertir_liste_vers_dict(donnees, thematique)
                            score = self._calculer_score_avec_vos_donnees(donnees_converties, thematique)
                        else:  # Liste vide
                            print(f"         ⚠️ Liste vide")
                            score = 0.0
                            
                    else:
                        print(f"         ⚠️ Format données inattendu: {type(donnees)}")
                        score = 0.0
                    
                    # DEBUG obligatoire
                    print(f"DEBUG: Score calculé {score:.3f} vs seuil {self.seuil_pertinence}")
                    
                    # Test du seuil
                    if score > self.seuil_pertinence:
                        print(f"         ✅ Thématique {thematique} VALIDÉE !")
                        
                        resultats_thematiques[thematique]['trouve'] = True
                        resultats_thematiques[thematique]['score_pertinence'] = score
                        if 'web_general' not in resultats_thematiques[thematique]['sources']:
                            resultats_thematiques[thematique]['sources'].append('web_general')
                        
                        # Extraction des informations
                        if isinstance(donnees, dict):
                            informations_extraites = self._extraire_infos_format_reel(donnees)
                        elif isinstance(donnees, list) and donnees:
                            donnees_conv = self._convertir_liste_vers_dict(donnees, thematique)
                            informations_extraites = self._extraire_infos_format_reel(donnees_conv)
                        else:
                            informations_extraites = {'type': 'donnees_minimales'}
                        
                        detail = {
                            'source': 'web_general',
                            'score': score,
                            'informations': informations_extraites,
                            'timestamp': datetime.now().isoformat(),
                            'raw_data': donnees
                        }
                        resultats_thematiques[thematique]['details'].append(detail)
                    else:
                        print(f"         ❌ Score trop faible: {score:.3f} <= {self.seuil_pertinence}")
                        
                except Exception as e:
                    print(f"         ❌ Erreur calcul score {thematique}: {e}")
                    score = 0.0  # Score par défaut en cas d'erreur
                    continue
        
        # Calcul des scores finaux
        for thematique in resultats_thematiques:
            self._calculer_score_final(resultats_thematiques[thematique])
        
        # Ajout des résultats à l'entreprise
        entreprise['analyse_thematique'] = resultats_thematiques
        entreprise['score_global'] = self._calculer_score_global(resultats_thematiques)
        entreprise['thematiques_principales'] = self._identifier_thematiques_principales(resultats_thematiques)
        entreprise['date_analyse'] = datetime.now().isoformat()
        
        print(f"    🏆 Score global final: {entreprise['score_global']:.3f}")
        print(f"    🎯 Thématiques principales: {entreprise['thematiques_principales']}")
        
        return entreprise

    def _convertir_liste_vers_dict(self, donnees_liste: List, thematique: str) -> Dict:
        """✅ NOUVEAU : Conversion d'une liste de données vers le format dict attendu"""
        try:
            if not donnees_liste:
                return {}
            
            print(f"           🔄 Conversion liste de {len(donnees_liste)} éléments")
            
            # Initialisation du dict de sortie
            donnees_converties = {
                'mots_cles_trouves': [thematique],
                'pertinence': 0.0,
                'extraits_textuels': [],
                'urls': [],
                'type': 'conversion_liste'
            }
            
            # Traitement de chaque élément de la liste
            for i, element in enumerate(donnees_liste):
                try:
                    if isinstance(element, dict):
                        # Élément déjà au bon format
                        if 'titre' in element or 'description' in element:
                            donnees_converties['extraits_textuels'].append(element)
                            if 'url' in element and element['url']:
                                donnees_converties['urls'].append(element['url'])
                        
                        # Extraction des mots-clés si présents
                        if 'mots_cles_trouves' in element:
                            donnees_converties['mots_cles_trouves'].extend(element['mots_cles_trouves'])
                        
                    elif isinstance(element, str):
                        # Conversion string → dict
                        extrait_string = {
                            'titre': f"Information {thematique} {i+1}",
                            'description': element[:200] if len(element) > 200 else element,
                            'url': '',
                            'type': 'conversion_string'
                        }
                        donnees_converties['extraits_textuels'].append(extrait_string)
                    
                    else:
                        # Type inattendu → conversion sécurisée
                        print(f"           ⚠️ Type inattendu dans liste: {type(element)}")
                        extrait_generique = {
                            'titre': f"Données {thematique} {i+1}",
                            'description': str(element)[:200],
                            'url': '',
                            'type': 'conversion_generique'
                        }
                        donnees_converties['extraits_textuels'].append(extrait_generique)
                        
                except Exception as e:
                    print(f"           ❌ Erreur conversion élément {i}: {e}")
                    continue
            
            # Calcul de la pertinence basée sur le nombre d'éléments valides
            nb_extraits_valides = len(donnees_converties['extraits_textuels'])
            donnees_converties['pertinence'] = min(nb_extraits_valides * 0.2, 0.8)
            
            # Déduplication des URLs
            donnees_converties['urls'] = list(set(donnees_converties['urls']))
            
            # Déduplication des mots-clés
            donnees_converties['mots_cles_trouves'] = list(set(donnees_converties['mots_cles_trouves']))
            
            print(f"           ✅ Conversion réussie: {nb_extraits_valides} extraits, pertinence {donnees_converties['pertinence']:.2f}")
            
            return donnees_converties
            
        except Exception as e:
            print(f"           ❌ Erreur conversion liste: {e}")
            return {}

    # ✅ MÉTHODE DE DEBUG pour identifier le format exact des données

    def _calculer_score_avec_vos_donnees(self, donnees: Dict, thematique: str) -> float:
        """✅ Calcul de score adapté au format exact de vos données"""
        score_total = 0.0
        
        print(f"           🐛 DEBUG: Analyse {thematique}")
        print(f"           📊 Données reçues: {list(donnees.keys())}")
        
        print(f"           📊 Analyse des données: {list(donnees.keys())}")
        
        # 1. Score basé sur la pertinence calculée par votre système
        if 'pertinence' in donnees:
            pertinence_brute = donnees['pertinence']
            # Normalisation : vos scores peuvent être > 1.0
            score_pertinence = min(pertinence_brute, 1.0)
            score_total += score_pertinence
            print(f"           🎯 Pertinence: {pertinence_brute} → {score_pertinence}")
        
        # 2. Score basé sur les mots-clés trouvés
        if 'mots_cles_trouves' in donnees:
            mots_cles = donnees['mots_cles_trouves']
            if isinstance(mots_cles, list) and len(mots_cles) > 0:
                score_mots_cles = min(len(mots_cles) * 0.15, 0.4)
                score_total += score_mots_cles
                print(f"           🔑 Mots-clés ({len(mots_cles)}): +{score_mots_cles}")
        
        # 3. Score basé sur les extraits textuels
        if 'extraits_textuels' in donnees:
            extraits = donnees['extraits_textuels']
            if isinstance(extraits, list) and len(extraits) > 0:
                score_extraits = self._analyser_extraits_vos_donnees(extraits, thematique)
                score_total += score_extraits
                print(f"           📄 Extraits ({len(extraits)}): +{score_extraits}")
        
        # 4. Bonus pour URLs multiples
        if 'urls' in donnees:
            urls = donnees['urls']
            if isinstance(urls, list) and len(urls) > 1:
                bonus_urls = min(len(urls) * 0.05, 0.2)
                score_total += bonus_urls
                print(f"           🔗 URLs ({len(urls)}): +{bonus_urls}")
        
        # Score final avec limite réaliste
        score_final = min(score_total, 0.9)
        print(f"           🏆 Score final: {score_final}")
        
        return score_final

    def _analyser_extraits_vos_donnees(self, extraits: List[Dict], thematique: str) -> float:
        """✅ CORRIGÉ : Analyse des extraits dans votre format exact"""
        if not extraits:
            return 0.0
        
        score_extraits = 0.0
        mots_cles_thematique = self.thematiques_mots_cles.get(thematique, [])
        
        print(f"             📋 Analyse de {len(extraits)} extraits pour {thematique}")
        
        for i, extrait in enumerate(extraits[:3]):  # Top 3 extraits
            if not isinstance(extrait, dict):
                continue
            
            # Construction du texte à analyser
            texte_parts = []
            for champ in ['titre', 'description', 'extrait_complet']:
                if champ in extrait and isinstance(extrait[champ], str):
                    texte_parts.append(extrait[champ])
            
            texte_complet = ' '.join(texte_parts).lower()
            
            if len(texte_complet) > 10:  # Texte significatif
                # Comptage des mots-clés thématiques
                mots_trouves = [mot for mot in mots_cles_thematique if mot.lower() in texte_complet]
                
                if mots_trouves:
                    score_extrait = min(len(mots_trouves) * 0.1, 0.3)
                    score_extraits += score_extrait
                    print(f"               {i+1}. {len(mots_trouves)} mots-clés → +{score_extrait}")
                else:
                    # Bonus minimal pour contenu pertinent
                    if any(terme in texte_complet for terme in ['entreprise', 'société', 'activité', 'service']):
                        score_extraits += 0.05
                        print(f"               {i+1}. Contenu général → +0.05")
        
        return min(score_extraits, 0.5)

    def _extraire_infos_format_reel(self, donnees: Dict) -> Dict:
        """✅ CORRIGÉ : Extraction d'informations selon votre format de données"""
        informations = {
            'timestamp': datetime.now().isoformat()
        }
        
        # Extraction directe des champs
        champs_directs = ['mots_cles_trouves', 'urls', 'pertinence', 'type']
        
        for champ in champs_directs:
            if champ in donnees:
                informations[champ] = donnees[champ]
        
        # Traitement des extraits textuels
        if 'extraits_textuels' in donnees:
            extraits = donnees['extraits_textuels']
            if isinstance(extraits, list) and len(extraits) > 0:
                informations['extraits_textuels'] = extraits[:3]  # Top 3
                
                # Résumés
                titres = []
                descriptions = []
                urls_extraits = []
                
                for extrait in extraits[:3]:
                    if isinstance(extrait, dict):
                        if 'titre' in extrait and extrait['titre']:
                            titres.append(extrait['titre'])
                        if 'description' in extrait and extrait['description']:
                            descriptions.append(extrait['description'])
                        if 'url' in extrait and extrait['url']:
                            urls_extraits.append(extrait['url'])
                
                if titres:
                    informations['resume_titres'] = ' | '.join(titres)
                if descriptions:
                    informations['resume_descriptions'] = ' | '.join(descriptions[:2])
                if urls_extraits:
                    informations['urls_sources'] = urls_extraits
        
        # Métadonnées
        informations['nb_champs_remplis'] = len([v for v in informations.values() if v])
        informations['source_data_format'] = 'format_reel_detecte'
        
        return informations

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
        """Calcule un score global d'activité de l'entreprise.

        Seules les thématiques considérées comme suffisamment pertinentes
        (score > 0.3) sont prises en compte. La moyenne de ces scores est
        ensuite augmentée d'un léger bonus reflétant la diversité des
        thématiques détectées, le tout étant plafonné à ``0.8`` afin de
        réserver une marge pour d'éventuels enrichissements externes
        (par exemple l'analyse de réseaux sociaux).
        """

        scores_valides = [
            res['score_pertinence']
            for res in resultats_thematiques.values()
            if res['trouve'] and res['score_pertinence'] > 0.3
        ]

        if not scores_valides:
            return 0.0

        score_moyen = sum(scores_valides) / len(scores_valides)

        # Bonus de 0.02 par thématique pertinente (maximum 0.1)
        bonus_diversite = min(len(scores_valides) * 0.02, 0.1)

        return min(score_moyen + bonus_diversite, 0.8)
    
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

    def _analyser_extraits_pour_thematique(self, extraits: List, thematique: str) -> float:
        """✅ NOUVEAU : Analyse spécifique des extraits pour une thématique"""
        if not extraits:
            return 0.0
        
        mots_cles_thematique = self.config.get(thematique, [])
        if not mots_cles_thematique:
            return 0.0
        
        score_total = 0.0
        
        for extrait in extraits[:5]:  # Analyser max 5 extraits
            texte_extrait = ""
            
            # Extraction du texte selon la structure
            if isinstance(extrait, dict):
                texte_extrait = f"{extrait.get('titre', '')} {extrait.get('description', '')} {extrait.get('extrait_complet', '')}"
            elif isinstance(extrait, str):
                texte_extrait = extrait
            else:
                continue
            
            texte_extrait = texte_extrait.lower()
            
            # Comptage des mots-clés thématiques trouvés
            mots_trouves = [mot for mot in mots_cles_thematique if mot.lower() in texte_extrait]
            
            if mots_trouves:
                score_extrait = min(len(mots_trouves) * 0.15, 0.4)
                score_total += score_extrait
                print(f"             📋 Extrait: {len(mots_trouves)} mots-clés → {score_extrait:.2f}")
        
        return min(score_total, 0.7)

    def _analyser_contenu_thematique(self, contenu: str, thematique: str) -> float:
        """✅ NOUVEAU : Analyse thématique directe du contenu textuel"""
        if not contenu or len(contenu) < 10:
            return 0.0
        
        contenu_lower = contenu.lower()
        mots_cles_thematique = self.config.get(thematique, [])
        
        score_contenu = 0.0
        
        for mot_cle in mots_cles_thematique:
            if mot_cle.lower() in contenu_lower:
                score_contenu += 0.1
                print(f"             🎯 Mot-clé '{mot_cle}' trouvé")
        
        return min(score_contenu, 0.5)

    def _extraire_contenu_textuel(self, donnees: Dict) -> str:
        """✅ NOUVEAU : Extraction du contenu textuel depuis les données"""
        contenu_parts = []
        
        # Sources possibles de contenu textuel
        champs_texte = [
            'titre', 'description', 'extrait_complet', 'resume_contenu',
            'texte', 'contenu', 'snippet'
        ]
        
        for champ in champs_texte:
            if champ in donnees and isinstance(donnees[champ], str):
                contenu_parts.append(donnees[champ])
        
        # Extraction depuis les extraits textuels
        if 'extraits_textuels' in donnees:
            extraits = donnees['extraits_textuels']
            if isinstance(extraits, list):
                for extrait in extraits[:3]:  # Max 3 extraits
                    if isinstance(extrait, dict):
                        for champ in champs_texte:
                            if champ in extrait and isinstance(extrait[champ], str):
                                contenu_parts.append(extrait[champ])
        
        return ' '.join(contenu_parts)

    def _extraire_informations_adaptees(self, donnees: Dict, source: str) -> Dict:
        """✅ NOUVEAU : Extraction d'informations adaptée à vos structures de données"""
        informations = {
            'source': source,
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Extraction des champs standard
        champs_standards = [
            'mots_cles_trouves', 'pertinence', 'url', 'type', 'urls',
            'titre', 'description', 'extrait_complet'
        ]
        
        for champ in champs_standards:
            if champ in donnees:
                informations[champ] = donnees[champ]
        
        # 2. ✅ Gestion spéciale des extraits textuels
        if 'extraits_textuels' in donnees:
            extraits = donnees['extraits_textuels']
            if isinstance(extraits, list) and len(extraits) > 0:
                informations['extraits_textuels'] = extraits[:3]  # Top 3
                
                # Résumé des extraits
                titres = []
                descriptions = []
                
                for extrait in extraits[:3]:
                    if isinstance(extrait, dict):
                        if 'titre' in extrait:
                            titres.append(extrait['titre'])
                        if 'description' in extrait:
                            descriptions.append(extrait['description'])
                
                if titres:
                    informations['resume_titres'] = ' | '.join(titres)
                if descriptions:
                    informations['resume_descriptions'] = ' | '.join(descriptions)
        
        # 3. ✅ Métadonnées supplémentaires
        informations['nb_champs_remplis'] = len([v for v in informations.values() if v])
        informations['qualite_donnees'] = 'elevee' if len(informations) > 5 else 'moyenne'
        
        return informations

    # ✅ MÉTHODE PRINCIPALE CORRIGÉE pour résoudre le problème de structure
    def analyser_resultats(self, resultats_bruts: List[Dict], logger=None) -> List[Dict]:
        """✅ VERSION FINALE CORRIGÉE : Analyse adaptée au format exact de vos données"""
        print("🔬 Analyse thématique des résultats (VERSION CORRIGÉE FINALE)")
        
        entreprises_enrichies = []
        
        for i, resultat in enumerate(resultats_bruts, 1):
            nom_entreprise = resultat.get('entreprise', {}).get('nom', f'Entreprise_{i}')
            print(f"  📊 Analyse {i}/{len(resultats_bruts)}: {nom_entreprise}")
            
            try:
                # Vérification des données
                donnees_thematiques = resultat.get('donnees_thematiques', {})
                
                if not donnees_thematiques:
                    print(f"    ⚠️ Aucune donnée thématique")
                    # Structure minimale
                    entreprise_base = resultat.get('entreprise', {})
                    entreprise_base.update({
                        'analyse_thematique': {thematique: {'trouve': False, 'score_pertinence': 0.0} for thematique in self.thematiques},
                        'score_global': 0.0,
                        'thematiques_principales': [],
                        'date_analyse': datetime.now().isoformat()
                    })
                    entreprises_enrichies.append(entreprise_base)
                    continue
                
                # Analyse avec la méthode corrigée
                entreprise_enrichie = self._analyser_entreprise(resultat)
                entreprises_enrichies.append(entreprise_enrichie)
                
                # Logging des résultats
                if logger:
                    thematiques_detectees = entreprise_enrichie.get('thematiques_principales', [])
                    score_global = entreprise_enrichie.get('score_global', 0.0)
                    
                    logger.log_analyse_thematique(
                        nom_entreprise=nom_entreprise,
                        thematiques=thematiques_detectees,
                        score=score_global
                    )
                    
                    if score_global > 0.0:
                        print(f"    🎉 SUCCÈS: {nom_entreprise} → score {score_global:.3f}")
                
            except Exception as e:
                print(f"    ❌ Erreur analyse {nom_entreprise}: {e}")
                import traceback
                traceback.print_exc()
                
                if logger:
                    logger.log_analyse_thematique(nom_entreprise, [], 0.0, erreurs=[str(e)])
                
                # Structure d'erreur
                entreprise_base = resultat.get('entreprise', {})
                entreprise_base.update({
                    'analyse_thematique': {thematique: {'trouve': False, 'score_pertinence': 0.0} for thematique in self.thematiques},
                    'score_global': 0.0,
                    'thematiques_principales': [],
                    'date_analyse': datetime.now().isoformat(),
                    'erreur_analyse': str(e)
                })
                entreprises_enrichies.append(entreprise_base)
                continue
        
        # Statistiques de détection
        entreprises_actives = [e for e in entreprises_enrichies if e.get('score_global', 0) > 0.2]
        entreprises_tres_actives = [e for e in entreprises_enrichies if e.get('score_global', 0) > 0.5]
        
        print(f"✅ Analyse terminée pour {len(entreprises_enrichies)} entreprises")
        print(f"🎯 Entreprises actives (>0.2): {len(entreprises_actives)}")
        print(f"🏆 Entreprises très actives (>0.5): {len(entreprises_tres_actives)}")
        
        if len(entreprises_actives) > 0:
            print("🎉 SUCCÈS : Entreprises détectées !")
            for ent in entreprises_actives[:3]:
                nom = ent.get('nom', 'N/A')
                score = ent.get('score_global', 0)
                themes = ent.get('thematiques_principales', [])
                print(f"    • {nom}: {score:.3f} → {themes}")
        
        return entreprises_enrichies

    def _analyser_donnee_thematique(self, thematique: str, donnee: Dict, source: str, resultats_thematiques: Dict):
        """✅ NOUVEAU : Analyse d'une donnée thématique spécifique"""
        if not isinstance(donnee, dict):
            return
        
        # Calcul du score de pertinence
        score = self._calculer_score_pertinence_adapte(donnee, source, thematique)
        
        if score > self.seuil_pertinence:
            print(f"      ✅ {thematique}: score {score:.2f}")
            
            resultats_thematiques[thematique]['trouve'] = True
            resultats_thematiques[thematique]['score_pertinence'] = max(
                resultats_thematiques[thematique]['score_pertinence'], score
            )
            
            if source not in resultats_thematiques[thematique]['sources']:
                resultats_thematiques[thematique]['sources'].append(source)
            
            # Ajout des détails
            detail = {
                'source': source,
                'score': score,
                'informations': self._extraire_informations_adaptees(donnee, source),
                'timestamp': datetime.now().isoformat()
            }
            resultats_thematiques[thematique]['details'].append(detail)
        else:
            print(f"      ⚪ {thematique}: score {score:.2f} (< {self.seuil_pertinence})")

    def _analyser_liste_donnees(self, donnees: List, thematique: str) -> float:
        """✅ NOUVEAU : Analyse d'une liste de données pour une thématique"""
        if not donnees:
            return 0.0
        
        score_total = 0.0
        mots_cles_thematique = self.config.get(thematique, [])
        
        for donnee in donnees[:5]:  # Max 5 éléments
            if isinstance(donnee, dict):
                contenu = self._extraire_contenu_textuel(donnee)
                if contenu:
                    score_element = self._analyser_contenu_thematique(contenu, thematique)
                    score_total += score_element
            elif isinstance(donnee, str):
                score_element = self._analyser_contenu_thematique(donnee, thematique)
                score_total += score_element
        
        return min(score_total, 0.6)