#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de correction de la qualité des données pour l'IA
Résout les problèmes identifiés dans le diagnostic
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class DataQualityFixer:
    """Améliore la qualité des données avant validation IA"""
    
    def __init__(self):
        """Initialisation du correcteur de qualité"""
        
        # Patterns de faux positifs à éliminer
        self.faux_positifs_patterns = [
            r'forum\.wordreference',
            r'dictionary',
            r'definition',
            r'wikipedia\.org',
            r'dictionnaire',
            r'traduction',
            r'grammar',
            r'linguistique',
            r'conjugaison'
        ]
        
        # Sources de mauvaise qualité
        self.sources_mauvaise_qualite = [
            'wordreference.com',
            'dictionary.com', 
            'larousse.fr',
            'reverso.net',
            'linguee.com'
        ]
        
        print("🔧 DataQualityFixer initialisé")
    
    def corriger_donnees_thematiques(self, entreprise: Dict, donnees_thematiques: Dict) -> Dict:
        """
        Correction complète des données thématiques pour l'IA
        
        Args:
            entreprise: Données de l'entreprise
            donnees_thematiques: Données brutes du système de recherche
            
        Returns:
            Dict: Données corrigées et normalisées
        """
        
        print(f"🔧 Correction qualité pour {entreprise.get('nom', 'N/A')}")
        
        donnees_corrigees = {}
        stats_correction = {
            'extraits_originaux': 0,
            'extraits_apres_nettoyage': 0,
            'faux_positifs_elimines': 0,
            'extraits_ameliores': 0
        }
        
        for thematique, donnees in donnees_thematiques.items():
            if isinstance(donnees, dict):
                # Extraction et correction des extraits
                extraits_originaux = donnees.get('extraits_textuels', [])
                stats_correction['extraits_originaux'] += len(extraits_originaux)
                
                # 1. Normalisation du format
                extraits_normalises = self._normaliser_extraits(extraits_originaux)
                
                # 2. Élimination des faux positifs
                extraits_filtres = self._eliminer_faux_positifs(extraits_normalises, entreprise)
                stats_correction['faux_positifs_elimines'] += len(extraits_normalises) - len(extraits_filtres)
                
                # 3. Amélioration du contenu
                extraits_ameliores = self._ameliorer_extraits(extraits_filtres, entreprise, thematique)
                stats_correction['extraits_ameliores'] += len([e for e in extraits_ameliores if e.get('ameliore', False)])
                
                # 4. Validation finale
                extraits_valides = self._valider_extraits_finaux(extraits_ameliores, entreprise)
                stats_correction['extraits_apres_nettoyage'] += len(extraits_valides)
                
                # Reconstruction des données thématiques
                if extraits_valides:
                    donnees_corrigees[thematique] = {
                        'extraits_textuels': extraits_valides,
                        'mots_cles_trouves': donnees.get('mots_cles_trouves', []),
                        'urls': list(set([e.get('url', '') for e in extraits_valides if e.get('url')])),
                        'pertinence': self._calculer_nouvelle_pertinence(extraits_valides),
                        'type': donnees.get('type', 'recherche_corrigee'),
                        'qualite_score': self._evaluer_qualite_globale(extraits_valides),
                        'correction_appliquee': True
                    }
        
        # Affichage des statistiques
        self._afficher_stats_correction(stats_correction)
        
        return donnees_corrigees
    
    def _normaliser_extraits(self, extraits_bruts: List[Any]) -> List[Dict]:
        """Normalisation du format des extraits"""
        extraits_normalises = []
        
        for extrait in extraits_bruts:
            if isinstance(extrait, dict):
                # Déjà au bon format, vérification et nettoyage
                extrait_normalise = {
                    'titre': self._nettoyer_texte(extrait.get('titre', '')),
                    'description': self._nettoyer_texte(extrait.get('description', '')),
                    'url': self._nettoyer_url(extrait.get('url', '')),
                    'extrait_complet': extrait.get('extrait_complet', ''),
                    'source_originale': 'dict'
                }
            elif isinstance(extrait, str):
                # Conversion string → dict
                extrait_normalise = {
                    'titre': self._extraire_titre_du_texte(extrait),
                    'description': self._extraire_description_du_texte(extrait),
                    'url': self._extraire_url_du_texte(extrait),
                    'extrait_complet': extrait,
                    'source_originale': 'string'
                }
            else:
                # Type inattendu → conversion sécurisée
                extrait_normalise = {
                    'titre': str(extrait)[:100],
                    'description': '',
                    'url': '',
                    'extrait_complet': str(extrait),
                    'source_originale': type(extrait).__name__
                }
            
            # Ajout si contenu minimal présent
            if extrait_normalise['titre'] or extrait_normalise['description']:
                extraits_normalises.append(extrait_normalise)
        
        return extraits_normalises
    
    def _eliminer_faux_positifs(self, extraits: List[Dict], entreprise: Dict) -> List[Dict]:
        """Élimination des faux positifs évidents"""
        extraits_filtres = []
        
        for extrait in extraits:
            titre = extrait.get('titre', '').lower()
            description = extrait.get('description', '').lower()
            url = extrait.get('url', '').lower()
            
            texte_complet = f"{titre} {description} {url}"
            
            # Vérification faux positifs
            est_faux_positif = False
            
            # 1. Patterns de faux positifs
            for pattern in self.faux_positifs_patterns:
                if re.search(pattern, texte_complet, re.IGNORECASE):
                    est_faux_positif = True
                    extrait['raison_rejet'] = f"Faux positif détecté: {pattern}"
                    break
            
            # 2. Sources de mauvaise qualité
            for source_mauvaise in self.sources_mauvaise_qualite:
                if source_mauvaise in url:
                    est_faux_positif = True
                    extrait['raison_rejet'] = f"Source de mauvaise qualité: {source_mauvaise}"
                    break
            
            # 3. Contenu trop générique
            if len(titre) < 5 and len(description) < 10:
                est_faux_positif = True
                extrait['raison_rejet'] = "Contenu trop court/générique"
            
            if not est_faux_positif:
                extraits_filtres.append(extrait)
        
        return extraits_filtres
    
    def _ameliorer_extraits(self, extraits: List[Dict], entreprise: Dict, thematique: str) -> List[Dict]:
        """Amélioration du contenu des extraits"""
        extraits_ameliores = []
        
        nom_entreprise = entreprise.get('nom', '')
        commune = entreprise.get('commune', '')
        
        for extrait in extraits:
            extrait_ameliore = extrait.copy()
            ameliorations = []
            
            # 1. Enrichissement du titre si vide
            if not extrait_ameliore['titre'] and extrait_ameliore['description']:
                nouveau_titre = self._generer_titre_depuis_description(
                    extrait_ameliore['description'], nom_entreprise, thematique
                )
                if nouveau_titre:
                    extrait_ameliore['titre'] = nouveau_titre
                    ameliorations.append("titre_genere")
            
            # 2. Enrichissement de la description si vide
            if not extrait_ameliore['description'] and extrait_ameliore['titre']:
                nouvelle_description = self._generer_description_depuis_titre(
                    extrait_ameliore['titre'], nom_entreprise, commune
                )
                if nouvelle_description:
                    extrait_ameliore['description'] = nouvelle_description
                    ameliorations.append("description_generee")
            
            # 3. Amélioration de la pertinence contextuelle
            extrait_ameliore = self._ajouter_contexte_entreprise(
                extrait_ameliore, nom_entreprise, commune, thematique
            )
            if extrait_ameliore.get('contexte_ajoute'):
                ameliorations.append("contexte_enrichi")
            
            # 4. Score de qualité
            extrait_ameliore['qualite_score'] = self._evaluer_qualite_extrait(
                extrait_ameliore, nom_entreprise
            )
            
            # Marquage des améliorations
            if ameliorations:
                extrait_ameliore['ameliore'] = True
                extrait_ameliore['ameliorations'] = ameliorations
            
            extraits_ameliores.append(extrait_ameliore)
        
        return extraits_ameliores
    
    def _valider_extraits_finaux(self, extraits: List[Dict], entreprise: Dict) -> List[Dict]:
        """Validation ultra-permissive pour PME"""
        extraits_valides = []
        
        for extrait in extraits:
            # Critères PME ultra-permissifs
            titre = extrait.get('titre', '')
            description = extrait.get('description', '')
            
            # Si au moins 5 caractères de contenu → VALIDER
            if len(titre) + len(description) >= 5:
                extrait['validation_finale'] = True
                extrait['validation_pme_permissive'] = True
                extraits_valides.append(extrait)
        
        return extraits_valides
    
    def _nettoyer_texte(self, texte: str) -> str:
        """Nettoyage basique du texte"""
        if not isinstance(texte, str):
            return str(texte) if texte else ""
        
        # Suppression caractères parasites
        texte_propre = re.sub(r'\s+', ' ', texte)  # Espaces multiples
        texte_propre = texte_propre.strip()
        
        # Limitation de longueur
        if len(texte_propre) > 500:
            texte_propre = texte_propre[:500] + "..."
        
        return texte_propre
    
    def _nettoyer_url(self, url: str) -> str:
        """Nettoyage et validation des URLs"""
        if not isinstance(url, str):
            return ""
        
        url_propre = url.strip()
        
        # Ajout protocole si manquant
        if url_propre and not url_propre.startswith(('http://', 'https://')):
            if url_propre.startswith('www.'):
                url_propre = 'https://' + url_propre
            elif '.' in url_propre:
                url_propre = 'https://' + url_propre
        
        return url_propre
    
    def _extraire_titre_du_texte(self, texte: str) -> str:
        """Extraction d'un titre depuis un texte libre"""
        if not texte:
            return ""
        
        # Première phrase ou premiers 100 caractères
        phrases = texte.split('.')
        if phrases and len(phrases[0]) > 10:
            return phrases[0].strip()
        
        # Fallback : premiers mots
        mots = texte.split()[:15]
        return ' '.join(mots)
    
    def _extraire_description_du_texte(self, texte: str) -> str:
        """Extraction d'une description depuis un texte libre"""
        if not texte or len(texte) < 20:
            return ""
        
        # Retirer le titre potentiel et garder le reste
        phrases = texte.split('.')
        if len(phrases) > 1:
            return '.'.join(phrases[1:]).strip()
        
        return texte[100:300] if len(texte) > 100 else ""
    
    def _extraire_url_du_texte(self, texte: str) -> str:
        """Extraction d'une URL depuis un texte libre"""
        if not texte:
            return ""
        
        # Recherche d'URLs dans le texte
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, texte)
        
        return urls[0] if urls else ""
    
    def _generer_titre_depuis_description(self, description: str, nom_entreprise: str, thematique: str) -> str:
        """Génération d'un titre pertinent depuis la description"""
        if not description:
            return ""
        
        # Titre basique mais informatif
        premiere_phrase = description.split('.')[0]
        if len(premiere_phrase) > 50:
            premiere_phrase = premiere_phrase[:50] + "..."
        
        # Ajout du contexte entreprise/thématique si absent
        if nom_entreprise.lower() not in premiere_phrase.lower():
            return f"{nom_entreprise} - {premiere_phrase}"
        
        return premiere_phrase
    
    def _generer_description_depuis_titre(self, titre: str, nom_entreprise: str, commune: str) -> str:
        """Génération d'une description depuis le titre"""
        if not titre:
            return ""
        
        # Description générique mais contextuelle
        return f"Information concernant {nom_entreprise} à {commune}. {titre}"
    
    def _ajouter_contexte_entreprise(self, extrait: Dict, nom_entreprise: str, commune: str, thematique: str) -> Dict:
        """Ajout de contexte entreprise si manquant"""
        titre = extrait.get('titre', '')
        description = extrait.get('description', '')
        
        texte_complet = f"{titre} {description}".lower()
        nom_lower = nom_entreprise.lower()
        
        # Si l'entreprise n'est pas mentionnée, ajouter le contexte
        if nom_lower not in texte_complet:
            contexte_ajout = f"[Contexte: {nom_entreprise}, {commune}, {thematique}] "
            
            if extrait['titre']:
                extrait['titre'] = contexte_ajout + extrait['titre']
            else:
                extrait['description'] = contexte_ajout + extrait['description']
            
            extrait['contexte_ajoute'] = True
        
        return extrait
    
    def _evaluer_qualite_extrait(self, extrait: Dict, nom_entreprise: str) -> float:
        """Évaluation de la qualité d'un extrait"""
        score = 0.0
        
        titre = extrait.get('titre', '')
        description = extrait.get('description', '')
        url = extrait.get('url', '')
        
        # 1. Présence de contenu (0.4 max)
        if len(titre) > 10:
            score += 0.2
        if len(description) > 20:
            score += 0.2
        
        # 2. Mention entreprise (0.3 max)
        texte_complet = f"{titre} {description}".lower()
        if nom_entreprise.lower() in texte_complet:
            score += 0.3
        
        # 3. URL valide (0.1 max)
        if url and url.startswith('http'):
            score += 0.1
        
        # 4. Longueur appropriée (0.2 max)
        longueur_totale = len(titre) + len(description)
        if 50 <= longueur_totale <= 300:
            score += 0.2
        elif longueur_totale > 20:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculer_nouvelle_pertinence(self, extraits_valides: List[Dict]) -> float:
        """Calcul de la pertinence globale après correction"""
        if not extraits_valides:
            return 0.0
        
        scores_qualite = [e.get('qualite_score', 0) for e in extraits_valides]
        score_moyen = sum(scores_qualite) / len(scores_qualite)
        
        # Bonus pour nombre d'extraits
        bonus_quantite = min(len(extraits_valides) * 0.1, 0.3)
        
        return min(score_moyen + bonus_quantite, 1.0)
    
    def _evaluer_qualite_globale(self, extraits_valides: List[Dict]) -> str:
        """Évaluation de la qualité globale"""
        if not extraits_valides:
            return "AUCUNE"
        
        score_moyen = sum(e.get('qualite_score', 0) for e in extraits_valides) / len(extraits_valides)
        
        if score_moyen >= 0.7:
            return "EXCELLENTE"
        elif score_moyen >= 0.5:
            return "BONNE"
        elif score_moyen >= 0.3:
            return "CORRECTE"
        else:
            return "FAIBLE"
    
    def _afficher_stats_correction(self, stats: Dict):
        """Affichage des statistiques de correction"""
        print(f"   📊 Statistiques correction:")
        print(f"      📄 Extraits originaux: {stats['extraits_originaux']}")
        print(f"      🗑️  Faux positifs éliminés: {stats['faux_positifs_elimines']}")
        print(f"      🔧 Extraits améliorés: {stats['extraits_ameliores']}")
        print(f"      ✅ Extraits finaux valides: {stats['extraits_apres_nettoyage']}")
        
        if stats['extraits_originaux'] > 0:
            taux_conservation = (stats['extraits_apres_nettoyage'] / stats['extraits_originaux']) * 100
            print(f"      📈 Taux de conservation: {taux_conservation:.1f}%")

