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
from urllib.parse import urljoin, urlparse
import hashlib

class RechercheWeb:
    """Moteur de recherche web pour informations entreprises"""
    
    def __init__(self, periode_recherche: timedelta, cache_dir: str = "data/cache"):
        """Initialisation du moteur de recherche"""
        self.periode_recherche = periode_recherche
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
        
    def rechercher_entreprise(self, entreprise: Dict) -> Dict:
        """Recherche complète pour une entreprise"""
        print(f"  🔍 Recherche: {entreprise['nom']} ({entreprise['commune']})")
        
        resultats = {
            'entreprise': entreprise,
            'timestamp': datetime.now().isoformat(),
            'sources_analysees': [],
            'donnees_thematiques': {},
            'erreurs': []
        }
        
        try:
            # 1. Vérification du site web officiel
            if entreprise.get('site_web'):
                resultats['sources_analysees'].append('site_officiel')
                donnees_site = self._analyser_site_officiel(entreprise['site_web'])
                if donnees_site:
                    resultats['donnees_thematiques']['site_officiel'] = donnees_site
                    
            # 2. Recherche web générale
            resultats['sources_analysees'].append('web_general')
            donnees_web = self._recherche_web_generale(entreprise)
            if donnees_web:
                resultats['donnees_thematiques']['web_general'] = donnees_web
                
            # 3. Recherche presse locale
            resultats['sources_analysees'].append('presse_locale')
            donnees_presse = self._recherche_presse_locale(entreprise)
            if donnees_presse:
                resultats['donnees_thematiques']['presse_locale'] = donnees_presse
                
        except Exception as e:
            resultats['erreurs'].append(f"Erreur recherche: {str(e)}")
            
        return resultats
        
    def _analyser_site_officiel(self, url: str) -> Optional[Dict]:
        """Analyse du site web officiel avec extraction de contenu"""
        try:
            from bs4 import BeautifulSoup
            
            # Vérification cache
            cache_key = self._get_cache_key(url)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
                
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                # Parsing HTML pour extraire le texte proprement
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Suppression des scripts et styles
                for script in soup(["script", "style"]):
                    script.decompose()
                
                contenu_texte = soup.get_text()
                contenu = contenu_texte.lower()
                
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
                            'pertinence': len(occurrences) / len(mots_cles),
                            'extraits_contextuels': extraits_contexte,  # ← CONTEXTE TEXTUEL !
                            'resume_contenu': contenu_texte[:500] + '...' if len(contenu_texte) > 500 else contenu_texte
                        }
                        
                # Mise en cache
                self._save_to_cache(cache_key, resultats_thematiques)
                return resultats_thematiques
                
        except Exception as e:
            print(f"    ⚠️  Erreur site officiel: {str(e)}")
            return None
            
    def _recherche_web_generale(self, entreprise: Dict) -> Optional[Dict]:
        """Version temporaire avec contenu textuel simulé réaliste"""
        import random
        
        resultats = {}
        nom_entreprise = entreprise['nom']
        commune = entreprise['commune']
        secteur = entreprise.get('secteur_naf', '').lower()
        
        print(f"    🔍 Simulation recherche pour {nom_entreprise}")
        
        # Génération de contenu textuel réaliste selon le secteur
        templates_textuels = {
            'recrutements': [
                f"{nom_entreprise} recrute plusieurs profils en CDI et CDD sur {commune}",
                f"Offres d'emploi disponibles chez {nom_entreprise} - postes techniques et commerciaux",
                f"{nom_entreprise} lance une campagne de recrutement pour renforcer ses équipes"
            ],
            'evenements': [
                f"{nom_entreprise} organise une journée portes ouvertes le samedi à {commune}",
                f"Conférence technique organisée par {nom_entreprise} sur les innovations du secteur",
                f"{nom_entreprise} participe au salon professionnel de {commune}"
            ],
            'innovations': [
                f"{nom_entreprise} lance un nouveau produit innovant développé en R&D",
                f"Brevet déposé par {nom_entreprise} pour une technologie révolutionnaire",
                f"{nom_entreprise} investit dans la modernisation de ses outils de production"
            ],
            'vie_entreprise': [
                f"{nom_entreprise} s'implante sur un nouveau site à {commune}",
                f"Partenariat stratégique signé entre {nom_entreprise} et un leader du secteur",
                f"{nom_entreprise} annonce son développement commercial sur la région"
            ]
        }
        
        # Simulation basée sur le secteur
        thematiques_probables = []
        if 'commerce' in secteur or 'vente' in secteur:
            thematiques_probables = ['evenements', 'recrutements']
        elif 'industrie' in secteur or 'fabrication' in secteur:
            thematiques_probables = ['innovations', 'recrutements']
        elif 'service' in secteur:
            thematiques_probables = ['recrutements', 'vie_entreprise']
        else:
            thematiques_probables = ['vie_entreprise']
        
        # Génération de 1-2 thématiques avec contenu textuel
        for thematique in random.sample(thematiques_probables, min(2, len(thematiques_probables))):
            if random.random() > 0.3:  # 70% de chance
                textes = templates_textuels.get(thematique, [])
                contenu_textuel = random.choice(textes) if textes else f"Information {thematique} pour {nom_entreprise}"
                
                resultats[thematique] = {
                    'mots_cles_trouves': ['simulation', thematique],
                    'urls': [f"https://example.com/{nom_entreprise.lower().replace(' ', '-')}"],
                    'pertinence': random.uniform(0.4, 0.9),
                    'extraits_textuels': [{
                        'titre': f"{thematique.title()} - {nom_entreprise}",
                        'description': contenu_textuel,
                        'url': f"https://example.com/{nom_entreprise.lower().replace(' ', '-')}",
                        'extrait_complet': contenu_textuel
                    }],
                    'type': 'simulation_textuelle'
                }
        
        return resultats if resultats else None

    def _rechercher_google(self, requete: str) -> Optional[Dict]:
        """Recherche Google avec extraction de contenu textuel"""
        try:
            from bs4 import BeautifulSoup
            
            # Initialisation de la variable résultats ici ↓
            resultats_extraits = []
            
            # URL de recherche Google
            url = "https://www.google.com/search"
            params = {
                'q': requete,
                'num': 10,  # Plus de résultats
                'hl': 'fr'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Recherche des snippets Google
                for result in soup.find_all('div', class_='g')[:5]:  # Top 5 résultats
                    try:
                        # Titre
                        titre_elem = result.find('h3')
                        titre = titre_elem.get_text() if titre_elem else ""
                        
                        # Description/snippet
                        desc_elem = result.find('span', {'class': lambda x: x and 'aCOpRe' in x})
                        if not desc_elem:
                            desc_elem = result.find('div', {'class': lambda x: x and 'VwiC3b' in x})
                        description = desc_elem.get_text() if desc_elem else ""
                        
                        # URL
                        url_elem = result.find('a')
                        url_result = url_elem['href'] if url_elem and url_elem.get('href') else ""
                        
                        if titre and description:
                            resultats_extraits.append({
                                'titre': titre,
                                'description': description,
                                'url': url_result,
                                'extrait_complet': f"{titre} - {description}"
                            })
                            
                    except Exception:
                        continue
        
            # Vérification des résultats trouvés
            if resultats_extraits:
                return {
                    'urls': [r['url'] for r in resultats_extraits],
                    'score': min(len(resultats_extraits) * 0.2, 1.0),
                    'mentions': len(resultats_extraits),
                    'extraits_textuels': resultats_extraits  # ← INFORMATION TEXTUELLE !
                }

            return None

        except Exception as e:
            print(f"      ⚠️  Erreur Google: {str(e)}")
            return None
            
    def _recherche_presse_locale(self, entreprise: Dict) -> Optional[Dict]:
        """Recherche dans la presse locale"""
        try:
            # URLs de presse locale à configurer selon région
            sites_presse_locale = [
                f"https://www.{entreprise['commune'].lower()}.fr",
                # Ajouter sites spécifiques à votre région
            ]
            
            resultats_presse = {}
            for site in sites_presse_locale:
                try:
                    # Recherche mention entreprise
                    resultats_site = self._rechercher_sur_site(site, entreprise['nom'])
                    if resultats_site:
                        resultats_presse[site] = resultats_site
                        
                except Exception:
                    continue
                    
            return resultats_presse if resultats_presse else None
            
        except Exception as e:
            print(f"    ⚠️  Erreur presse locale: {str(e)}")
            return None
            
    def _simuler_resultats_web(self, entreprise: Dict, requete: str) -> Dict:
        """Simulation de résultats web (à remplacer par vraie API)"""
        # Simulation basée sur les caractéristiques de l'entreprise
        resultats = {}
        
        # Simulation probabiliste selon le secteur
        secteur = entreprise.get('secteur_naf', '').lower()
        
        if 'commerce' in secteur or 'vente' in secteur:
            resultats['evenements'] = {
                'type': 'simulation',
                'probabilite': 0.7,
                'indicateurs': ['secteur_commercial']
            }
            
        if 'industrie' in secteur or 'fabrication' in secteur:
            resultats['innovations'] = {
                'type': 'simulation',
                'probabilite': 0.6,
                'indicateurs': ['secteur_industriel']
            }
            
        if 'service' in secteur:
            resultats['recrutements'] = {
                'type': 'simulation',
                'probabilite': 0.8,
                'indicateurs': ['secteur_services']
            }
            
        return resultats
        
    def _rechercher_sur_site(self, site_url: str, terme: str) -> Optional[Dict]:
        """Recherche d'un terme sur un site spécifique"""
        try:
            response = self.session.get(site_url, timeout=10)
            if response.status_code == 200:
                contenu = response.text.lower()
                if terme.lower() in contenu:
                    return {
                        'trouve': True,
                        'url': site_url,
                        'extrait': contenu[max(0, contenu.find(terme.lower())-50):
                                         contenu.find(terme.lower())+50]
                    }
                    
        except Exception:
            pass
            
        return None
        
    def _get_cache_key(self, url: str) -> str:
        """Génération d'une clé de cache"""
        return hashlib.md5(url.encode()).hexdigest()
        
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Récupération depuis le cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Vérification âge du cache (24h)
                timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                if datetime.now() - timestamp < timedelta(hours=24):
                    return data.get('resultats')
                    
            except Exception:
                pass
                
        return None
        
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Sauvegarde en cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'resultats': data
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
            
    def nettoyer_cache(self, max_age_hours: int = 24):
        """Nettoyage du cache ancien"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    # Suppression des fichiers trop anciens
                    if os.path.getmtime(filepath) < time.time() - (max_age_hours * 3600):
                        os.remove(filepath)
                        
        except Exception:
            pass