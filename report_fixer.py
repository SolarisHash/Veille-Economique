#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correctif pour éliminer les doublons et valider les URLs
À intégrer dans votre générateur de rapports
"""

import requests
from urllib.parse import urlparse
from typing import List, Dict, Set
import time
import re
from collections import defaultdict

class ReportFixer:
    """Correcteur de rapports - Anti-doublons et validation URLs"""
    
    def __init__(self):
        self.urls_valides = {}  # Cache des URLs validées
        self.urls_invalides = set()  # URLs à éviter
        
    def deduplicate_enterprises(self, entreprises_enrichies: List[Dict]) -> List[Dict]:
        """Élimine les doublons d'entreprises"""
        print("🔄 Déduplication des entreprises...")
        
        entreprises_uniques = {}  # Clé: SIRET, Valeur: entreprise
        entreprises_deduplicates = []
        
        for entreprise in entreprises_enrichies:
            siret = entreprise.get('siret', '')
            nom = entreprise.get('nom', '')
            
            # Clé unique basée sur SIRET + nom
            cle_unique = f"{siret}_{nom}".strip('_')
            
            if cle_unique in entreprises_uniques:
                # Fusion des données si doublon détecté
                print(f"   🔄 Doublon détecté: {nom[:50]}...")
                entreprise_existante = entreprises_uniques[cle_unique]
                entreprise_fusionnee = self._fusionner_entreprises(entreprise_existante, entreprise)
                entreprises_uniques[cle_unique] = entreprise_fusionnee
            else:
                entreprises_uniques[cle_unique] = entreprise
                print(f"   ✅ Unique: {nom[:50]}...")
        
        entreprises_deduplicates = list(entreprises_uniques.values())
        
        print(f"📊 Déduplication terminée:")
        print(f"   📥 Entreprises avant: {len(entreprises_enrichies)}")
        print(f"   📤 Entreprises après: {len(entreprises_deduplicates)}")
        print(f"   🗑️ Doublons éliminés: {len(entreprises_enrichies) - len(entreprises_deduplicates)}")
        
        return entreprises_deduplicates
    
    def _fusionner_entreprises(self, entreprise1: Dict, entreprise2: Dict) -> Dict:
        """Fusionne deux entreprises dupliquées en conservant le meilleur"""
        print(f"     🔗 Fusion en cours...")
        
        # Prendre l'entreprise avec le meilleur score comme base
        score1 = entreprise1.get('score_global', 0)
        score2 = entreprise2.get('score_global', 0)
        
        if score2 > score1:
            entreprise_base = entreprise2.copy()
            entreprise_fusion = entreprise1
        else:
            entreprise_base = entreprise1.copy()
            entreprise_fusion = entreprise2
        
        # Fusionner les thématiques
        analyse1 = entreprise1.get('analyse_thematique', {})
        analyse2 = entreprise2.get('analyse_thematique', {})
        
        # Merger les analyses thématiques
        for thematique, data in analyse2.items():
            if data.get('trouve', False):
                if thematique not in analyse1 or not analyse1[thematique].get('trouve', False):
                    # Ajouter la thématique manquante
                    analyse1[thematique] = data
                else:
                    # Fusionner les détails
                    details1 = analyse1[thematique].get('details', [])
                    details2 = data.get('details', [])
                    analyse1[thematique]['details'] = details1 + details2
                    
                    # Prendre le meilleur score
                    score_max = max(
                        analyse1[thematique].get('score_pertinence', 0),
                        data.get('score_pertinence', 0)
                    )
                    analyse1[thematique]['score_pertinence'] = score_max
        
        entreprise_base['analyse_thematique'] = analyse1
        
        # Recalculer le score global
        entreprise_base['score_global'] = self._recalculer_score_global(analyse1)
        
        # Fusionner les thématiques principales
        themes1 = set(entreprise1.get('thematiques_principales', []))
        themes2 = set(entreprise2.get('thematiques_principales', []))
        entreprise_base['thematiques_principales'] = list(themes1.union(themes2))
        
        return entreprise_base
    
    def _recalculer_score_global(self, analyse_thematique: Dict) -> float:
        """Recalcule le score global après fusion"""
        scores_valides = [
            data['score_pertinence']
            for data in analyse_thematique.values()
            if data.get('trouve', False) and data.get('score_pertinence', 0) > 0.3
        ]
        
        if not scores_valides:
            return 0.0
        
        score_moyen = sum(scores_valides) / len(scores_valides)
        bonus_diversite = min(len(scores_valides) * 0.02, 0.1)
        
        return min(score_moyen + bonus_diversite, 0.8)
    
    def validate_and_fix_urls(self, entreprises: List[Dict]) -> List[Dict]:
        """Valide et corrige les URLs dans les rapports"""
        print("🔗 Validation et correction des URLs...")
        
        total_urls = 0
        urls_corrigees = 0
        urls_supprimees = 0
        
        for entreprise in entreprises:
            nom_entreprise = entreprise.get('nom', 'N/A')
            print(f"   🔍 URLs de: {nom_entreprise[:40]}...")
            
            analyse = entreprise.get('analyse_thematique', {})
            
            for thematique, data in analyse.items():
                if not data.get('trouve', False):
                    continue
                
                details = data.get('details', [])
                details_corriges = []
                
                for detail in details:
                    total_urls += 1
                    informations = detail.get('informations', {})
                    
                    # Traitement des extraits textuels avec URLs
                    extraits_textuels = informations.get('extraits_textuels', [])
                    extraits_corriges = []
                    
                    for extrait in extraits_textuels:
                        if isinstance(extrait, dict):
                            url = extrait.get('url', '')
                            
                            if url:
                                url_status = self._validate_url(url)
                                
                                if url_status == 'valid':
                                    extraits_corriges.append(extrait)
                                elif url_status == 'invalid':
                                    # Supprimer l'URL invalide mais garder le contenu
                                    extrait_sans_url = extrait.copy()
                                    extrait_sans_url['url'] = ''
                                    extrait_sans_url['url_status'] = 'removed_invalid'
                                    extraits_corriges.append(extrait_sans_url)
                                    urls_supprimees += 1
                                elif url_status == 'simulation':
                                    # Remplacer par une recherche Google
                                    extrait_corrige = self._fix_simulation_url(extrait, nom_entreprise, thematique)
                                    extraits_corriges.append(extrait_corrige)
                                    urls_corrigees += 1
                            else:
                                extraits_corriges.append(extrait)
                    
                    # Mettre à jour les extraits corrigés
                    informations['extraits_textuels'] = extraits_corriges
                    details_corriges.append(detail)
                
                data['details'] = details_corriges
        
        print(f"📊 Validation URLs terminée:")
        print(f"   📥 URLs analysées: {total_urls}")
        print(f"   🔧 URLs corrigées: {urls_corrigees}")
        print(f"   🗑️ URLs supprimées: {urls_supprimees}")
        
        return entreprises
    
    def _validate_url(self, url: str) -> str:
        """Valide une URL"""
        if not url or not url.startswith('http'):
            return 'invalid'
        
        # URLs de simulation détectées
        simulation_indicators = [
            '-sante.fr/entreprises-locales',
            '-eco.fr/activites',
            '-news.fr/economie',
            '-formation.fr/services',
            'exemple-local.fr',
            'salon-lagny-sur-marne.fr'
        ]
        
        if any(indicator in url for indicator in simulation_indicators):
            return 'simulation'
        
        # Cache pour éviter de tester la même URL plusieurs fois
        if url in self.urls_valides:
            return self.urls_valides[url]
        
        if url in self.urls_invalides:
            return 'invalid'
        
        try:
            # Test rapide avec HEAD request
            response = requests.head(url, timeout=5, allow_redirects=True)
            
            if response.status_code < 400:
                self.urls_valides[url] = 'valid'
                return 'valid'
            else:
                self.urls_invalides.add(url)
                return 'invalid'
                
        except:
            self.urls_invalides.add(url)
            return 'invalid'
    
    def _fix_simulation_url(self, extrait: Dict, nom_entreprise: str, thematique: str) -> Dict:
        """Corrige une URL de simulation"""
        titre = extrait.get('titre', '')
        
        # Générer une recherche Google appropriée
        search_query = f"{nom_entreprise} {thematique}".replace(' ', '+')
        google_url = f"https://www.google.fr/search?q={search_query}"
        
        extrait_corrige = extrait.copy()
        extrait_corrige.update({
            'url': google_url,
            'url_status': 'corrected_to_search',
            'original_url': extrait.get('url', ''),
            'correction_note': 'URL simulée remplacée par recherche Google'
        })
        
        return extrait_corrige

