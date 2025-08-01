#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mots-clés spécialisés pour PME - Version améliorée et réaliste
Simple, efficace, testé sur le terrain
"""

from typing import Dict, List


class MotsClesPME:
    """Mots-clés optimisés pour la réalité des PME françaises"""
    
    def __init__(self):
        """Mots-clés testés et validés pour les PME"""
        
        # ✅ MOTS-CLÉS PME RÉALISTES (basés sur le vrai langage PME)
        self.mots_cles_pme = {
            
            # 🎯 RECRUTEMENTS PME (langage réel)
            'recrutements': {
                'essentiels': [
                    'cherche', 'recherche', 'recrute', 'embauche',
                    'poste à pourvoir', 'nous recherchons', 'rejoindre notre équipe'
                ],
                'pme_specifiques': [
                    'cherche apprenti', 'forme un apprenti', 'accueille stagiaire',
                    'recherche vendeur', 'recherche vendeuse', 'cherche employé',
                    'besoin urgentement', 'poste disponible immédiatement'
                ],
                'contexte_local': [
                    'emploi local', 'travail proche', 'temps partiel accepté',
                    'débutant accepté', 'avec expérience souhaitée'
                ]
            },
            
            # 🏪 ÉVÉNEMENTS PME (réalité terrain)
            'evenements': {
                'essentiels': [
                    'ouverture', 'inauguration', 'nouveau magasin',
                    'porte ouverte', 'portes ouvertes', 'venez découvrir'
                ],
                'pme_specifiques': [
                    'nouveaux locaux', 'déménage', 'agrandit',
                    'fête ses', 'anniversaire', 'années d\'existence',
                    'soldes', 'promotion', 'opération spéciale'
                ],
                'saisonniers': [
                    'ouvert dimanche', 'horaires étendus', 'nocturne',
                    'marché de noël', 'braderie', 'vide-grenier'
                ]
            },
            
            # 💡 INNOVATIONS PME (adaptées à la réalité)
            'innovations': {
                'essentiels': [
                    'nouveau service', 'nouvelle prestation', 'nouveauté',
                    'améliore', 'modernise', 'rénove'
                ],
                'pme_specifiques': [
                    'installe', 'équipe de', 'investit dans',
                    'nouvelle machine', 'nouvel outil', 'se digitalise',
                    'livraison maintenant', 'commande en ligne', 'click and collect'
                ],
                'tendances_actuelles': [
                    'écologique', 'bio', 'local', 'circuit court',
                    'fait maison', 'artisanal', 'personnalisé'
                ]
            },
            
            # 🏢 VIE ENTREPRISE PME (développement réaliste)
            'vie_entreprise': {
                'essentiels': [
                    'développe', 'grandit', 'expansion', 'croissance',
                    'partenariat', 'collaboration', 'association'
                ],
                'pme_specifiques': [
                    'reprend l\'entreprise', 'cède son entreprise',
                    'transmission', 'rachat', 'fusion',
                    'ouvre une succursale', 'second magasin'
                ],
                'geographiques': [
                    'implantation', 'installation', 's\'installe à',
                    'rayonne sur', 'dessert maintenant', 'zone de chalandise'
                ]
            }
        }
        
        # 🏭 MOTS-CLÉS PAR SECTEUR PME (les plus courants)
        self.secteurs_pme = {
            'commerce': [
                'magasin', 'boutique', 'commerce', 'vente',
                'clientèle', 'service client', 'conseil'
            ],
            'restauration': [
                'restaurant', 'brasserie', 'café', 'bar',
                'plat du jour', 'menu', 'réservation', 'terrasse'
            ],
            'artisanat': [
                'artisan', 'fait main', 'sur mesure',
                'réparation', 'création', 'atelier'
            ],
            'services': [
                'à domicile', 'sur site', 'intervention',
                'devis gratuit', 'urgence', '7j/7'
            ],
            'sante': [
                'cabinet', 'consultation', 'soins',
                'rendez-vous', 'urgence', 'garde'
            ]
        }
        
        # ❌ MOTS À ÉVITER (faux positifs courants)
        self.mots_a_eviter = [
            'définition', 'dictionnaire', 'traduction',
            'cours de', 'formation à', 'apprendre',
            'wikipédia', 'forum', 'question'
        ]
    
    def obtenir_mots_cles_adaptes(self, thematique: str, secteur: str = '') -> List[str]:
        """Obtient les mots-clés adaptés à une thématique et un secteur"""
        
        mots_finaux = []
        
        # 1. Mots-clés de base de la thématique
        if thematique in self.mots_cles_pme:
            theme_data = self.mots_cles_pme[thematique]
            
            # Essentiels (toujours inclus)
            mots_finaux.extend(theme_data.get('essentiels', []))
            
            # PME spécifiques (priorité)
            mots_finaux.extend(theme_data.get('pme_specifiques', []))
            
            # Contextuels (bonus)
            mots_finaux.extend(theme_data.get('contexte_local', [])[:3])
        
        # 2. Adaptation par secteur
        secteur_simplifie = self._detecter_secteur_principal(secteur)
        if secteur_simplifie in self.secteurs_pme:
            mots_secteur = self.secteurs_pme[secteur_simplifie][:4]  # Max 4
            mots_finaux.extend(mots_secteur)
        
        # 3. Nettoyage et limitation
        mots_uniques = list(set(mots_finaux))  # Déduplication
        
        return mots_uniques[:15]  # Max 15 mots-clés par recherche
    
    def _detecter_secteur_principal(self, secteur_naf: str) -> str:
        """Détecte le secteur principal depuis le libellé NAF"""
        
        if not secteur_naf:
            return ''
        
        secteur_lower = secteur_naf.lower()
        
        # Détection par mots-clés dans le secteur NAF
        if any(mot in secteur_lower for mot in ['commerce', 'vente', 'magasin']):
            return 'commerce'
        elif any(mot in secteur_lower for mot in ['restaurant', 'café', 'bar', 'alimentation']):
            return 'restauration'
        elif any(mot in secteur_lower for mot in ['artisan', 'fabrication', 'réparation']):
            return 'artisanat'
        elif any(mot in secteur_lower for mot in ['service', 'conseil', 'maintenance']):
            return 'services'
        elif any(mot in secteur_lower for mot in ['santé', 'médical', 'soin']):
            return 'sante'
        
        return 'general'
    
    def construire_requete_optimisee(self, nom_entreprise: str, commune: str, 
                                   thematique: str, secteur: str = '') -> str:
        """Construit une requête optimisée avec les bons mots-clés"""
        
        # Mots-clés adaptés
        mots_cles = self.obtenir_mots_cles_adaptes(thematique, secteur)
        
        # Sélection des 2-3 meilleurs mots-clés
        mots_prioritaires = mots_cles[:3]
        
        # Construction de la requête intelligente
        if len(nom_entreprise) < 30:  # Nom pas trop long
            requete = f'"{nom_entreprise}" {commune} {" ".join(mots_prioritaires[:2])}'
        else:
            # Nom long : utiliser mots-clés principaux
            mots_entreprise = nom_entreprise.split()[:3]
            requete = f'{" ".join(mots_entreprise)} {commune} {mots_prioritaires[0]}'
        
        return requete
    
    def valider_pertinence_resultat(self, resultat: Dict, thematique: str) -> float:
        """Valide la pertinence d'un résultat selon les mots-clés PME"""
        
        titre = resultat.get('titre', '').lower()
        description = resultat.get('description', '').lower()
        texte_complet = f"{titre} {description}"
        
        # 1. Vérification mots à éviter (exclusion)
        for mot_eviter in self.mots_a_eviter:
            if mot_eviter in texte_complet:
                return 0.0  # Exclusion immédiate
        
        # 2. Comptage mots-clés pertinents
        mots_cles_theme = self.obtenir_mots_cles_adaptes(thematique)
        
        mots_trouves = 0
        mots_essentiels_trouves = 0
        
        for mot_cle in mots_cles_theme:
            if mot_cle.lower() in texte_complet:
                mots_trouves += 1
                
                # Bonus pour mots essentiels
                if thematique in self.mots_cles_pme:
                    essentiels = self.mots_cles_pme[thematique].get('essentiels', [])
                    if mot_cle in essentiels:
                        mots_essentiels_trouves += 1
        
        # 3. Calcul du score
        if mots_trouves == 0:
            return 0.0
        
        score_base = min(mots_trouves * 0.2, 0.8)
        bonus_essentiels = mots_essentiels_trouves * 0.1
        
        return min(score_base + bonus_essentiels, 1.0)