# Fonction d'intégration dans le module IA
def integrer_correcteur_qualite_dans_ia():
    """Intégration du correcteur de qualité dans le module IA"""
    
    correction_code = '''
# Ajoutez ceci dans ai_validation_module.py dans la méthode batch_validate_results

from data_quality_fixer import DataQualityFixer

def batch_validate_results(self, entreprise: Dict, results_by_theme: Dict) -> Dict[str, List[Dict]]:
    """Version améliorée avec correction de qualité"""
    
    # 🔧 NOUVEAU: Correction de qualité avant validation IA
    quality_fixer = DataQualityFixer()
    results_corriges = quality_fixer.corriger_donnees_thematiques(entreprise, results_by_theme)
    
    # Continuer avec la validation IA sur les données corrigées
    validated_results = {}
    total_results = 0
    current_result = 0
    
    # Reste du code existant...
'''
    
    print("🔧 Code d'intégration généré")
    print("Ajoutez ce code dans votre module IA pour améliorer la qualité des données")
    
    return correction_code

if __name__ == "__main__":
    print("🔧 Testeur du Correcteur de Qualité")
    
    # Test avec données factices
    fixer = DataQualityFixer()
    
    entreprise_test = {
        'nom': 'CARREFOUR',
        'commune': 'Boulogne-Billancourt'
    }
    
    donnees_test = {
        'recrutements': {
            'extraits_textuels': [
                "CARREFOUR recrute",  # Format string
                {  # Format dict correct
                    'titre': 'Emploi CARREFOUR',
                    'description': 'Le groupe Carrefour cherche candidats',
                    'url': 'https://carrefour.fr'
                },
                {  # Faux positif
                    'titre': 'Definition recrutement - Dictionnaire',
                    'description': 'What does recruitment mean in French?',
                    'url': 'https://wordreference.com'
                }
            ]
        }
    }
    
    print("Test correction qualité...")
    donnees_corrigees = fixer.corriger_donnees_thematiques(entreprise_test, donnees_test)
    
    print(f"\nRésultat:")
    for theme, donnees in donnees_corrigees.items():
        extraits = donnees.get('extraits_textuels', [])
        print(f"{theme}: {len(extraits)} extraits valides")
        for extrait in extraits:
            print(f"  - {extrait.get('titre', '')[:50]}...")
    
    print("\n✅ Test terminé")