# INTÉGRATION DANS VOTRE GÉNÉRATEUR DE RAPPORTS
def integrate_report_fixer():
    """Code d'intégration dans generateur_rapports.py"""
    
    integration_code = '''
# Dans votre generateur_rapports.py, méthode generer_tous_rapports():

from report_fixer import ReportFixer  # Ajoutez cet import

class GenerateurRapports:
    def generer_tous_rapports(self, entreprises_enrichies: List[Dict]) -> Dict[str, str]:
        """Version avec correction automatique"""
        print("📊 Génération de tous les rapports avec corrections")
        
        # ✅ NOUVEAU: Correction automatique avant génération
        fixer = ReportFixer()
        
        # 1. Élimination des doublons
        entreprises_uniques = fixer.deduplicate_enterprises(entreprises_enrichies)
        
        # 2. Validation et correction des URLs
        entreprises_corrigees = fixer.validate_and_fix_urls(entreprises_uniques)
        
        print(f"✅ Corrections appliquées:")
        print(f"   🗑️ Doublons éliminés: {len(entreprises_enrichies) - len(entreprises_uniques)}")
        print(f"   🔗 URLs corrigées automatiquement")
        
        # Continuer avec la génération normale des rapports
        rapports = {}
        
        # Vos rapports existants avec les données corrigées
        try:
            rapports['excel'] = self.generer_rapport_excel(entreprises_corrigees)
        except Exception as e:
            rapports['excel'] = f"ERREUR: {str(e)}"
        
        try:
            rapports['html'] = self.generer_rapport_html(entreprises_corrigees)
        except Exception as e:
            rapports['html'] = f"ERREUR: {str(e)}"
        
        # Autres rapports...
        
        return rapports
'''
    
    return integration_code