# INTÉGRATION DANS VOTRE SYSTÈME
def integrer_mots_cles_pme():
    """Comment intégrer les mots-clés PME dans votre système"""
    
    code_integration = '''
# Dans votre recherche_web.py ou analyseur_thematiques.py :

from mots_cles_pme import MotsClesPME

class RechercheWeb:
    def __init__(self, periode_recherche):
        # Votre code existant...
        self.mots_cles_pme = MotsClesPME()  # ← AJOUT
    
    def construire_requetes_pme_territoriales(self, entreprise: Dict, thematique: str) -> List[str]:
        """Version améliorée avec mots-clés PME optimisés"""
        
        nom = entreprise.get('nom', '')
        commune = entreprise.get('commune', '')
        secteur = entreprise.get('secteur_naf', '')
        
        # ✅ NOUVELLE requête optimisée PME
        requete_optimisee = self.mots_cles_pme.construire_requete_optimisee(
            nom, commune, thematique, secteur
        )
        
        # Vos autres requêtes existantes...
        requetes = [requete_optimisee]
        
        return requetes

class AnalyseurThematiques:
    def __init__(self, thematiques_config):
        # Votre code existant...
        self.mots_cles_pme = MotsClesPME()  # ← AJOUT
    
    def _valider_pertinence_resultat(self, resultat: Dict, thematique: str) -> float:
        """Validation améliorée avec mots-clés PME"""
        
        # ✅ NOUVELLE validation PME
        score_pme = self.mots_cles_pme.valider_pertinence_resultat(resultat, thematique)
        
        # Combiner avec votre validation existante si vous en avez une
        # score_final = (score_pme + votre_score_existant) / 2
        
        return score_pme
'''
    
    return code_integration


