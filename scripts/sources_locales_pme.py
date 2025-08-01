#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de recherche dans les sources locales spécialisées PME
Simple et efficace - Va à l'essentiel
"""

from typing import Dict, List, Optional
import requests
import time
import random

class SourcesLocalesPME:
    """Recherche ciblée dans les sources locales pour PME"""
    
    def __init__(self):
        """Initialisation avec sources locales françaises"""
        
        # Sources locales par type (simplifiées)
        self.sources_locales = {
            'presse_locale': [
                'site:francebleu.fr',
                'site:actu.fr', 
                'site:france3-regions.francetvinfo.fr',
                'site:larepublique77.fr',  # Seine-et-Marne
                'site:leparisien.fr'
            ],
            
            'institutionnels': [
                'site:cci.fr',
                'site:cma.fr',  # Chambre des Métiers
                'site:bpifrance.fr',
                'site:economie.gouv.fr'
            ],
            
            'reseaux_pro': [
                'site:linkedin.com/company',
                'site:facebook.com',
                'site:cpme.fr'  # Confédération PME
            ]
        }
        
        # Départements ciblés (à adapter selon votre territoire)
        self.departements_cibles = ['77', '93', '94', '95']  # Seine-et-Marne et petite couronne
        
    def rechercher_pme_locale(self, entreprise: Dict, thematique: str) -> List[Dict]:
        """Recherche PME dans sources locales - SIMPLE ET EFFICACE"""
        
        nom = entreprise.get('nom', '').strip()
        commune = entreprise.get('commune', '').strip()
        
        if not nom or not commune:
            return []
        
        print(f"    🏘️ Recherche locale: {nom} à {commune}")
        
        resultats_locaux = []
        
        # 1. PRESSE LOCALE (priorité max pour PME)
        resultats_presse = self._rechercher_presse_locale(nom, commune, thematique)
        if resultats_presse:
            resultats_locaux.extend(resultats_presse)
            print(f"      📰 Presse locale: {len(resultats_presse)} résultats")
        
        # 2. SOURCES INSTITUTIONNELLES (si peu de résultats presse)
        if len(resultats_locaux) < 2:
            resultats_instit = self._rechercher_institutionnels(nom, commune, thematique)
            if resultats_instit:
                resultats_locaux.extend(resultats_instit)
                print(f"      🏛️ Institutionnels: {len(resultats_instit)} résultats")
        
        # 3. RÉSEAUX PROFESSIONNELS (bonus si entreprise connue)
        if self._entreprise_visible(nom):
            resultats_reseaux = self._rechercher_reseaux_pro(nom, commune)
            if resultats_reseaux:
                resultats_locaux.extend(resultats_reseaux[:2])  # Max 2
                print(f"      🤝 Réseaux pro: {len(resultats_reseaux)} résultats")
        
        # Déduplication simple
        resultats_uniques = self._dedupliquer_resultats(resultats_locaux)
        
        if resultats_uniques:
            print(f"    ✅ Sources locales: {len(resultats_uniques)} résultats uniques")
        
        return resultats_uniques[:5]  # Max 5 résultats par entreprise
    
    def _rechercher_presse_locale(self, nom: str, commune: str, thematique: str) -> List[Dict]:
        """Recherche dans la presse locale - ESSENTIEL pour PME"""
        
        # Requêtes presse locale optimisées
        requetes_presse = [
            f'site:francebleu.fr "{nom}" {commune}',
            f'site:actu.fr {nom} {commune}',
            f'{nom} {commune} actualité -site:wikipedia.org'
        ]
        
        # Ajout thématique si pertinente
        if thematique in ['recrutements', 'evenements', 'innovations']:
            requetes_presse.append(f'{nom} {commune} {thematique} site:france3-regions.francetvinfo.fr')
        
        resultats = []
        
        for requete in requetes_presse[:2]:  # Max 2 requêtes presse
            try:
                # Simulation de recherche (remplacez par votre moteur de recherche)
                resultats_requete = self._executer_recherche_locale(requete)
                if resultats_requete:
                    resultats.extend(resultats_requete)
                
                time.sleep(random.uniform(2, 4))  # Délai raisonnable
                
            except Exception as e:
                print(f"      ⚠️ Erreur presse locale: {e}")
                continue
        
        return resultats
    
    def _rechercher_institutionnels(self, nom: str, commune: str, thematique: str) -> List[Dict]:
        """Recherche sources institutionnelles"""
        
        requetes_instit = [
            f'site:cci.fr {nom} {commune}',
            f'site:bpifrance.fr {nom}'
        ]
        
        # Thématiques spécifiques institutionnelles
        if thematique == 'aides_subventions':
            requetes_instit.append(f'{nom} {commune} aide financement site:economie.gouv.fr')
        
        resultats = []
        
        for requete in requetes_instit[:2]:
            try:
                resultats_requete = self._executer_recherche_locale(requete)
                if resultats_requete:
                    resultats.extend(resultats_requete)
                
                time.sleep(random.uniform(3, 5))
                
            except Exception as e:
                print(f"      ⚠️ Erreur institutionnels: {e}")
                continue
        
        return resultats
    
    def _rechercher_reseaux_pro(self, nom: str, commune: str) -> List[Dict]:
        """Recherche réseaux professionnels"""
        
        requetes_reseaux = [
            f'site:linkedin.com/company {nom.replace(" ", "-")}',
            f'{nom} {commune} site:facebook.com'
        ]
        
        resultats = []
        
        for requete in requetes_reseaux:
            try:
                resultats_requete = self._executer_recherche_locale(requete)
                if resultats_requete:
                    resultats.extend(resultats_requete[:1])  # Max 1 par réseau
                
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"      ⚠️ Erreur réseaux pro: {e}")
                continue
        
        return resultats
    
    def _executer_recherche_locale(self, requete: str) -> List[Dict]:
        """Exécute une recherche locale - INTÉGRER avec votre moteur existant"""
        
        # PLACEHOLDER - Remplacez par votre vraie recherche
        # Par exemple : return votre_moteur_recherche.rechercher(requete)
        
        # Simulation réaliste pour le développement
        if random.random() > 0.7:  # 30% de chances de trouver quelque chose
            return [
                {
                    'titre': f'Actualité locale trouvée dans {requete.split("site:")[1].split()[0] if "site:" in requete else "source locale"}',
                    'description': f'Information pertinente trouvée via recherche locale ciblée.',
                    'url': f'https://exemple-local.fr/actualite-{random.randint(1000,9999)}',
                    'source_locale': True,
                    'type_source': self._detecter_type_source(requete)
                }
            ]
        
        return []
    
    def _detecter_type_source(self, requete: str) -> str:
        """Détecte le type de source selon la requête"""
        if 'francebleu.fr' in requete or 'actu.fr' in requete:
            return 'presse_locale'
        elif 'cci.fr' in requete or 'bpifrance.fr' in requete:
            return 'institutionnel'
        elif 'linkedin.com' in requete or 'facebook.com' in requete:
            return 'reseau_social'
        return 'web_local'
    
    def _entreprise_visible(self, nom: str) -> bool:
        """Détermine si une entreprise est assez visible pour être sur les réseaux"""
        
        # Critères simples de visibilité
        indicateurs_visibilite = [
            len(nom) > 10,  # Nom pas trop court
            not any(terme in nom.upper() for terme in ['MADAME', 'MONSIEUR', 'M.']),  # Pas personne physique
            any(terme in nom.upper() for terme in ['SARL', 'SAS', 'SA', 'ENTREPRISE', 'SOCIETE'])  # Société
        ]
        
        return sum(indicateurs_visibilite) >= 2
    
    def _dedupliquer_resultats(self, resultats: List[Dict]) -> List[Dict]:
        """Déduplication simple par titre"""
        
        vus = set()
        resultats_uniques = []
        
        for resultat in resultats:
            titre_normalise = resultat.get('titre', '').lower().strip()
            
            if titre_normalise and titre_normalise not in vus:
                vus.add(titre_normalise)
                resultats_uniques.append(resultat)
        
        return resultats_uniques


# INTÉGRATION DANS VOTRE SYSTÈME EXISTANT
def integrer_sources_locales_dans_recherche():
    """
    Comment intégrer ce module dans votre recherche_web.py existant
    """
    
    integration_code = '''
# Dans recherche_web.py, ajouter :

from sources_locales_pme import SourcesLocalesPME

class RechercheWeb:
    def __init__(self, periode_recherche):
        # Votre code existant...
        self.sources_locales = SourcesLocalesPME()  # ← AJOUT
    
    def rechercher_entreprise(self, entreprise: Dict, logger=None) -> Dict:
        # Votre code existant...
        
        # ✅ AJOUT après la recherche web classique :
        try:
            print(f"    🏘️ Recherche sources locales spécialisées...")
            
            for thematique in ['recrutements', 'evenements', 'innovations', 'vie_entreprise']:
                if thematique not in resultats['donnees_thematiques']:
                    
                    resultats_locaux = self.sources_locales.rechercher_pme_locale(entreprise, thematique)
                    
                    if resultats_locaux:
                        resultats['donnees_thematiques'][thematique] = {
                            'mots_cles_trouves': [thematique, 'local'],
                            'urls': [r['url'] for r in resultats_locaux],
                            'pertinence': len(resultats_locaux) * 0.4,
                            'extraits_textuels': resultats_locaux,
                            'type': 'sources_locales_specialisees'
                        }
                        print(f"      ✅ {thematique}: {len(resultats_locaux)} sources locales")
        
        except Exception as e:
            print(f"    ⚠️ Erreur sources locales: {e}")
        
        return resultats
'''
    
    return integration_code


if __name__ == "__main__":
    # Test simple
    sources = SourcesLocalesPME()
    
    entreprise_test = {
        'nom': 'Boulangerie Martin',
        'commune': 'Bussy-Saint-Georges'
    }
    
    resultats = sources.rechercher_pme_locale(entreprise_test, 'recrutements')
    print(f"Résultats test: {len(resultats)} trouvés")
    
    print("\n" + "="*50)
    print("📋 CODE D'INTÉGRATION:")
    print("="*50)
    print(integrer_sources_locales_dans_recherche())