def _strip_html(s): return (s or '').strip()

def _fix_extraits_dupliques(html: str) -> str:
    """Supprime blocs d'extraits strictement identiques répétés à la suite."""
    # Heuristique : si trois <div ...> consécutifs ont même titre+desc+url -> n’en garder qu’un
    pattern = re.compile(
        r'(<div[^>]*>\s*<div[^>]*>\s*🌐[^<]*</div>\s*<div[^>]*>[^<]*</div>\s*(?:<div[^>]*>.*?</div>\s*)?</div>)(\s*\1)+',
        re.DOTALL | re.IGNORECASE
    )
    return re.sub(pattern, r'\1', html)

def _fix_noms_dupliques_commune(html: str) -> str:
    """Dans la carte 'Résumé par Commune', supprime les répétitions immédiates 'ARGEDIS, ARGEDIS'."""
    # Simpliste mais efficace : remplacer ', NOM, NOM' par ', NOM'
    def dedup_list(match):
        bloc = match.group(1)
        noms = [n.strip() for n in bloc.split(',') if n.strip()]
        uniques = []
        for n in noms:
            if n not in uniques:
                uniques.append(n)
        return ', '.join(uniques)

    return re.sub(
        r'(<div style="font-size: 0\.9em; color: #2c3e50; line-height: 1\.4;">\s*)([^<]+)(\s*</div>)',
        lambda m: m.group(1) + dedup_list(m.group(2)) + m.group(3),
        html, flags=re.DOTALL
    )

def post_process_html(html: str) -> str:
    html = _fix_extraits_dupliques(html)
    html = _fix_noms_dupliques_commune(html)
    return html