if __name__ == "__main__":
    # Test des mots-clés PME
    mots_cles = MotsClesPME()
    
    print("🧪 TEST MOTS-CLÉS PME")
    print("="*40)
    
    # Test 1: Mots-clés par thématique
    for thematique in ['recrutements', 'evenements', 'innovations']:
        mots = mots_cles.obtenir_mots_cles_adaptes(thematique, 'commerce de détail')
        print(f"\n{thematique.upper()}: {len(mots)} mots-clés")
        print(f"   {', '.join(mots[:8])}...")
    
    # Test 2: Requête optimisée
    print(f"\n🎯 REQUÊTE OPTIMISÉE:")
    requete = mots_cles.construire_requete_optimisee(
        "Boulangerie Martin", "Bussy-Saint-Georges", "recrutements", "boulangerie"
    )
    print(f"   {requete}")
    
    # Test 3: Validation
    print(f"\n✅ TEST VALIDATION:")
    resultat_test = {
        'titre': 'Boulangerie Martin cherche apprenti à Bussy-Saint-Georges',
        'description': 'La boulangerie recherche un apprenti motivé pour rejoindre notre équipe'
    }
    score = mots_cles.valider_pertinence_resultat(resultat_test, 'recrutements')
    print(f"   Score de pertinence: {score:.2f}")
    
    print(f"\n📋 CODE D'INTÉGRATION:")
    print("="*40)
    print(integrer_mots_cles_pme())