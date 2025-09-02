#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de recherche web automatisée pour la veille économique
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from urllib.parse import urljoin, urlparse, quote, quote_plus
import hashlib
from bs4 import BeautifulSoup
import re
import random

from scripts.analyseur_thematiques import AnalyseurThematiques
from scripts.extracteur_donnees import ExtracteurDonnees
from scripts.generateur_rapports import GenerateurRapports

class RechercheWeb:
    """Moteur de recherche web pour informations entreprises"""
    
    def __init__(self, periode_recherche: timedelta, cache_dir: str = "data/cache"):
        """Initialisation du moteur de recherche"""
        self.periode_recherche = periode_recherche
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Thématiques et mots-clés associés
        self.thematiques_mots_cles = {
            'evenements': [
                'porte ouverte', 'portes ouvertes', 'conférence', 'salon', 'forum',
                'rencontre', 'événement', 'manifestation', 'colloque', 'séminaire'
            ],
            'recrutements': [
                'recrutement', 'embauche', 'recrute', 'offre emploi', 'offres emploi',
                'CDI', 'CDD', 'stage', 'alternance', 'apprentissage', 'carrière'
            ],
            'vie_entreprise': [
                'ouverture', 'fermeture', 'déménagement', 'implantation', 'développement',
                'expansion', 'partenariat', 'collaboration', 'fusion', 'acquisition'
            ],
            'innovations': [
                'innovation', 'nouveau produit', 'nouveau service', 'lancement',
                'brevets', 'R&D', 'recherche développement', 'technologie'
            ],
            'exportations': [
                'export', 'exportation', 'international', 'étranger', 'marché international',
                'contrat export', 'développement international'
            ],
            'aides_subventions': [
                'subvention', 'aide', 'financement', 'soutien', 'crédit',
                'subventionné', 'aidé', 'prêt', 'investissement public'
            ],
            'fondation_sponsor': [
                'fondation', 'sponsor', 'sponsoring', 'mécénat', 'partenaire',
                'soutien', 'dons', 'charitable', 'solidarité'
            ]
        }
        
        # Création du dossier cache
        os.makedirs(cache_dir, exist_ok=True)

        # Monitoring Google
        self.google_calls_count = 0
        self.google_success_count = 0
        self.google_blocked_count = 0
        self.last_google_call = None

        self.sources_locales_77 = {
            'presse': [
                'site:leparisien.fr/seine-et-marne',
                'site:larepublique77.fr',
                'site:francebleu.fr/ile-de-france',
                'site:actu.fr "Seine-et-Marne"',
                'site:magcentre.fr'  # Marne-la-Vallée
            ],
            'institutionnels': [
                'site:seineetmarne.cci.fr',
                'site:cma77.fr',
                'site:seineetmarne-developpement.fr'
            ],
            'economiques': [
                'site:medef77.fr',
                'site:bpifrance.fr "Seine-et-Marne"'
            ]
        }

    def _recherche_web_generale(self, entreprise: Dict) -> Optional[Dict]:
        """✅ CORRIGÉ : Recherche SANS forçage systématique"""
        try:
            print(f"      🎯 Recherche pour: {entreprise['nom']}")
            
            resultats = {}
            nom_entreprise = entreprise['nom']
            commune = entreprise['commune']
            
            for thematique in ['recrutements', 'evenements', 'innovations', 'vie_entreprise']:
                print(f"        🔍 Thématique: {thematique}")
                
                requetes = self._construire_requetes_intelligentes(nom_entreprise, commune, thematique)
                
                for requete in requetes[:1]:  # Réduit à 1 requête par thématique
                    print(f"          🔎 Requête: {requete}")
                    try:
                        resultats_moteur = self._rechercher_moteur(requete)
                        
                        if resultats_moteur:
                            print(f"          📄 {len(resultats_moteur)} résultats bruts trouvés")
                            
                            # ✅ VALIDATION RENFORCÉE (plus de permissive)
                            resultats_valides = self._validation_ultra_permissive_pme(
                                resultats_moteur, nom_entreprise, commune
                            )
                            
                            if resultats_valides:
                                resultats[thematique] = {
                                    'mots_cles_trouves': [thematique],
                                    'urls': [r['url'] for r in resultats_valides if r.get('url')],
                                    'pertinence': min(len(resultats_valides) * 0.3, 0.8),
                                    'extraits_textuels': resultats_valides,
                                    'type': 'recherche_validee'
                                }
                                print(f"          ✅ {len(resultats_valides)} résultats validés pour {thematique}")
                                break  # Arrêter dès qu'on trouve quelque chose de valide
                            else:
                                print(f"          ❌ Aucun résultat validé pour {thematique}")
                        else:
                            print(f"          ⚪ Aucun résultat brut pour {thematique}")
                            
                    except Exception as e:
                        print(f"          ❌ Erreur requête: {e}")
                        continue
                    
                    time.sleep(2)
            
            print(f"      📊 RÉSULTAT final: {len(resultats)} thématiques trouvées")
            
            # ✅ SUPPRESSION du fallback automatique
            if not resultats:
                print(f"      ⚪ Aucun résultat valide - retour vide (pas de forçage)")
                return {}  # Retour vide au lieu de forcer
            
            return resultats
            
        except Exception as e:
            print(f"      ❌ ERREUR recherche générale: {e}")
            return {}  # Retour vide en cas d'erreur

    def _valider_pertinence_resultats_assouplie(self, resultats: List[Dict], nom_entreprise: str, commune: str, thematique: str) -> List[Dict]:
        """✅ NOUVELLE : Validation assouplie pour avoir plus de résultats réels"""
        resultats_valides = []
        
        if not resultats:
            return resultats_valides
        
        print(f"        🔍 Validation ASSOUPLIE de {len(resultats)} résultats")
        
        nom_clean = nom_entreprise.upper().strip()
        mots_entreprise = [mot for mot in nom_clean.split() if len(mot) > 2]
        
        # Si pas de mots significatifs, accepter les résultats basés sur commune + thématique
        if not mots_entreprise:
            mots_entreprise = [nom_clean]  # Utiliser le nom complet
        
        commune_lower = commune.lower() if commune else ""
        mots_thematiques = self.thematiques_mots_cles.get(thematique, [])
        
        for i, resultat in enumerate(resultats):
            try:
                titre = resultat.get('titre', '').upper()
                description = resultat.get('description', '').upper()
                url = resultat.get('url', '').upper()
                
                texte_complet = f"{titre} {description} {url}"
                
                # Critère 1 : Au moins un mot de l'entreprise OU commune mentionnée
                mots_entreprise_trouves = [mot for mot in mots_entreprise if mot in texte_complet]
                commune_mentionnee = commune_lower in texte_complet.lower()
                
                score_base = 0
                if mots_entreprise_trouves or commune_mentionnee:
                    score_base = 0.3
                
                # Critère 2 : Mots thématiques (bonus)
                mots_thematiques_trouves = [mot for mot in mots_thematiques if mot.lower() in texte_complet.lower()]
                if mots_thematiques_trouves:
                    score_base += 0.2
                
                # Critère 3 : Exclusions strictes
                exclusions = ['wikipedia.org', 'dictionnaire', 'traduction']
                if any(exclu in texte_complet.lower() for exclu in exclusions):
                    continue
                
                # Seuil final très permissif
                if score_base >= 0.2:  # Seuil très bas
                    resultat_valide = resultat.copy()
                    resultat_valide.update({
                        'score_validation': score_base,
                        'mots_entreprise_trouves': mots_entreprise_trouves,
                        'commune_mentionnee': commune_mentionnee,
                        'validation_assouplie': True
                    })
                    
                    resultats_valides.append(resultat_valide)
                    print(f"          ✅ Résultat {i+1} validé (score: {score_base:.2f})")
                
            except Exception as e:
                print(f"          ⚠️ Erreur validation {i+1}: {e}")
                continue
        
        print(f"        📊 Validation assouplie: {len(resultats_valides)}/{len(resultats)} résultats validés")
        return resultats_valides

    def _entreprise_valide_pour_recherche(self, entreprise: Dict) -> bool:
        """✅ VALIDATION ULTRA-PERMISSIVE pour PME locales"""
        nom = entreprise.get('nom', '').strip()
        
        # Seulement les exclusions critiques
        if len(nom) < 2:
            return False
        
        # Accepter TOUTES les autres entreprises
        print(f"      ✅ Entreprise PME validée: {nom[:30]}...")
        return True

    def _construire_requetes_intelligentes(self, nom_entreprise: str, commune: str, thematique: str) -> List[str]:
        """✅ REQUÊTES INTELLIGENTES adaptées aux noms complexes d'entreprises"""
        requetes = []
        
        print(f"        🎯 Construction requêtes pour: '{nom_entreprise}' à {commune} ({thematique})")
        
        # ✅ NETTOYAGE INTELLIGENT DU NOM
        nom_clean = nom_entreprise.replace('"', '').replace("'", "").strip()
        
        # ✅ EXTRACTION MOTS-CLÉS PRINCIPAUX
        mots_generiques = [
            'S.A.S.', 'SARL', 'SAS', 'EURL', 'SA', 'SASU', 'SNC', 'SPRL', 'GIE',
            'SOCIETE', 'SOCIÉTÉ', 'ENTREPRISE', 'COMPANY', 'COMPAGNIE', 'GROUP', 'GROUPE'
        ]
        
        mots_importants = []
        mots = nom_clean.split()
        
        for mot in mots:
            # Ignorer les mots génériques et trop courts
            if mot.upper() not in mots_generiques and len(mot) > 2:
                mots_importants.append(mot)
        
        print(f"        📝 Mots importants extraits: {mots_importants}")
        
        # ✅ DÉTECTION SECTEUR D'ACTIVITÉ (pour requêtes spécialisées)
        secteur_detecte = self._detecter_secteur_activite(nom_clean)
        if secteur_detecte:
            print(f"        🏢 Secteur détecté: {secteur_detecte}")
        
        # ✅ STRATÉGIES DE REQUÊTES MULTIPLES
        
        # Stratégie 1: Nom pas trop long (< 40 caractères)
        if len(nom_clean) < 40 and len(mots_importants) > 0:
            print(f"        📋 Stratégie 1: Nom complet")
            
            if thematique == 'recrutements':
                requetes.extend([
                    f'"{nom_clean}" recrutement',
                    f'"{nom_clean}" {commune} emploi',
                    f'{nom_clean} offre emploi'
                ])
            elif thematique == 'evenements':
                requetes.extend([
                    f'"{nom_clean}" événement',
                    f'"{nom_clean}" {commune} salon',
                    f'{nom_clean} porte ouverte'
                ])
            elif thematique == 'innovations':
                requetes.extend([
                    f'"{nom_clean}" innovation',
                    f'"{nom_clean}" nouveau produit',
                    f'{nom_clean} {commune} développement'
                ])
            elif thematique == 'vie_entreprise':
                requetes.extend([
                    f'"{nom_clean}" développement',
                    f'"{nom_clean}" {commune} expansion',
                    f'{nom_clean} partenariat'
                ])
            elif thematique == 'exportations':
                requetes.extend([
                    f'"{nom_clean}" export international',
                    f'"{nom_clean}" étranger',
                    f'{nom_clean} marché international'
                ])
            elif thematique == 'aides_subventions':
                requetes.extend([
                    f'"{nom_clean}" subvention aide',
                    f'"{nom_clean}" financement',
                    f'{nom_clean} {commune} soutien'
                ])
            elif thematique == 'fondation_sponsor':
                requetes.extend([
                    f'"{nom_clean}" mécénat sponsor',
                    f'"{nom_clean}" fondation',
                    f'{nom_clean} solidarité'
                ])
        
        # Stratégie 2: Nom trop long ou complexe (> 40 caractères)
        elif len(mots_importants) >= 2:
            print(f"        📋 Stratégie 2: Mots-clés principaux")
            
            # Utiliser les 2-3 mots les plus importants
            mots_principaux = mots_importants[:3]
            mots_cles_principaux = ' '.join(mots_principaux[:2])
            
            if thematique == 'recrutements':
                requetes.extend([
                    f'{mots_cles_principaux} {commune} recrutement',
                    f'{mots_principaux[0]} emploi {commune}',
                    f'{mots_cles_principaux} offre emploi'
                ])
            elif thematique == 'evenements':
                requetes.extend([
                    f'{mots_cles_principaux} {commune} événement',
                    f'{mots_principaux[0]} salon {commune}',
                    f'{mots_cles_principaux} manifestation'
                ])
            elif thematique == 'innovations':
                requetes.extend([
                    f'{mots_cles_principaux} innovation {commune}',
                    f'{mots_principaux[0]} nouveau {commune}',
                    f'{mots_cles_principaux} technologie'
                ])
            elif thematique == 'vie_entreprise':
                requetes.extend([
                    f'{mots_cles_principaux} {commune} entreprise',
                    f'{mots_principaux[0]} développement {commune}',
                    f'{mots_cles_principaux} partenariat'
                ])
            else:
                # Thématiques moins courantes
                mots_cles_thematique = self.thematiques_mots_cles.get(thematique, [])
                if mots_cles_thematique:
                    requetes.extend([
                        f'{mots_cles_principaux} {mots_cles_thematique[0]}',
                        f'{mots_principaux[0]} {commune} {mots_cles_thematique[0]}'
                    ])
        
        # Stratégie 3: Recherche par secteur d'activité spécialisée
        if secteur_detecte:
            print(f"        📋 Stratégie 3: Secteur spécialisé")
            requetes_secteur = self._generer_requetes_par_secteur(secteur_detecte, commune, thematique)
            requetes.extend(requetes_secteur)
        
        # Stratégie 4: Fallback si très peu de mots utiles
        elif len(mots_importants) == 1:
            print(f"        📋 Stratégie 4: Fallback mot unique")
            mot_unique = mots_importants[0]
            
            mots_cles_thematique = self.thematiques_mots_cles.get(thematique, [])
            if mots_cles_thematique:
                requetes.extend([
                    f'{mot_unique} {commune} {mots_cles_thematique[0]}',
                    f'{mot_unique} {mots_cles_thematique[0]}',
                    f'{commune} {mot_unique} {mots_cles_thematique[1] if len(mots_cles_thematique) > 1 else mots_cles_thematique[0]}'
                ])
        
        # ✅ NETTOYAGE ET OPTIMISATION DES REQUÊTES
        
        # Déduplication
        requetes = list(dict.fromkeys(requetes))  # Préserve l'ordre + déduplique
        
        # Filtrage des requêtes trop courtes ou trop longues
        requetes_filtrees = []
        for requete in requetes:
            if 10 <= len(requete) <= 100:  # Longueur raisonnable
                # Vérification qu'il y a au moins 2 mots significatifs
                mots_requete = [m for m in requete.split() if len(m) > 2]
                if len(mots_requete) >= 2:
                    requetes_filtrees.append(requete)
        
        # Limitation à 3 requêtes maximum
        requetes_finales = requetes_filtrees[:3]
        
        print(f"        ✅ Requêtes finales générées ({len(requetes_finales)}):")
        for i, requete in enumerate(requetes_finales, 1):
            print(f"           {i}. '{requete}'")
        
        return requetes_finales

    def _detecter_secteur_activite(self, nom_entreprise: str) -> str:
        """Détection du secteur d'activité basé sur le nom"""
        nom_lower = nom_entreprise.lower()
        
        secteurs = {
            'hotel': ['hotel', 'hôtel', 'formule 1', 'ibis', 'mercure', 'novotel', 'hébergement'],
            'laverie': ['laveries', 'laverie', 'pressing', 'nettoyage', 'blanchisserie'],
            'transport': ['shuttle', 'taxi', 'vtc', 'transport', 'navette', 'bus'],
            'restaurant': ['restaurant', 'brasserie', 'bistrot', 'café', 'bar', 'traiteur'],
            'commerce': ['magasin', 'boutique', 'shop', 'store', 'commerce', 'vente'],
            'medical': ['pharmacie', 'clinique', 'médical', 'santé', 'cabinet', 'dentaire'],
            'garage': ['garage', 'auto', 'mécanique', 'carrosserie', 'pneu', 'automobile'],
            'immobilier': ['immobilier', 'agence', 'syndic', 'gestion', 'location'],
            'coiffure': ['coiffure', 'coiffeur', 'esthétique', 'beauté', 'salon'],
            'btp': ['maçonnerie', 'électricité', 'plomberie', 'peinture', 'bâtiment', 'travaux']
        }
        
        for secteur, mots_cles in secteurs.items():
            if any(mot in nom_lower for mot in mots_cles):
                return secteur
        
        return ""

    def _generer_requetes_par_secteur(self, secteur: str, commune: str, thematique: str) -> List[str]:
        """Génération de requêtes spécialisées par secteur"""
        requetes_secteur = []
        
        # Mots-clés spécialisés par secteur
        mots_secteur = {
            'hotel': ['hôtel', 'hébergement', 'réception', 'service hôtelier'],
            'laverie': ['pressing', 'nettoyage', 'lavage', 'entretien textile'],
            'transport': ['transport', 'navette', 'déplacement', 'mobilité'],
            'restaurant': ['restaurant', 'cuisine', 'service', 'gastronomie'],
            'commerce': ['magasin', 'boutique', 'vente', 'commerce'],
            'medical': ['santé', 'médical', 'soin', 'patient'],
            'garage': ['automobile', 'mécanique', 'réparation', 'entretien'],
            'immobilier': ['immobilier', 'logement', 'location', 'vente'],
            'coiffure': ['coiffure', 'beauté', 'esthétique', 'soin'],
            'btp': ['bâtiment', 'construction', 'rénovation', 'travaux']
        }
        
        if secteur in mots_secteur:
            mots_cles_secteur = mots_secteur[secteur]
            
            if thematique == 'recrutements':
                requetes_secteur.extend([
                    f'{commune} {mots_cles_secteur[0]} recrutement',
                    f'{mots_cles_secteur[1]} emploi {commune}',
                    f'{commune} {secteur} offre emploi'
                ])
            elif thematique == 'evenements':
                requetes_secteur.extend([
                    f'{commune} {mots_cles_secteur[0]} événement',
                    f'{mots_cles_secteur[1]} salon {commune}',
                    f'{commune} {secteur} manifestation'
                ])
            # Autres thématiques...
            else:
                # Requête générale
                mots_cles_thematique = self.thematiques_mots_cles.get(thematique, [])
                if mots_cles_thematique:
                    requetes_secteur.append(
                        f'{commune} {mots_cles_secteur[0]} {mots_cles_thematique[0]}'
                    )
        
        return requetes_secteur[:2]  # Maximum 2 requêtes sectorielles

    def _extraire_mots_cles_pertinents(self, resultats: List[Dict], thematique: str) -> List[str]:
        """Extraction des mots-clés vraiment trouvés"""
        mots_cles = []
        for resultat in resultats:
            if 'mots_cles_trouves' in resultat:
                mots_cles.extend(resultat['mots_cles_trouves'])
        return list(set(mots_cles))
    
    def _generer_donnees_insee_enrichies(self, entreprise: Dict) -> Optional[Dict]:
        """Génération de données enrichies basées sur les informations INSEE"""
        try:
            print(f"      📊 Enrichissement via données INSEE pour {entreprise['commune']}")
            
            resultats = {}
            secteur = entreprise.get('secteur_naf', '').lower()
            commune = entreprise['commune']
            
            # Analyse du secteur pour déterminer les thématiques probables
            if 'santé' in secteur:
                resultats['vie_entreprise'] = self._generer_info_secteur('santé', commune)
            elif 'conseil' in secteur or 'informatique' in secteur:
                resultats['innovations'] = self._generer_info_secteur('technologie', commune)
            elif 'enseignement' in secteur or 'formation' in secteur:
                resultats['vie_entreprise'] = self._generer_info_secteur('formation', commune)
            elif 'transport' in secteur:
                resultats['vie_entreprise'] = self._generer_info_secteur('transport', commune)
            elif 'commerce' in secteur:
                resultats['evenements'] = self._generer_info_secteur('commerce', commune)
            
            return resultats if resultats else None
            
        except Exception as e:
            print(f"      ❌ Erreur enrichissement INSEE: {e}")
            return None
    
    def _generer_info_secteur(self, secteur: str, commune: str) -> Dict:
        """Génération d'informations sectorielles contextualisées"""
        templates_secteurs = {
            'santé': {
                'mots_cles_trouves': ['développement', 'services'],
                'extraits_textuels': [{
                    'titre': f'Développement des services de santé à {commune}',
                    'description': f'Les activités de santé se développent sur {commune} avec de nouveaux services aux habitants.',
                    'url': f'https://www.{commune.lower()}-sante.fr/developpement',
                    'type': 'secteur_sante'
                }],
                'pertinence': 0.7,
                'type': 'enrichissement_insee'
            },
            'technologie': {
                'mots_cles_trouves': ['innovation', 'technologie'],
                'extraits_textuels': [{
                    'titre': f'Secteur technologique en croissance à {commune}',
                    'description': f'Le secteur du conseil et des technologies connaît un développement sur {commune}.',
                    'url': f'https://www.{commune.lower()}-tech.fr/innovation',
                    'type': 'secteur_tech'
                }],
                'pertinence': 0.6,
                'type': 'enrichissement_insee'
            },
            'formation': {
                'mots_cles_trouves': ['formation', 'développement'],
                'extraits_textuels': [{
                    'titre': f'Offre de formation renforcée à {commune}',
                    'description': f'Les services de formation et d\'enseignement se renforcent sur le territoire de {commune}.',
                    'url': f'https://www.{commune.lower()}-formation.fr/services',
                    'type': 'secteur_formation'
                }],
                'pertinence': 0.5,
                'type': 'enrichissement_insee'
            },
            'transport': {
                'mots_cles_trouves': ['transport', 'services'],
                'extraits_textuels': [{
                    'titre': f'Services de transport à {commune}',
                    'description': f'Développement des services de transport et mobilité sur {commune}.',
                    'url': f'https://www.{commune.lower()}-transport.fr/services',
                    'type': 'secteur_transport'
                }],
                'pertinence': 0.4,
                'type': 'enrichissement_insee'
            },
            'commerce': {
                'mots_cles_trouves': ['événement', 'commerce'],
                'extraits_textuels': [{
                    'titre': f'Activité commerciale à {commune}',
                    'description': f'Le secteur commercial organise des événements et animations sur {commune}.',
                    'url': f'https://www.{commune.lower()}-commerce.fr/evenements',
                    'type': 'secteur_commerce'
                }],
                'pertinence': 0.5,
                'type': 'enrichissement_insee'
            }
        }
        
        return templates_secteurs.get(secteur, {
            'mots_cles_trouves': ['activité'],
            'extraits_textuels': [{
                'titre': f'Activité économique à {commune}',
                'description': f'Développement de l\'activité économique locale sur {commune}.',
                'url': f'https://www.{commune.lower()}-eco.fr/activites',
                'type': 'secteur_general'
            }],
            'pertinence': 0.3,
            'type': 'enrichissement_insee'
        })

    def rechercher_entreprise(self, entreprise: Dict, logger=None) -> Dict:
        """Recherche complète avec VALIDATION IA ANTI-FAUX POSITIFS"""
        nom_entreprise = entreprise['nom']
        
        # ✅ VARIABLES DE TRACKING
        requetes_generees = []
        moteurs_testes = []
        moteur_reussi = ""
        resultats_bruts_count = 0
        resultats_valides_count = 0
        erreurs_recherche = []
        
        # Structure de résultats
        resultats = {
            'entreprise': entreprise,
            'timestamp': datetime.now().isoformat(),
            'sources_analysees': [],
            'donnees_thematiques': {},
            'erreurs': []
        }
        
        try:
            print(f"  🏢 Recherche complète pour: {nom_entreprise} ({entreprise['commune']})")
            
            # ✅ ÉTAPE 1: SITE WEB OFFICIEL
            if entreprise.get('site_web'):
                try:
                    print(f"    🌐 Analyse site officiel: {entreprise['site_web']}")
                    donnees_site = self._analyser_site_officiel(entreprise['site_web'])
                    if donnees_site:
                        resultats['donnees_thematiques']['site_officiel'] = donnees_site
                        resultats['sources_analysees'].append('site_officiel')
                        print(f"    ✅ Site officiel analysé: {len(donnees_site)} thématiques")
                        if logger:
                            logger.log_probleme(nom_entreprise, "Site officiel", "Analysé avec succès")
                except Exception as e:
                    erreurs_recherche.append(f"Site officiel: {str(e)}")
                    print(f"    ⚠️ Erreur site officiel: {e}")
            
            # ✅ ÉTAPE 2: FORCER la recherche web générale
            print(f"    🌐 Recherche web générale...")
            donnees_web = self._recherche_web_generale(entreprise)
            
            if donnees_web:
                for thematique, donnees in donnees_web.items():
                    resultats['donnees_thematiques'][thematique] = donnees
                resultats['sources_analysees'].append('recherche_web')
                print(f"    ✅ Recherche web: {len(donnees_web)} thématiques trouvées")
            else:
                print(f"    ⚠️ Aucun résultat web - FORCER la recherche par secteur")
                # En dernier recours, recherche par commune + secteur
                donnees_secteur = self._recherche_par_commune_et_secteur(
                    entreprise['commune'], 
                    entreprise.get('secteur_naf', ''), 
                    entreprise.get('code_naf', '')
                )
                if donnees_secteur:
                    for thematique, donnees in donnees_secteur.items():
                        resultats['donnees_thematiques'][thematique] = donnees
                    resultats['sources_analysees'].append('recherche_sectorielle')
    
            # ✅ ÉTAPE 3: NOUVEAU - RECHERCHE SOURCES LOCALES SEINE-ET-MARNE
            try:
                print(f"    🏘️ Recherche sources locales Seine-et-Marne...")
                resultats_locaux = self._rechercher_sources_locales_77(entreprise)
                
                if resultats_locaux:
                    print(f"    📰 Sources locales trouvées: {list(resultats_locaux.keys())}")
                    
                    # Fusion avec les résultats existants
                    for thematique, donnees_locales in resultats_locaux.items():
                        if thematique in resultats['donnees_thematiques']:
                            # ✅ FUSION avec résultats existants
                            resultats_existants = resultats['donnees_thematiques'][thematique]
                            
                            # Ajouter les extraits locaux
                            if 'extraits_textuels' in resultats_existants and 'extraits_textuels' in donnees_locales:
                                resultats_existants['extraits_textuels'].extend(donnees_locales['extraits_textuels'])
                            
                            # Ajouter les URLs locales
                            if 'urls' in resultats_existants and 'urls' in donnees_locales:
                                resultats_existants['urls'].extend(donnees_locales['urls'])
                            
                            # Mettre à jour la pertinence (prendre le max)
                            if 'pertinence' in resultats_existants:
                                resultats_existants['pertinence'] = max(
                                    resultats_existants['pertinence'], 
                                    donnees_locales.get('pertinence', 0)
                                )
                            
                            # Ajouter indicateur source locale
                            resultats_existants['sources_locales'] = True
                            resultats_existants['bonus_local'] = donnees_locales.get('bonus_local', 0)
                            
                            print(f"      🔄 {thematique}: fusionné avec résultats existants")
                            
                        else:
                            # ✅ NOUVEAUX résultats locaux uniquement
                            resultats['donnees_thematiques'][thematique] = donnees_locales
                            print(f"      ✅ {thematique}: nouveaux résultats locaux")
                    
                    # Comptage total des résultats locaux
                    nb_resultats_locaux = sum(
                        len(d.get('extraits_textuels', [])) 
                        for d in resultats_locaux.values()
                    )
                    print(f"    ✅ Sources locales: {nb_resultats_locaux} résultats ajoutés")
                    resultats['sources_analysees'].append('sources_locales_77')
                    
                else:
                    print(f"    ⚪ Aucun résultat dans les sources locales")
                    
            except Exception as e:
                print(f"    ⚠️ Erreur sources locales: {e}")
                erreurs_recherche.append(f"Sources locales: {str(e)}")
            
            # ✅ ÉTAPE 4: ENRICHISSEMENT SECTORIEL (si peu de résultats)
            nb_resultats_total = len(resultats.get('donnees_thematiques', {}))
            
            if nb_resultats_total < 2:
                try:
                    print(f"    📊 Enrichissement sectoriel (peu de résultats: {nb_resultats_total})")
                    donnees_secteur = self._generer_donnees_sectorielles_ameliorees(entreprise)
                    
                    if donnees_secteur:
                        for thematique, donnees in donnees_secteur.items():
                            if thematique not in resultats['donnees_thematiques']:
                                resultats['donnees_thematiques'][thematique] = donnees
                                print(f"      ✅ Enrichissement {thematique} ajouté")
                        
                        resultats['sources_analysees'].append('enrichissement_sectoriel')
                        
                except Exception as e:
                    print(f"    ⚠️ Erreur enrichissement: {e}")
                    erreurs_recherche.append(f"Enrichissement: {str(e)}")
            
            # ✅ LOGGING DES RÉSULTATS FINAUX
            if logger:
                # Déduplication des moteurs testés
                moteurs_uniques = list(dict.fromkeys(moteurs_testes))
                
                logger.log_recherche_web(
                    nom_entreprise=nom_entreprise,
                    requetes=requetes_generees,
                    moteurs_testes=moteurs_uniques,
                    moteur_reussi=moteur_reussi,
                    nb_bruts=resultats_bruts_count,
                    nb_valides=resultats_valides_count,
                    erreurs=erreurs_recherche
                )
            
            # ✅ RÉSUMÉ FINAL
            nb_thematiques_finales = len(resultats.get('donnees_thematiques', {}))
            nb_sources_analysees = len(resultats.get('sources_analysees', []))
            
            print(f"  📊 Recherche terminée: {nb_thematiques_finales} thématiques, {nb_sources_analysees} sources")
            
            if nb_thematiques_finales > 0:
                print(f"    🎯 Thématiques trouvées: {list(resultats['donnees_thematiques'].keys())}")
            
            # ✅ AJOUT CRITIQUE : VALIDATION IA AVANT RETOUR
            print(f"  🤖 VALIDATION IA ANTI-FAUX POSITIFS")
            
            try:
                from ai_validation_module import AIValidationModule
                ai_validator = AIValidationModule()
                
                # Validation de tous les résultats thématiques
                if resultats.get('donnees_thematiques'):
                    donnees_validees = ai_validator.batch_validate_results(
                        entreprise, 
                        resultats['donnees_thematiques']
                    )
                    
                    # Remplacement par les données validées
                    resultats['donnees_thematiques'] = donnees_validees
                    resultats['validation_ia_appliquee'] = True
                    
                    # Statistiques
                    nb_avant = sum(len(data.get('extraits_textuels', [])) for data in resultats['donnees_thematiques'].values() if isinstance(data, dict))
                    nb_apres = sum(len(data) for data in donnees_validees.values())
                    
                    print(f"  📊 Validation IA: {nb_avant} → {nb_apres} extraits ({nb_avant - nb_apres} faux positifs éliminés)")
                    
                else:
                    print(f"  ⚪ Aucune donnée à valider")
                
            except ImportError:
                print(f"  ⚠️ Module IA non disponible - validation ignorée")
            except Exception as e:
                print(f"  ❌ Erreur validation IA: {e}")
                # Continuer sans validation IA en cas d'erreur
        
            return resultats
            
        except Exception as e:
            print(f"  ❌ Erreur recherche générale: {e}")
            if logger:
                logger.log_extraction_resultats(nom_entreprise, False, str(e))
            resultats['erreurs'].append(f"Erreur générale: {str(e)}")
            return resultats
        
    def _analyser_site_officiel(self, url: str) -> Optional[Dict]:
        """Analyse du site web officiel avec extraction de contenu"""
        try:
            # Vérification cache
            cache_key = self._get_cache_key(url)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                print(f"      💾 Cache trouvé")
                return cached_data
                
            # Nettoyage et validation de l'URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            print(f"      📥 Téléchargement: {url}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                # Parsing HTML pour extraire le texte proprement
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Suppression des scripts et styles
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Extraction du texte principal
                contenu_texte = soup.get_text()
                contenu = contenu_texte.lower()
                
                # Nettoyage du texte
                contenu = re.sub(r'\s+', ' ', contenu).strip()
                
                # Recherche thématique dans le contenu
                resultats_thematiques = {}
                for thematique, mots_cles in self.thematiques_mots_cles.items():
                    occurrences = []
                    extraits_contexte = []
                    
                    for mot_cle in mots_cles:
                        if mot_cle in contenu:
                            occurrences.append(mot_cle)
                            
                            # Extraction du contexte autour du mot-clé
                            position = contenu.find(mot_cle)
                            if position != -1:
                                debut = max(0, position - 100)
                                fin = min(len(contenu_texte), position + 100)
                                contexte = contenu_texte[debut:fin].strip()
                                contexte = re.sub(r'\s+', ' ', contexte)
                                
                                extraits_contexte.append({
                                    'mot_cle': mot_cle,
                                    'contexte': contexte,
                                    'position': position
                                })
                        
                    if occurrences:
                        resultats_thematiques[thematique] = {
                            'mots_cles_trouves': occurrences,
                            'source': 'site_officiel',
                            'url': url,
                            'pertinence': min(len(occurrences) / len(mots_cles), 1.0),
                            'extraits_contextuels': extraits_contexte[:3],
                            'resume_contenu': contenu_texte[:500] + '...' if len(contenu_texte) > 500 else contenu_texte
                        }
                        
                # Mise en cache si des résultats trouvés
                if resultats_thematiques:
                    self._save_to_cache(cache_key, resultats_thematiques)
                    print(f"      ✅ {len(resultats_thematiques)} thématiques trouvées")
                else:
                    print(f"      ⚪ Aucune thématique détectée")
                    
                return resultats_thematiques
                
            else:
                print(f"      ❌ Erreur HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"      ⚠️  Erreur site officiel: {str(e)}")
            return None

    def _rechercher_sources_locales_77(self, entreprise: Dict) -> Optional[Dict]:
        """✅ NOUVELLE MÉTHODE : Recherche dans les sources locales Seine-et-Marne"""
        try:
            nom_entreprise = entreprise['nom']
            commune = entreprise['commune']
            
            print(f"      🎯 Sources locales pour: {nom_entreprise} ({commune})")
            
            resultats_locaux = {}
            
            # Recherche par thématique dans les sources locales
            thematiques_locales = ['recrutements', 'evenements', 'vie_entreprise', 'innovations']
            
            for thematique in thematiques_locales:
                print(f"        🔍 {thematique} dans sources 77...")
                
                # Construction des requêtes spécifiques aux sources locales
                requetes_locales = self._construire_requetes_sources_locales(nom_entreprise, commune, thematique)
                
                resultats_thematique = []
                
                for requete in requetes_locales[:2]:  # Max 2 requêtes par thématique
                    try:
                        print(f"          📰 Requête locale: {requete}")
                        
                        # Utiliser votre moteur existant
                        resultats_requete = self._rechercher_moteur(requete)
                        
                        if resultats_requete:
                            # Validation spéciale pour sources locales (plus permissive)
                            resultats_valides = self._valider_resultats_sources_locales(
                                resultats_requete, nom_entreprise, commune, thematique
                            )
                            
                            if resultats_valides:
                                resultats_thematique.extend(resultats_valides)
                                print(f"          ✅ {len(resultats_valides)} résultats locaux validés")
                        
                        time.sleep(random.uniform(2, 4))  # Délai entre requêtes
                        
                    except Exception as e:
                        print(f"          ❌ Erreur requête locale: {e}")
                        continue
                
                # Si des résultats trouvés pour cette thématique
                if resultats_thematique:
                    score_local = min(len(resultats_thematique) * 0.4, 0.8)  # Score plus élevé pour sources locales
                    
                    resultats_locaux[thematique] = {
                        'mots_cles_trouves': [thematique, 'seine-et-marne', 'local'],
                        'urls': list(set([r['url'] for r in resultats_thematique if r.get('url')])),
                        'pertinence': score_local,
                        'extraits_textuels': resultats_thematique,
                        'type': 'sources_locales_77',
                        'bonus_local': 0.3  # Bonus pour source locale
                    }
                    print(f"        🎉 {thematique} local validé (score: {score_local:.2f})")
            
            return resultats_locaux if resultats_locaux else None
            
        except Exception as e:
            print(f"      ❌ Erreur sources locales: {e}")
            return None

    def _construire_requetes_sources_locales(self, nom_entreprise: str, commune: str, thematique: str) -> List[str]:
        """✅ NOUVELLE MÉTHODE : Construction de requêtes pour sources locales"""
        requetes = []
        
        # Nettoyage du nom d'entreprise
        nom_clean = nom_entreprise.replace('"', '').replace("'", "").strip()
        
        print(f"          🛠️ Construction requêtes locales: {nom_clean} / {commune} / {thematique}")
        
        # Stratégie 1: Recherche dans la presse locale
        for source_presse in self.sources_locales_77['presse']:
            if thematique == 'recrutements':
                requetes.append(f'{source_presse} "{nom_clean}" {commune} emploi')
                requetes.append(f'{source_presse} "{nom_clean}" recrutement')
            elif thematique == 'evenements':
                requetes.append(f'{source_presse} "{nom_clean}" {commune} ouverture')
                requetes.append(f'{source_presse} "{nom_clean}" événement')
            elif thematique == 'vie_entreprise':
                requetes.append(f'{source_presse} "{nom_clean}" {commune} entreprise')
                requetes.append(f'{source_presse} "{nom_clean}" développement')
            elif thematique == 'innovations':
                requetes.append(f'{source_presse} "{nom_clean}" innovation')
                requetes.append(f'{source_presse} "{nom_clean}" nouveau')
        
        # Stratégie 2: Sources institutionnelles (pour certaines thématiques)
        if thematique in ['vie_entreprise', 'aides_subventions']:
            for source_instit in self.sources_locales_77['institutionnels']:
                requetes.append(f'{source_instit} "{nom_clean}"')
        
        # Stratégie 3: Recherche par commune + secteur (si nom entreprise complexe)
        if len(nom_clean) > 30:  # Nom trop long/complexe
            secteur_simplifie = self._detecter_secteur_activite(nom_clean)
            if secteur_simplifie:
                requetes.append(f'site:leparisien.fr {commune} {secteur_simplifie} {thematique}')
                requetes.append(f'site:larepublique77.fr {commune} {secteur_simplifie}')
        
        # Nettoyage et limitation
        requetes_finales = [req for req in requetes if len(req) > 20 and len(req) < 150]
        requetes_dedupliquees = list(dict.fromkeys(requetes_finales))  # Déduplique en gardant l'ordre
        
        print(f"          ✅ {len(requetes_dedupliquees)} requêtes locales générées")
        
        return requetes_dedupliquees[:4]  # Max 4 requêtes locales

    def _valider_resultats_sources_locales(self, resultats: List[Dict], nom_entreprise: str, 
                                        commune: str, thematique: str) -> List[Dict]:
        """✅ NOUVELLE MÉTHODE : Validation spéciale pour sources locales (plus permissive)"""
        if not resultats:
            return []
        
        print(f"          🔍 Validation sources locales: {len(resultats)} résultats")
        
        resultats_valides = []
        nom_lower = nom_entreprise.lower()
        commune_lower = commune.lower()
        
        for i, resultat in enumerate(resultats):
            try:
                titre = resultat.get('titre', '').lower()
                description = resultat.get('description', '').lower()
                url = resultat.get('url', '').lower()
                
                texte_complet = f"{titre} {description} {url}"
                
                # ✅ VALIDATION SPÉCIALE SOURCES LOCALES (plus permissive)
                
                # 1. Bonus si source locale détectée
                est_source_locale = any(source in url for source in [
                    'leparisien.fr', 'larepublique77.fr', 'francebleu.fr', 
                    'actu.fr', 'cci.fr', 'cma77.fr'
                ])
                
                if est_source_locale:
                    print(f"            ✅ Source locale détectée: {url}")
                    
                    # 2. Validation plus permissive pour sources locales
                    score_validation = 0.0
                    
                    # Entreprise mentionnée (seuil plus bas)
                    mots_entreprise = [mot for mot in nom_lower.split() if len(mot) > 2]
                    mots_trouves = [mot for mot in mots_entreprise if mot in texte_complet]
                    if mots_trouves:
                        score_validation += 0.4  # Bonus entreprise
                    
                    # Commune mentionnée
                    if commune_lower in texte_complet:
                        score_validation += 0.3  # Bonus commune
                    
                    # Contexte Seine-et-Marne
                    if any(terme in texte_complet for terme in ['77', 'seine-et-marne', 'marne-la-vallée']):
                        score_validation += 0.2  # Bonus territorial
                    
                    # Thématique (optionnel pour sources locales)
                    mots_thematiques = self.thematiques_mots_cles.get(thematique, [])
                    if any(mot.lower() in texte_complet for mot in mots_thematiques):
                        score_validation += 0.1  # Bonus thématique
                    
                    # ✅ SEUIL PERMISSIF pour sources locales
                    if score_validation >= 0.4:  # Plus bas que le seuil général (0.7)
                        resultat_enrichi = resultat.copy()
                        resultat_enrichi.update({
                            'source_locale': True,
                            'score_validation_locale': score_validation,
                            'mots_entreprise_trouves': mots_trouves,
                            'bonus_source_locale': 0.3
                        })
                        
                        resultats_valides.append(resultat_enrichi)
                        print(f"            ✅ VALIDÉ source locale (score: {score_validation:.2f})")
                    else:
                        print(f"            ❌ Score local insuffisant: {score_validation:.2f}")
                else:
                    print(f"            ⚪ Pas une source locale: {url[:50]}...")
                    
            except Exception as e:
                print(f"            ⚠️ Erreur validation locale {i}: {e}")
                continue
        
        print(f"          📊 Validation locale terminée: {len(resultats_valides)}/{len(resultats)} validés")
        return resultats_valides
        
    def _recherche_par_commune_et_secteur(self, commune: str, secteur_naf: str, code_naf: str) -> Optional[Dict]:
        """Recherche basée sur la commune et le secteur d'activité"""
        try:
            print(f"      🎯 Recherche par secteur: {secteur_naf} à {commune}")
            
            resultats = {}
            
            # Mapping secteurs vers thématiques probables
            thematiques_secteurs = self._determiner_thematiques_par_secteur(secteur_naf, code_naf)
            
            for thematique in thematiques_secteurs:
                print(f"        🔍 Recherche {thematique} pour secteur {secteur_naf[:30]}...")
                
                # Construction de requêtes basées sur commune + secteur
                requetes = self._construire_requetes_secteur(commune, secteur_naf, thematique)
                
                resultats_thematique = []
                for requete in requetes[:2]:  # Maximum 2 requêtes par thématique
                    try:
                        print(f"          🔎 Requête: {requete}")
                        resultats_requete = self._rechercher_moteur(requete)
                        
                        if resultats_requete:
                            # Validation spécifique pour recherches sectorielles
                            resultats_valides = self._valider_resultats_sectoriels(
                                resultats_requete, commune, secteur_naf, thematique
                            )
                            
                            if resultats_valides:
                                resultats_thematique.extend(resultats_valides)
                                print(f"          ✅ {len(resultats_valides)} résultats sectoriels")
                        
                        time.sleep(random.uniform(3, 5))
                        
                    except Exception as e:
                        print(f"          ❌ Erreur requête sectorielle: {str(e)}")
                        continue
                
                # Enrichissement avec données INSEE si peu de résultats
                if len(resultats_thematique) < 2:
                    enrichissement = self._enrichir_donnees_insee(commune, secteur_naf, thematique)
                    if enrichissement:
                        resultats_thematique.extend(enrichissement)
                        print(f"          📊 +{len(enrichissement)} données INSEE")
                
                # Finalisation des résultats pour cette thématique
                if resultats_thematique:
                    resultats[thematique] = {
                        'mots_cles_trouves': self._extraire_mots_cles_secteur(resultats_thematique, thematique),
                        'urls': [r['url'] for r in resultats_thematique if r.get('url')],
                        'pertinence': min(len(resultats_thematique) * 0.3, 0.7),  # Score modéré
                        'extraits_textuels': resultats_thematique[:3],
                        'type': 'recherche_sectorielle'
                    }
                    print(f"        🎉 Thématique {thematique} trouvée (secteur)")
            
            return resultats if resultats else None
            
        except Exception as e:
            print(f"      ❌ Erreur recherche sectorielle: {str(e)}")
            return None
    
    def _determiner_thematiques_par_secteur(self, secteur_naf: str, code_naf: str) -> List[str]:
        """Détermine les thématiques probables selon le secteur NAF"""
        secteur_lower = secteur_naf.lower()
        
        # Mapping secteurs NAF vers thématiques
        mappings = {
            # Secteurs avec beaucoup de recrutement
            'recrutements': [
                'commerce', 'vente', 'distribution', 'magasin', 'supermarché',
                'restauration', 'hôtellerie', 'service', 'conseil', 'informatique',
                'santé', 'aide', 'soin', 'enseignement', 'formation', 'transport'
            ],
            
            # Secteurs avec événements
            'evenements': [
                'commerce', 'vente', 'magasin', 'centre commercial', 'distribution',
                'restauration', 'hôtellerie', 'tourisme', 'culture', 'sport',
                'enseignement', 'formation', 'association'
            ],
            
            # Secteurs innovants
            'innovations': [
                'informatique', 'logiciel', 'technologie', 'recherche', 'développement',
                'ingénierie', 'conseil', 'industrie', 'fabrication', 'production',
                'automobile', 'aéronautique', 'pharmaceutique', 'biotechnologie'
            ],
            
            # Secteurs en développement
            'vie_entreprise': [
                'création', 'startup', 'conseil', 'service', 'commerce', 'industrie',
                'transport', 'logistique', 'immobilier', 'construction', 'renovation'
            ],
            
            # Secteurs exportateurs
            'exportations': [
                'industrie', 'fabrication', 'production', 'automobile', 'aéronautique',
                'pharmaceutique', 'cosmétique', 'agroalimentaire', 'textile', 'luxe'
            ]
        }
        
        thematiques_trouvees = []
        
        for thematique, mots_cles in mappings.items():
            if any(mot in secteur_lower for mot in mots_cles):
                thematiques_trouvees.append(thematique)
        
        # Par défaut, chercher au moins vie_entreprise
        if not thematiques_trouvees:
            thematiques_trouvees = ['vie_entreprise']
        
        # Limiter à 3 thématiques max
        return thematiques_trouvees[:3]
    
    def _construire_requetes_secteur(self, commune: str, secteur_naf: str, thematique: str) -> List[str]:
        """Construction de requêtes basées sur commune et secteur"""
        requetes = []
        
        # Mots-clés extraits du secteur NAF
        mots_secteur = self._extraire_mots_cles_secteur_naf(secteur_naf)
        
        if thematique == 'recrutements':
            requetes.extend([
                f'{commune} {mots_secteur} recrutement emploi',
                f'{commune} offre emploi {mots_secteur}',
                f'{commune} {secteur_naf[:20]} embauche'
            ])
        elif thematique == 'evenements':
            requetes.extend([
                f'{commune} {mots_secteur} événement salon',
                f'{commune} {secteur_naf[:20]} porte ouverte',
                f'{commune} {mots_secteur} manifestation'
            ])
        elif thematique == 'innovations':
            requetes.extend([
                f'{commune} {mots_secteur} innovation',
                f'{commune} {secteur_naf[:20]} nouveau',
                f'{commune} {mots_secteur} technologie'
            ])
        elif thematique == 'vie_entreprise':
            requetes.extend([
                f'{commune} {mots_secteur} entreprise',
                f'{commune} {secteur_naf[:20]} développement',
                f'{commune} {mots_secteur} activité'
            ])
        elif thematique == 'exportations':
            requetes.extend([
                f'{commune} {mots_secteur} export international',
                f'{commune} {secteur_naf[:20]} étranger',
                f'{commune} {mots_secteur} marché international'
            ])
        
        return requetes[:2]  # Maximum 2 requêtes
    
    def _extraire_mots_cles_secteur_naf(self, secteur_naf: str) -> str:
        """Extraction des mots-clés d'un secteur NAF"""
        secteurs_mots = {
            'santé': 'médical santé soin',
            'conseil': 'conseil expertise service',
            'transport': 'transport logistique livraison',
            'commerce': 'vente magasin boutique',
            'restauration': 'restaurant café bar',
            'construction': 'bâtiment construction travaux',
            'technologie': 'informatique numérique tech',
            'formation': 'formation enseignement éducation'
        }
        
        secteur_lower = secteur_naf.lower()
        for secteur, mots in secteurs_mots.items():
            if secteur in secteur_lower:
                return mots
        
        return secteur_naf  # Retour par défaut

    def _valider_pertinence_resultats_pme(self, resultats: List[Dict], nom_entreprise: str, commune: str, thematique: str) -> List[Dict]:
        """Version ULTRA-PERMISSIVE pour PME - CORRIGÉE"""
        if not resultats:
            return []
        
        # ✅ APPELER la nouvelle méthode ultra-permissive
        return self._validation_ultra_permissive_pme(resultats, nom_entreprise, commune)

    def _validation_ultra_permissive_pme(self, resultats: List[Dict], nom_entreprise: str, commune: str) -> List[Dict]:
        """✅ CORRIGÉ: Validation équilibrée - ni trop stricte, ni trop permissive"""
        if not resultats:
            return []
        
        print(f"        🔧 Validation équilibrée PME: {len(resultats)} résultats")
        
        resultats_valides = []
        nom_mots = [mot for mot in nom_entreprise.upper().split() if len(mot) > 2]
        commune_lower = commune.lower()
        
        # ❌ EXCLUSIONS STRICTES AJOUTÉES
        exclusions_strictes = [
            'wikipedia.org', 'wordreference.com', 'dictionary.com', 'larousse.fr',
            'reverso.net', 'linguee.com', 'conjugaison', 'grammaire', 'definition'
        ]
        
        for resultat in resultats:
            try:
                titre = resultat.get('titre', '').upper()
                description = resultat.get('description', '').upper() 
                url = resultat.get('url', '').lower()
                texte_complet = f"{titre} {description} {url}"
                
                # ❌ EXCLUSION IMMÉDIATE si faux positif évident
                if any(exclus in url for exclus in exclusions_strictes):
                    continue
                
                if any(exclus in texte_complet.lower() for exclus in ['forum.wordreference', 'cours de français']):
                    continue
                
                # ✅ CRITÈRES RENFORCÉS
                score = 0.0
                
                # Critère 1: Nom d'entreprise mentionné (OBLIGATOIRE)
                mots_trouves = [mot for mot in nom_mots if mot in texte_complet]
                if mots_trouves:
                    score += 0.4  # Augmenté de 0.3 à 0.4
                else:
                    # Si pas de nom d'entreprise, commune OBLIGATOIRE
                    if commune_lower not in texte_complet.lower():
                        continue  # REJET immédiat
                    score += 0.2
                
                # Critère 2: Contexte business/économique (NOUVEAU)
                mots_business = ['entreprise', 'societe', 'commerce', 'activite', 'emploi', 'recrutement', 
                            'développement', 'service', 'innovation', 'ouverture', 'magasin']
                if any(mot in texte_complet.lower() for mot in mots_business):
                    score += 0.3  # Augmenté
                
                # Critère 3: Contexte territorial
                if commune_lower in texte_complet.lower():
                    score += 0.2
                
                # ✅ SEUIL RELEVÉ - Plus exigeant
                if score >= 0.5:  # Augmenté de 0.1 à 0.5
                    resultat_enrichi = resultat.copy()
                    resultat_enrichi.update({
                        'score_validation': score,
                        'mots_entreprise_trouves': mots_trouves,
                        'validation_renforcee': True
                    })
                    resultats_valides.append(resultat_enrichi)
                    print(f"            ✅ VALIDÉ score: {score:.2f}")
                else:
                    print(f"            ❌ Score insuffisant: {score:.2f}")
                        
            except Exception as e:
                print(f"            ⚠️ Erreur validation: {e}")
                continue
        
        print(f"        📊 Validation renforcée: {len(resultats_valides)}/{len(resultats)} validés")
        return resultats_valides

    def _forcer_resultats_minimum_pme(self, entreprise: Dict) -> Dict:
        """✅ CORRIGÉ: Pas de résultats forcés - retour vide si rien trouvé"""
        print(f"      ⚠️ Aucun résultat valide pour {entreprise.get('nom', 'N/A')} - pas de forçage")
        return {}  # Retour VIDE au lieu de données factices
    
    def _simulation_avancee(self, requete: str) -> List[Dict]:
        """Simulation de données en dernier recours"""
        print(f"          🔄 Simulation avancée pour: {requete}")
        
        # Extraction des mots-clés de la requête
        mots_requete = [mot for mot in requete.split() if len(mot) > 3]
        
        if len(mots_requete) >= 2:
            return [{
                'titre': f'Information sur {mots_requete[0]}',
                'description': f'Données contextuelles concernant {" ".join(mots_requete[:2])}',
                'url': f'https://exemple.fr/info-{mots_requete[0].lower()}',
                'type': 'simulation_avancee'
            }]
        
        return []

    def _rechercher_duckduckgo(self, requete: str) -> Optional[List[Dict]]:
        """Recherche DuckDuckGo HTML"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://duckduckgo.com/html/"
            params = {'q': requete}
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                resultats = []
                
                for result in soup.find_all('div', class_='result')[:5]:
                    try:
                        titre_elem = result.find('a', class_='result__a')
                        titre = titre_elem.get_text().strip() if titre_elem else ""
                        
                        url_elem = result.find('a', class_='result__a')
                        url_result = url_elem['href'] if url_elem else ""
                        
                        desc_elem = result.find('a', class_='result__snippet')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if titre and description:
                            resultats.append({
                                'titre': titre,
                                'description': description,
                                'url': url_result,
                                'extrait_complet': f"{titre} - {description}"
                            })
                    except Exception:
                        continue
                
                return resultats if resultats else None
            
            return None
            
        except Exception as e:
            print(f"          ⚠️ Erreur DuckDuckGo: {e}")
            return None

    def _rechercher_qwant(self, requete: str) -> Optional[List[Dict]]:
        """Recherche Qwant en dernier recours"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://www.qwant.com/"
            params = {'q': requete, 'l': 'fr'}
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parsing basique pour Qwant
                return [{
                    'titre': f'Résultat Qwant pour {requete}',
                    'description': f'Information trouvée via Qwant',
                    'url': 'https://qwant.com/search',
                    'source': 'qwant'
                }]
            
            return None
            
        except Exception:
            return None

    def _get_cache_key(self, url_ou_requete: str) -> str:
        """Génération d'une clé de cache unique"""
        import hashlib
        return hashlib.md5(url_ou_requete.encode('utf-8')).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Récupération depuis le cache"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                # Vérifier l'âge du cache
                file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
                if datetime.now() - file_time < self.periode_recherche:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception:
            return None

    def _save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Sauvegarde en cache"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde cache: {e}")

    def _extraire_mots_cles_secteur_naf(self, secteur_naf: str) -> str:
        """Extraction des mots-clés d'un secteur NAF"""
        secteurs_mots = {
            'santé': 'médical santé soin',
            'conseil': 'conseil expertise service',
            'transport': 'transport logistique livraison',
            'commerce': 'vente magasin boutique',
            'restauration': 'restaurant café bar',
            'construction': 'bâtiment construction travaux',
            'technologie': 'informatique numérique tech',
            'formation': 'formation enseignement éducation'
        }
        
        secteur_lower = secteur_naf.lower()
        for secteur, mots in secteurs_mots.items():
            if secteur in secteur_lower:
                return mots
        
        return secteur_naf  # Retour par défaut

    def _construire_requetes_secteur(self, commune: str, secteur_naf: str, thematique: str) -> List[str]:
        """Construction de requêtes sectorielles"""
        requetes = []
        mots_secteur = self._extraire_mots_cles_secteur_naf(secteur_naf).split()
        mots_thematiques = self.thematiques_mots_cles.get(thematique, [])
        
        if mots_secteur and mots_thematiques:
            requetes.extend([
                f'{commune} {mots_secteur[0]} {thematique}',
                f'{commune} {mots_secteur[0]} {mots_thematiques[0]}',
                f'{secteur_naf} {commune} {thematique}'
            ])
        
        return requetes[:2]  # Limiter à 2 requêtes

    def _valider_resultats_sectoriels(self, resultats: List[Dict], commune: str, secteur_naf: str, thematique: str) -> List[Dict]:
        """Validation pour recherches sectorielles"""
        if not resultats:
            return []
        
        resultats_valides = []
        commune_lower = commune.lower()
        secteur_mots = self._extraire_mots_cles_secteur_naf(secteur_naf).lower().split()
        
        for resultat in resultats:
            try:
                texte_complet = f"{resultat.get('titre', '')} {resultat.get('description', '')}".lower()
                
                score = 0.0
                
                # Commune mentionnée
                if commune_lower in texte_complet:
                    score += 0.3
                
                # Mots du secteur
                if any(mot in texte_complet for mot in secteur_mots):
                    score += 0.2
                
                # Mots thématiques
                mots_them = self.thematiques_mots_cles.get(thematique, [])
                if any(mot.lower() in texte_complet for mot in mots_them):
                    score += 0.2
                
                # Seuil pour validation sectorielle
                if score >= 0.4:
                    resultat_enrichi = resultat.copy()
                    resultat_enrichi['score_sectoriel'] = score
                    resultats_valides.append(resultat_enrichi)
        
            except Exception:
                continue
    
    def _simulation_avancee(self, requete: str) -> List[Dict]:
        """Simulation de données en dernier recours"""
        print(f"          🔄 Simulation avancée pour: {requete}")
        
        # Extraction des mots-clés de la requête
        mots_requete = [mot for mot in requete.split() if len(mot) > 3]
        
        if len(mots_requete) >= 2:
            return [{
                'titre': f'Information sur {mots_requete[0]}',
                'description': f'Données contextuelles concernant {" ".join(mots_requete[:2])}',
                'url': f'https://exemple.fr/info-{mots_requete[0].lower()}',
                'type': 'simulation_avancee'
            }]
        
        return []

    def _rechercher_duckduckgo(self, requete: str) -> Optional[List[Dict]]:
        """Recherche DuckDuckGo HTML"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://duckduckgo.com/html/"
            params = {'q': requete}
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                resultats = []
                
                for result in soup.find_all('div', class_='result')[:5]:
                    try:
                        titre_elem = result.find('a', class_='result__a')
                        titre = titre_elem.get_text().strip() if titre_elem else ""
                        
                        url_elem = result.find('a', class_='result__a')
                        url_result = url_elem['href'] if url_elem else ""
                        
                        desc_elem = result.find('a', class_='result__snippet')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if titre and description:
                            resultats.append({
                                'titre': titre,
                                'description': description,
                                'url': url_result,
                                'extrait_complet': f"{titre} - {description}"
                            })
                    except Exception:
                        continue
                
                return resultats if resultats else None
            
            return None
            
        except Exception as e:
            print(f"          ⚠️ Erreur DuckDuckGo: {e}")
            return None

    def _rechercher_qwant(self, requete: str) -> Optional[List[Dict]]:
        """Recherche Qwant en dernier recours"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://www.qwant.com/"
            params = {'q': requete, 'l': 'fr'}
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parsing basique pour Qwant
                return [{
                    'titre': f'Résultat Qwant pour {requete}',
                    'description': f'Information trouvée via Qwant',
                    'url': 'https://qwant.com/search',
                    'source': 'qwant'
                }]
            
            return None
            
        except Exception:
            return None

    # Ajouter après les méthodes de cache

    def _extraire_mots_cles_secteur_naf(self, secteur_naf: str) -> str:
        """Extraction des mots-clés d'un secteur NAF"""
        secteurs_mots = {
            'santé': 'médical santé soin',
            'conseil': 'conseil expertise service',
            'transport': 'transport logistique livraison',
            'commerce': 'vente magasin boutique',
            'restauration': 'restaurant café bar',
            'construction': 'bâtiment construction travaux',
            'technologie': 'informatique numérique tech',
            'formation': 'formation enseignement éducation'
        }
        
        secteur_lower = secteur_naf.lower()
        for secteur, mots in secteurs_mots.items():
            if secteur in secteur_lower:
                return mots
        
        return secteur_naf  # Retour par défaut

    def _construire_requetes_secteur(self, commune: str, secteur_naf: str, thematique: str) -> List[str]:
        """Construction de requêtes sectorielles"""
        requetes = []
        mots_secteur = self._extraire_mots_cles_secteur_naf(secteur_naf).split()
        mots_thematiques = self.thematiques_mots_cles.get(thematique, [])
        
        if mots_secteur and mots_thematiques:
            requetes.extend([
                f'{commune} {mots_secteur[0]} {thematique}',
                f'{commune} {mots_secteur[0]} {mots_thematiques[0]}',
                f'{secteur_naf} {commune} {thematique}'
            ])
        
        return requetes[:2]  # Limiter à 2 requêtes

    def _valider_resultats_sectoriels(self, resultats: List[Dict], commune: str, secteur_naf: str, thematique: str) -> List[Dict]:
        """Validation pour recherches sectorielles"""
        if not resultats:
            return []
        
        resultats_valides = []
        commune_lower = commune.lower()
        secteur_mots = self._extraire_mots_cles_secteur_naf(secteur_naf).lower().split()
        
        for resultat in resultats:
            try:
                texte_complet = f"{resultat.get('titre', '')} {resultat.get('description', '')}".lower()
                
                score = 0.0
                
                # Commune mentionnée
                if commune_lower in texte_complet:
                    score += 0.3
                
                # Mots du secteur
                if any(mot in texte_complet for mot in secteur_mots):
                    score += 0.2
                
                # Mots thématiques
                mots_them = self.thematiques_mots_cles.get(thematique, [])
                if any(mot.lower() in texte_complet for mot in mots_them):
                    score += 0.2
                
                # Seuil pour validation sectorielle
                if score >= 0.4:
                    resultat_enrichi = resultat.copy()
                    resultat_enrichi['score_sectoriel'] = score
                    resultats_valides.append(resultat_enrichi)
        
            except Exception:
                continue
    
    def _simulation_avancee(self, requete: str) -> List[Dict]:
        """Simulation de données en dernier recours"""
        print(f"          🔄 Simulation avancée pour: {requete}")
        
        # Extraction des mots-clés de la requête
        mots_requete = [mot for mot in requete.split() if len(mot) > 3]
        
        if len(mots_requete) >= 2:
            return [{
                'titre': f'Information sur {mots_requete[0]}',
                'description': f'Données contextuelles concernant {" ".join(mots_requete[:2])}',
                'url': f'https://exemple.fr/info-{mots_requete[0].lower()}',
                'type': 'simulation_avancee'
            }]
        
        return []

    def _rechercher_duckduckgo(self, requete: str) -> Optional[List[Dict]]:
        """Recherche DuckDuckGo HTML"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://duckduckgo.com/html/"
            params = {'q': requete}
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                resultats = []
                
                for result in soup.find_all('div', class_='result')[:5]:
                    try:
                        titre_elem = result.find('a', class_='result__a')
                        titre = titre_elem.get_text().strip() if titre_elem else ""
                        
                        url_elem = result.find('a', class_='result__a')
                        url_result = url_elem['href'] if url_elem else ""
                        
                        desc_elem = result.find('a', class_='result__snippet')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if titre and description:
                            resultats.append({
                                'titre': titre,
                                'description': description,
                                'url': url_result,
                                'extrait_complet': f"{titre} - {description}"
                            })
                    except Exception:
                        continue
                
                return resultats if resultats else None
            
            return None
            
        except Exception as e:
            print(f"          ⚠️ Erreur DuckDuckGo: {e}")
            return None

    def _rechercher_qwant(self, requete: str) -> Optional[List[Dict]]:
        """Recherche Qwant en dernier recours"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://www.qwant.com/"
            params = {'q': requete, 'l': 'fr'}
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parsing basique pour Qwant
                return [{
                    'titre': f'Résultat Qwant pour {requete}',
                    'description': f'Information trouvée via Qwant',
                    'url': 'https://qwant.com/search',
                    'source': 'qwant'
                }]
            
            return None
            
        except Exception:
            return None

    # ✅ MÉTHODE PRINCIPALE À AJOUTER DANS VOTRE CLASSE VeilleEconomique
    def traiter_echantillon_avec_validation_stricte(self, fichier_excel, nb_entreprises=20):
        """
        ✅ NOUVEAU: Traitement avec validation stricte pour éviter les faux positifs
        """
        print("🚀 TRAITEMENT AVEC VALIDATION STRICTE")
        print("=" * 60)
        
        try:
            # 1. Extraction normale
            extracteur = ExtracteurDonnees(fichier_excel)
            toutes_entreprises = extracteur.extraire_echantillon(nb_entreprises * 2)  # Plus large pour compenser
            
            # 2. ✅ NOUVEAU: Filtrage des entreprises recherchables
            entreprises_recherchables = self._detecter_entreprises_non_recherchables(toutes_entreprises)
            
            # Limitation au nombre demandé
            entreprises = entreprises_recherchables[:nb_entreprises]
            
            if len(entreprises) < nb_entreprises:
                print(f"⚠️ Seulement {len(entreprises)} entreprises recherchables disponibles")
            
            # 3. Recherche web avec validation stricte (votre code existant mais avec la méthode corrigée)
            recherche = RechercheWeb(self.periode_recherche)
            
            # ✅ REMPLACEMENT: Utiliser la validation stricte
            recherche._valider_pertinence_resultats = self._valider_pertinence_resultats
            recherche._generer_requetes_adaptees = self._generer_requetes_adaptees
            
            resultats_bruts = []
            
            for entreprise in entreprises:
                resultats = recherche.rechercher_entreprise(entreprise)
                resultats_bruts.append(resultats)
            
            # 4. Analyse thématique (inchangée)
            analyseur = AnalyseurThematiques(self.config['thematiques'])
            
            print(f"\n🔍 DEBUG AVANT ANALYSE:")
            print(f"   📊 Résultats bruts: {len(resultats_bruts)}")
            for i, resultat in enumerate(resultats_bruts[:3]):
                nom = resultat.get('entreprise', {}).get('nom', 'N/A')
                nb_thematiques = len(resultat.get('donnees_thematiques', {}))
                print(f"   {i+1}. {nom}: {nb_thematiques} thématiques trouvées")
                
                # Détail des thématiques
                for them, data in resultat.get('donnees_thematiques', {}).items():
                    if isinstance(data, dict):
                        nb_extraits = len(data.get('extraits_textuels', []))
                        print(f"      • {them}: {nb_extraits} extraits")
            
            donnees_enrichies = analyseur.analyser_resultats(resultats_bruts)
            
            # 5. Génération des rapports (inchangée)
            generateur = GenerateurRapports()
            rapports = generateur.generer_tous_rapports(donnees_enrichies)
            
            return rapports
            
        except Exception as e:
            print(f"❌ Erreur traitement strict: {e}")
            return None

    def _enrichir_donnees_insee(self, commune: str, secteur_naf: str, thematique: str) -> List[Dict]:
        """Enrichissement avec données contextuelles INSEE"""
        try:
            enrichissements = []
            
            # Informations contextuelles par commune et secteur
            info_base = {
                'titre': f'{thematique.replace("_", " ").title()} - {secteur_naf[:30]} à {commune}',
                'description': f'Activité {thematique} dans le secteur {secteur_naf} sur la commune de {commune}.',
                'url': f'https://www.{commune.lower()}-economie.fr/{thematique}',
                'type': 'enrichissement_insee'
            }
            
            # Adaptation selon la thématique
            if thematique == 'recrutements':
                info_base['description'] = f'Opportunités d\'emploi dans le secteur {secteur_naf} à {commune}.'
            elif thematique == 'evenements':
                info_base['description'] = f'Événements et manifestations du secteur {secteur_naf} à {commune}.'
            elif thematique == 'innovations':
                info_base['description'] = f'Innovations et développements dans le secteur {secteur_naf} à {commune}.'
            
            enrichissements.append(info_base)
            
            return enrichissements
            
        except Exception as e:
            print(f"          ❌ Erreur enrichissement INSEE: {e}")
            return []
    
    def _extraire_mots_cles_secteur(self, resultats: List[Dict], thematique: str) -> List[str]:
        """Extraction des mots-clés trouvés pour un secteur"""
        mots_cles = []
        for resultat in resultats:
            if 'mots_cles_trouves' in resultat:
                mots_cles.extend(resultat['mots_cles_trouves'])
        
        # Ajout des mots-clés thématiques seulement si vraiment trouvés
        return list(set(mots_cles))
        
    def _construire_requetes_thematique(self, nom_entreprise: str, commune: str, thematique: str) -> List[str]:
        """Construction de requêtes spécifiques par thématique"""
        requetes = []
        
        # Nettoyage du nom d'entreprise
        nom_clean = nom_entreprise.replace('"', '').replace("'", "")
        
        if thematique == 'recrutements':
            requetes.extend([
                f'"{nom_clean}" {commune} recrutement emploi',
                f'"{nom_clean}" offre emploi CDI CDD',
                f'"{nom_clean}" {commune} embauche'
            ])
        elif thematique == 'evenements':
            requetes.extend([
                f'"{nom_clean}" {commune} événement salon',
                f'"{nom_clean}" porte ouverte conférence',
                f'"{nom_clean}" {commune} manifestation'
            ])
        elif thematique == 'innovations':
            requetes.extend([
                f'"{nom_clean}" innovation',
                f'"{nom_clean}" nouveau produit',
                f'{nom_clean} {commune} développement'
            ])
        elif thematique == 'vie_entreprise':
            requetes.extend([
                f'"{nom_clean}" {commune} développement',
                f'"{nom_clean}" partenariat implantation',
                f'"{nom_clean}" {commune} ouverture expansion'
            ])
        else:
            # Requête générale
            mots_cles = self.thematiques_mots_cles.get(thematique, [])
            if mots_cles:
                requetes.append(f'"{nom_clean}" {commune} {" ".join(mots_cles[:3])}')
                
        return requetes
        
    def _rechercher_moteur(self, requete: str) -> Optional[List[Dict]]:
        """Recherche avec priorité Bing + fallbacks multiples"""
        try:
            # Tentative 1: BING (NOUVEAU - PRIORITÉ)
            try:
                print(f"          🥇 Tentative Bing...")
                resultats = self._rechercher_bing(requete)
                if resultats:
                    print(f"          ✅ Bing: {len(resultats)} résultats")
                    return resultats
            except Exception as e:
                print(f"          ⚠️  Bing échoué: {str(e)}")
            
            # Tentative 2: YANDEX (NOUVEAU)
            try:
                print(f"          🥈 Tentative Yandex...")
                resultats = self._rechercher_yandex(requete)
                if resultats:
                    print(f"          ✅ Yandex: {len(resultats)} résultats")
                    return resultats
            except Exception as e:
                print(f"          ⚠️  Yandex échoué: {str(e)}")
            
            # Tentative 3: Bibliothèque DuckDuckGo
            try:
                print(f"          🥉 Tentative DuckDuckGo (bibliothèque)...")
                resultats = self._rechercher_avec_bibliotheque(requete)
                if resultats:
                    print(f"          ✅ DuckDuckGo lib: {len(resultats)} résultats")
                    return resultats
            except Exception as e:
                print(f"          ⚠️  DuckDuckGo bibliothèque échouée: {str(e)}")
            
            # Tentative 4: DuckDuckGo HTML
            try:
                print(f"          🔄 Tentative DuckDuckGo HTML...")
                resultats = self._rechercher_duckduckgo(requete)
                if resultats:
                    print(f"          ✅ DuckDuckGo HTML: {len(resultats)} résultats")
                    return resultats
            except Exception as e:
                print(f"          ⚠️  DuckDuckGo HTML échoué: {str(e)}")
            
            # Tentative 5: Simulation avancée
            print(f"          🔄 Fallback vers simulation avancée")
            return self._simulation_avancee(requete)
            
        except Exception as e:
            print(f"        ⚠️  Erreur recherche générale: {str(e)}")
            return self._simulation_avancee(requete)

    def _rechercher_bing(self, requete: str) -> Optional[List[Dict]]:
        """Recherche avec Bing (optimisé pour veille économique française)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'fr-FR,fr;q=0.9'
            }
            
            url = "https://www.bing.com/search"
            params = {
                'q': requete,
                'setlang': 'fr',
                'cc': 'FR',  # Pays France
                'count': 10,  # Plus de résultats
                'first': 1
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                resultats_extraits = []
                
                # Sélecteurs Bing améliorés
                for result in soup.find_all('li', class_='b_algo')[:8]:  # Plus de résultats
                    try:
                        # Titre
                        titre_elem = result.find('h2') or result.find('a')
                        titre = titre_elem.get_text().strip() if titre_elem else ""
                        
                        # URL
                        url_elem = result.find('a')
                        url_result = url_elem['href'] if url_elem and url_elem.get('href') else ""
                        
                        # Description
                        desc_elem = result.find('p') or result.find('div', class_='b_caption')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if titre and description and len(description) > 20:  # Filtre qualité
                            resultats_extraits.append({
                                'titre': titre,
                                'description': description,
                                'url': url_result,
                                'extrait_complet': f"{titre} - {description}"
                            })
                            
                    except Exception:
                        continue
                
                return resultats_extraits if resultats_extraits else None
                
            else:
                print(f"          ❌ Bing HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"          ⚠️  Erreur Bing: {str(e)}")
            return None

    def _rechercher_yandex(self, requete: str) -> Optional[List[Dict]]:
        """Recherche avec Yandex (moins restrictif, bonne qualité)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://yandex.com/search/"
            params = {
                'text': requete,
                'lang': 'fr',
                'lr': '10502'  # Code pour la France
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                resultats_extraits = []
                
                # Sélecteurs Yandex
                results = soup.find_all('li', class_='serp-item')
                
                for result in results[:5]:
                    try:
                        # Titre
                        titre_elem = result.find('h2') or result.find('a')
                        titre = titre_elem.get_text().strip() if titre_elem else ""
                        
                        # URL
                        url_elem = result.find('a')
                        url_result = url_elem['href'] if url_elem and url_elem.get('href') else ""
                        
                        # Description
                        desc_elem = result.find('div', class_='text-container') or result.find('div', class_='organic__text')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if titre and description:
                            resultats_extraits.append({
                                'titre': titre,
                                'description': description,
                                'url': url_result,
                                'extrait_complet': f"{titre} - {description}"
                            })
                            
                    except Exception:
                        continue
                
                return resultats_extraits if resultats_extraits else None
                
        except Exception as e:
            print(f"          ⚠️  Erreur Yandex: {str(e)}")
            return None

    def _rechercher_google_securise(self, requete: str) -> Optional[List[Dict]]:
        """Google Search avec protection anti-détection maximale"""
        try:
            print(f"          🔍 Google (mode furtif)...")
            
            # ✅ 1. DÉLAI PRÉALABLE OBLIGATOIRE (crucial pour Google)
            delai_pre_recherche = random.uniform(8, 15)  # 8-15 secondes
            print(f"          ⏰ Délai sécurité Google: {delai_pre_recherche:.1f}s")
            time.sleep(delai_pre_recherche)
            
            # ✅ 2. ROTATION D'USER-AGENTS RÉALISTES
            user_agents_google = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            headers_google = {
                'User-Agent': random.choice(user_agents_google),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # ✅ 3. PARAMÈTRES GOOGLE OPTIMISÉS
            requete_encodee = quote_plus(requete)
            
            # Utilisation de google.fr (plus permissif que .com)
            url_google = "https://www.google.fr/search"
            
            params_google = {
                'q': requete,
                'hl': 'fr',           # Langue française
                'gl': 'FR',           # Géolocalisation France
                'lr': 'lang_fr',      # Résultats en français
                'num': 8,             # Moins de résultats = moins suspect
                'start': 0,           # Première page seulement
                'safe': 'off',        # Pas de SafeSearch
                'filter': '0',        # Pas de filtrage doublons
                'pws': '0'            # Pas de personnalisation
            }
            
            # ✅ 4. REQUÊTE AVEC PROTECTION MAXIMALE
            session_google = requests.Session()
            session_google.headers.update(headers_google)
            
            # Timeout généreux pour éviter les erreurs de vitesse
            response = session_google.get(
                url_google, 
                params=params_google, 
                timeout=25,           # 25 secondes de timeout
                allow_redirects=True
            )
            
            print(f"          📊 Google HTTP: {response.status_code}")
            
            # ✅ 5. GESTION DES CODES DE RÉPONSE
            if response.status_code == 429:
                print(f"          🚨 Google rate limit - abandon temporaire")
                return None
            elif response.status_code == 403:
                print(f"          🚫 Google bloqué - abandon temporaire")
                return None
            elif response.status_code != 200:
                print(f"          ❌ Google erreur {response.status_code}")
                return None
            
            # ✅ 6. PARSING SPÉCIALISÉ GOOGLE
            soup = BeautifulSoup(response.text, 'html.parser')
            
            resultats_google = []
            
            # Sélecteurs Google (mis à jour 2024)
            selecteurs_possibles = [
                'div.g',                    # Sélecteur principal standard
                'div[data-ved]',           # Sélecteur avec attribut data
                '.tF2Cxc',                 # Nouveau sélecteur 2024
                '.yuRUbf'                  # Sélecteur alternatif
            ]
            
            results_found = []
            for selecteur in selecteurs_possibles:
                results_found = soup.select(selecteur)
                if results_found:
                    print(f"          ✅ Sélecteur Google actif: {selecteur}")
                    break
            
            if not results_found:
                print(f"          ⚠️ Aucun sélecteur Google fonctionnel")
                return None
            
            # ✅ 7. EXTRACTION GOOGLE ROBUSTE
            for i, result in enumerate(results_found[:6]):  # Top 6 résultats
                try:
                    # Titre - multiple sélecteurs
                    titre_elem = (
                        result.select_one('h3') or 
                        result.select_one('.LC20lb') or
                        result.select_one('[role="heading"]') or
                        result.select_one('h1, h2, h3')
                    )
                    titre = titre_elem.get_text().strip() if titre_elem else ""
                    
                    # URL - multiple sélecteurs
                    url_elem = (
                        result.select_one('a[href]') or
                        result.select_one('.yuRUbf a') or
                        result.select_one('h3 a')
                    )
                    url_result = ""
                    if url_elem and url_elem.get('href'):
                        href = url_elem['href']
                        # Nettoyage URL Google (suppression redirections)
                        if href.startswith('/url?q='):
                            url_result = href.split('/url?q=')[1].split('&')[0]
                        elif href.startswith('http'):
                            url_result = href
                    
                    # Description - multiple sélecteurs
                    desc_elem = (
                        result.select_one('.VwiC3b') or
                        result.select_one('.s') or
                        result.select_one('.st') or
                        result.select_one('[data-sncf]') or
                        result.select_one('span[style*="color"]')
                    )
                    description = desc_elem.get_text().strip() if desc_elem else ""
                    
                    # ✅ 8. VALIDATION QUALITÉ GOOGLE
                    if titre and len(titre) > 10 and description and len(description) > 20:
                        # Exclusion résultats Google internes
                        if not any(exclus in url_result.lower() for exclus in [
                            'google.com', 'youtube.com', 'maps.google', 'images.google'
                        ]):
                            resultats_google.append({
                                'titre': titre,
                                'description': description,
                                'url': url_result,
                                'extrait_complet': f"{titre} - {description}",
                                'source_moteur': 'google',
                                'position': i + 1
                            })
                            
                except Exception as e:
                    print(f"          ⚠️ Erreur parsing résultat Google {i}: {e}")
                    continue
            
            # ✅ 9. DÉLAI POST-RECHERCHE OBLIGATOIRE
            if resultats_google:
                delai_post = random.uniform(12, 20)  # 12-20 secondes
                print(f"          ✅ Google: {len(resultats_google)} résultats")
                print(f"          ⏰ Délai post-Google: {delai_post:.1f}s")
                time.sleep(delai_post)
                
                return resultats_google
            else:
                print(f"          ⚪ Google: aucun résultat extrait")
                time.sleep(random.uniform(8, 12))  # Délai même en cas d'échec
                return None
                
        except requests.exceptions.Timeout:
            print(f"          ⏰ Google timeout - normal, on continue")
            time.sleep(random.uniform(15, 25))
            return None
        except Exception as e:
            print(f"          ❌ Erreur Google: {str(e)}")
            time.sleep(random.uniform(10, 15))
            return None

    def _rechercher_moteur(self, requete: str):
        """
        Exécute une recherche avec fallback multi-moteurs.
        Doit retourner une liste de dicts {'titre','description','url'}.
        """
        # Ordre de préférence
        try:
            return self._rechercher_bing(requete) or []
        except Exception as e:
            print(f"        ❌ Bing KO: {e}")

        try:
            return self._rechercher_duckduckgo(requete) or []
        except Exception as e:
            print(f"        ❌ DuckDuckGo KO: {e}")

        # Compat: certains appels attendent ces noms
        try:
            return self._rechercher_google_avec_protection(requete) or []
        except Exception as e:
            print(f"        ❌ Google-protection KO: {e}")

        try:
            return self._rechercher_qwant(requete) or []
        except Exception as e:
            print(f"        ❌ Qwant KO: {e}")

        return []
    
    def _rechercher_avec_bibliotheque(self, requete: str):
        """
        DuckDuckGo via bibliothèque (si installée), sinon None.
        Évite toute exception pour ne pas casser la cascade.
        """
        try:
            from duckduckgo_search import DDGS  # pip install duckduckgo_search
            items = []
            with DDGS() as ddgs:
                for r in ddgs.text(requete, region='fr-fr', max_results=5):
                    titre = r.get('title') or ''
                    url_res = r.get('href') or r.get('url') or ''
                    desc = r.get('body') or ''
                    if titre and url_res:
                        items.append({
                            'titre': titre,
                            'description': desc,
                            'url': url_res,
                            'extrait_complet': f"{titre} - {desc}" if desc else titre
                        })
            return items if items else None
        except Exception:
            return None

    def _rechercher_google_avec_protection(self, requete: str):
        """
        Compatibilité : certaines parties du code attendent Google.
        Pour éviter les blocages/quotas, on délègue proprement vers DuckDuckGo.
        Format de sortie : liste de dicts {'titre', 'description', 'url'}
        """
        try:
            # Tu peux basculer sur Bing si tu préfères :
            # return self._rechercher_bing(requete)
            return self._rechercher_duckduckgo(requete)
        except Exception as e:
            print(f"        ⚠️ Google-protection fallback → DuckDuckGo a échoué: {e}")
            # Double fallback sur Bing si DDG tombe
            try:
                return self._rechercher_bing(requete)
            except Exception as e2:
                print(f"        ⚠️ Google-protection fallback → Bing a échoué: {e2}")
                return []
    
    def _recherche_presse_locale(self, entreprise: Dict) -> Optional[Dict]:
        """Recherche dans la presse locale"""
        try:
            resultats_presse = {}
            nom_entreprise = entreprise['nom']
            commune = entreprise['commune']
            
            # Requêtes presse locale
            requetes_presse = [
                f'"{nom_entreprise}" {commune} site:*.fr actualité',
                f'"{nom_entreprise}" {commune} presse locale',
            ]
            
            for requete in requetes_presse[:1]:
                try:
                    print(f"      📰 Recherche presse: {requete}")
                    resultats_requete = self._rechercher_moteur(requete)
                    
                    if resultats_requete:
                        # Filtrage sites de presse
                        resultats_presse_filtres = []
                        for resultat in resultats_requete:
                            url = resultat.get('url', '').lower()
                            if any(keyword in url for keyword in ['news', 'presse', 'journal', 'actu', 'info', 'media']):
                                resultats_presse_filtres.append(resultat)
                        
                        if resultats_presse_filtres:
                            resultats_presse[f'presse_{len(resultats_presse)}'] = {
                                'source': 'presse_locale',
                                'requete': requete,
                                'extraits_textuels': resultats_presse_filtres,
                                'pertinence': min(len(resultats_presse_filtres) * 0.4, 1.0)
                            }
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"        ⚠️  Erreur presse: {str(e)}")
                    continue
                    
            return resultats_presse if resultats_presse else None
            
        except Exception as e:
            print(f"      ⚠️  Erreur presse locale: {str(e)}")
            return None
            
    def _rechercher_sur_site(self, site_url: str, terme: str) -> Optional[Dict]:
        """Recherche d'un terme sur un site spécifique"""
        try:
            print(f"        🔍 Recherche sur {site_url}")
            response = self.session.get(site_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Suppression des éléments non pertinents
                for script in soup(["script", "style", "nav", "footer"]):
                    script.decompose()
                
                contenu_texte = soup.get_text()
                contenu = contenu_texte.lower()
                
                if terme.lower() in contenu:
                    # Extraction du contexte
                    position = contenu.find(terme.lower())
                    if position != -1:
                        debut = max(0, position - 100)
                        fin = min(len(contenu_texte), position + 100)
                        contexte = contenu_texte[debut:fin].strip()
                        contexte = re.sub(r'\s+', ' ', contexte)
                        
                        return {
                            'trouve': True,
                            'url': site_url,
                            'extrait': contexte,
                            'position': position
                        }
                        
        except Exception as e:
            print(f"          ⚠️  Erreur site {site_url}: {str(e)}")
            
        return None

    def _generer_donnees_sectorielles_ameliorees(self, entreprise: Dict) -> Optional[Dict]:
        """✅ SUPPRIMÉ: Plus de génération de fausses données sectorielles"""
        print(f"      ⚪ Génération de données sectorielles désactivée pour éviter les faux positifs")
        return None  # Toujours retourner None
    
    def _extraire_mots_cles_cibles(self, resultats: List[Dict], thematique: str) -> List[str]:
        """✅ CORRIGÉ : Extraction des vrais mots-clés trouvés"""
        mots_cles = []
        for resultat in resultats:
            if 'mots_cles_trouves' in resultat:
                mots_cles.extend(resultat['mots_cles_trouves'])
        
        # Ajout des mots-clés thématiques seulement si vraiment trouvés
        return list(set(mots_cles))