def post_process_html(html: str) -> str:
    """
    Petit lissage HTML de fin de chaîne :
    - Supprime les doublons immédiats du type "ARGEDIS, ARGEDIS"
    - Déduplique des suites "X, X, X"
    - Normalise espaces et virgules
    - Évite les répétitions consécutives de balises simples

    Le traitement reste volontairement conservateur (scope limité aux listes/phrases).
    """
    if not html:
        return html

    # 1) Nettoyage basique des espaces/virgules
    html = re.sub(r'\s+,', ', ', html)          # espace avant virgule -> après
    html = re.sub(r',\s+', ', ', html)          # normalise ",    " -> ", "
    html = re.sub(r'\s{2,}', ' ', html)         # espaces multiples -> simple espace

    # 2) Déduplication de mots/expressions consécutifs séparés par virgule
    #    Exemple: "ARGEDIS, ARGEDIS" -> "ARGEDIS"
    #    On reste prudent: on limite la longueur de l'expression et on évite de traverser tags/balises HTML.
    def dedupe_csv(match: re.Match) -> str:
        # prend la séquence capturée et supprime doublons consécutifs
        items = [x.strip() for x in match.group(0).split(',')]
        deduped = []
        prev = None
        for it in items:
            if it != prev:
                deduped.append(it)
            prev = it
        return ', '.join(deduped)

    # cible les segments CSV "Mot[, Mot]..." sans chevrons (évite HTML tags)
    # On traite par blocs entre balises pour rester conservateur.
    def dedupe_in_text_segments(html_text: str) -> str:
        # Sur chaque bloc de texte (hors balises), on retire "X, X" immédiats
        # Passes multiples pour capturer des triples "X, X, X"
        for _ in range(2):
            html_text = re.sub(
                r'(?<![<>])\b([A-Z0-9][A-Z0-9\'&\-. ]{1,80}?)\b,\s+\1\b(?![^<]*>)',
                r'\1',
                html_text
            )
        return html_text

    html = dedupe_in_text_segments(html)

    # 3) Déduplication douce dans les listes "bullet-like" séparées par " | "
    #    Exemple: "A | A | B" -> "A | B"
    def dedupe_pipe_segments(text: str) -> str:
        parts = text.split(' | ')
        result = []
        seen_prev = None
        for p in parts:
            if p != seen_prev:
                result.append(p)
            seen_prev = p
        return ' | '.join(result)

    html = re.sub(
        r'((?:[^<>]|<(?!/?(?:script|style)[^>]*>))+)',
        lambda m: dedupe_pipe_segments(m.group(1)),
        html,
        flags=re.IGNORECASE
    )

    # 4) Évite la répétition immédiate de mêmes balises simples (ex: <div>..</div><div>..</div> identiques collées)
    #    Ici on ne supprime pas, on insère une fine espace pour éviter "collage visuel" ; c’est safe.
    html = re.sub(r'(</(div|p)>\s*)(<(div|p)[ >])', r'\1\n\3', html, flags=re.IGNORECASE)

    # 5) Finitions ponctuation/espaces
    html = re.sub(r'\s+\.', '.', html)
    html = re.sub(r'\s+,', ', ', html)
    html = re.sub(r',\s+,', ', ', html)

    return html

if __name__ == "__main__":
    print("🧪 Test du correcteur de rapports")
    
    # Test déduplication
    fixer = ReportFixer()
    
    # Entreprises test avec doublons
    entreprises_test = [
        {
            'siret': '12345',
            'nom': 'ENTREPRISE TEST',
            'score_global': 0.5,
            'thematiques_principales': ['recrutements']
        },
        {
            'siret': '12345',  # Même SIRET = doublon
            'nom': 'ENTREPRISE TEST',
            'score_global': 0.3,
            'thematiques_principales': ['innovations']
        },
        {
            'siret': '67890',
            'nom': 'AUTRE ENTREPRISE',
            'score_global': 0.7,
            'thematiques_principales': ['evenements']
        }
    ]
    
    entreprises_uniques = fixer.deduplicate_enterprises(entreprises_test)
    
    print(f"\n✅ Test déduplication:")
    print(f"   Avant: {len(entreprises_test)} entreprises")
    print(f"   Après: {len(entreprises_uniques)} entreprises")
    
    for ent in entreprises_uniques:
        print(f"   - {ent['nom']}: themes {ent['thematiques_principales']}")