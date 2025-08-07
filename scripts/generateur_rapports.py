#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de génération de rapports pour la veille économique
Version modifiée pour le rapport HTML sans scores
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional
import os
from pathlib import Path

class GenerateurRapports:
    """Générateur de rapports multi-format pour la veille économique"""
    
    def __init__(self, dossier_sortie: str = "data/output"):
        """Initialisation du générateur"""
        self.dossier_sortie = Path(dossier_sortie)
        self.dossier_sortie.mkdir(parents=True, exist_ok=True)
        
        self.thematiques = [
            'evenements', 'recrutements', 'vie_entreprise', 'innovations',
            'exportations', 'aides_subventions', 'fondation_sponsor'
        ]
        
    def generer_rapport_excel(self, entreprises_enrichies: List[Dict]) -> str:
        """Génération du rapport Excel enrichi"""
        print("📊 Génération du rapport Excel")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"veille_economique_{timestamp}.xlsx"
        chemin_fichier = self.dossier_sortie / nom_fichier
        
        with pd.ExcelWriter(chemin_fichier, engine='openpyxl') as writer:
            
            # Feuille 1: Données enrichies principales
            df_principal = self._creer_dataframe_principal(entreprises_enrichies)
            df_principal.to_excel(writer, sheet_name='Données_Enrichies', index=False)
            
            # Feuille 2: Synthèse thématique
            df_synthese = self._creer_dataframe_synthese(entreprises_enrichies)
            df_synthese.to_excel(writer, sheet_name='Synthèse_Thématique', index=False)
            
            # Feuille 3: Détails par thématique
            for thematique in self.thematiques:
                df_thematique = self._creer_dataframe_thematique(entreprises_enrichies, thematique)
                if not df_thematique.empty:
                    nom_feuille = thematique.replace('_', ' ').title()[:31]  # Limite Excel
                    df_thematique.to_excel(writer, sheet_name=nom_feuille, index=False)
                    
            # Feuille 4: Résumé par commune
            df_communes = self._creer_dataframe_communes(entreprises_enrichies)
            df_communes.to_excel(writer, sheet_name='Résumé_Communes', index=False)
            
        print(f"✅ Rapport Excel généré: {chemin_fichier}")
        return str(chemin_fichier)
        
    def _creer_dataframe_principal(self, entreprises: List[Dict]) -> pd.DataFrame:
        """Version SANS SCORES - Focus sur les entreprises actives uniquement"""
        donnees = []
        
        for entreprise in entreprises:
            # ✅ FILTRAGE : Seulement les entreprises avec activité
            if entreprise.get('score_global', 0) <= 0.1:
                continue  # Skip les entreprises sans activité
            
            ligne = {
                # Données de base (inchangées)
                'SIRET': entreprise.get('siret', ''),
                'Nom': entreprise.get('nom', ''),
                'Enseigne': entreprise.get('enseigne', ''),
                'Commune': entreprise.get('commune', ''),
                'Secteur_NAF': entreprise.get('secteur_naf', ''),
                'Code_NAF': entreprise.get('code_naf', ''),
                'Site_Web': entreprise.get('site_web', ''),
                'Dirigeant': entreprise.get('dirigeant', ''),
                
                # ❌ SUPPRIMÉ : Score_Global, Thematiques_Principales (basés sur scores)
                'Date_Analyse': entreprise.get('date_analyse', ''),
                'Activités_Détectées': ', '.join(entreprise.get('thematiques_principales', [])),
            }
            
            # ✅ EXTRACTION DÉTAILLÉE SANS SCORES
            tous_extraits = []
            tous_liens = []
            resume_par_thematique = {}
            
            analyse = entreprise.get('analyse_thematique', {})
            
            for thematique in self.thematiques:
                if thematique in analyse and analyse[thematique].get('trouve', False):
                    result = analyse[thematique]
                    
                    # Informations détaillées par thématique
                    infos_thematique = []
                    liens_thematique = []
                    
                    for detail in result.get('details', []):
                        info = detail.get('informations', {})
                        
                        # Extraits textuels des recherches web
                        if 'extraits_textuels' in info:
                            for extrait in info['extraits_textuels']:
                                titre = extrait.get('titre', '')
                                description = extrait.get('description', '')
                                url = extrait.get('url', '')
                                
                                if titre and description:
                                    info_complete = f"{titre}: {description}"
                                    infos_thematique.append(info_complete)
                                    tous_extraits.append(f"[{thematique}] {info_complete}")
                                    
                                    if url:
                                        liens_thematique.append(url)
                                        tous_liens.append(url)
                    
                    # Résumé pour cette thématique
                    resume_par_thematique[thematique] = ' | '.join(infos_thematique[:2])
                    
                    # ✅ COLONNES PAR THÉMATIQUE SANS SCORES
                    ligne[f'{thematique}_Détecté'] = 'Oui'
                    # ❌ SUPPRIMÉ : ligne[f'{thematique}_Score'] 
                    # ❌ SUPPRIMÉ : ligne[f'{thematique}_Confiance']
                    ligne[f'{thematique}_Sources'] = ', '.join(result.get('sources', []))
                    ligne[f'{thematique}_Détails'] = resume_par_thematique[thematique]
                    ligne[f'{thematique}_Liens'] = ' | '.join(list(set(liens_thematique))[:2])
                else:
                    ligne[f'{thematique}_Détecté'] = 'Non'
                    # ❌ SUPPRIMÉ : Colonnes score/confiance pour "Non"
                    ligne[f'{thematique}_Sources'] = ''
                    ligne[f'{thematique}_Détails'] = ''
                    ligne[f'{thematique}_Liens'] = ''
            
            # ✅ COLONNES GLOBALES SANS SCORES
            liens_uniques = list(set([lien for lien in tous_liens if lien and lien.startswith('http')]))
            
            ligne['Résumé_Complet'] = ' | '.join(tous_extraits[:5])
            ligne['Nombre_Total_Informations'] = len(tous_extraits)
            ligne['Liens_Sources_Principaux'] = ' | '.join(liens_uniques[:3])
            ligne['Nombre_Sources_Uniques'] = len(liens_uniques)
            ligne['Première_Source'] = liens_uniques[0] if liens_uniques else ''
            ligne['Activité_Principale'] = self._determiner_activite_principale(resume_par_thematique)
            
            donnees.append(ligne)
            
        return pd.DataFrame(donnees)

    def _determiner_activite_principale(self, resume_par_thematique: Dict[str, str]) -> str:
        """Détermine l'activité principale basée sur les résumés"""
        if not resume_par_thematique:
            return "Aucune activité détectée"
        
        # Trouve la thématique avec le plus d'informations
        thematique_principale = max(resume_par_thematique.items(), key=lambda x: len(x[1]))
        
        if thematique_principale[1]:  # Si il y a du contenu
            nom_thematique = thematique_principale[0].replace('_', ' ').title()
            return f"{nom_thematique}: {thematique_principale[1][:100]}..."
        
        return "Informations limitées"
        
    def _creer_dataframe_thematique(self, entreprises: List[Dict], thematique: str) -> pd.DataFrame:
        """DataFrame thématique SANS SCORES - Seulement entreprises avec cette thématique"""
        donnees_thematique = []
        
        for entreprise in entreprises:
            analyse = entreprise.get('analyse_thematique', {})
            if thematique in analyse and analyse[thematique].get('trouve', False):
                
                result = analyse[thematique]
                
                # ✅ EXTRACTION COMPLÈTE DES INFORMATIONS SANS SCORES
                extraits_textuels = []
                mots_cles_trouves = []
                liens_sources = []
                details_evenements = []
                
                # Parcours de tous les détails trouvés
                for detail in result.get('details', []):
                    source = detail.get('source', 'Inconnue')
                    info = detail.get('informations', {})
                    
                    # 1. Mots-clés trouvés
                    if 'mots_cles' in info:
                        mots_cles_trouves.extend(info['mots_cles'])
                    
                    # 2. Liens sources
                    if 'url' in info and info['url']:
                        liens_sources.append(info['url'])
                    
                    # 3. Extraits avec détails
                    if 'extraits_textuels' in info:
                        for extrait in info['extraits_textuels']:
                            details_evenements.append({
                                'source': 'Recherche web',
                                'titre': extrait.get('titre', ''),
                                'contenu': extrait.get('description', ''),
                                'url': extrait.get('url', ''),
                                'extrait_complet': extrait.get('extrait_complet', '')
                            })
                
                # ✅ FORMATAGE DES INFORMATIONS DÉTAILLÉES
                informations_detaillees = []
                for i, detail in enumerate(details_evenements[:5], 1):
                    if detail.get('titre'):
                        info_text = f"[{detail['source']}] {detail['titre']}: {detail['contenu']}"
                    else:
                        info_text = f"[{detail['source']}] {detail['contenu']}"
                    
                    if detail.get('url'):
                        info_text += f" (Source: {detail['url']})"
                    
                    informations_detaillees.append(info_text)
                
                # Liens sources uniques
                liens_uniques = list(set([lien for lien in liens_sources if lien and lien != '']))
                liens_formattes = []
                for lien in liens_uniques[:3]:
                    if lien.startswith('http'):
                        liens_formattes.append(lien)
                    else:
                        liens_formattes.append(f"https://{lien}")
                
                ligne = {
                    'Entreprise': entreprise['nom'],
                    'Commune': entreprise['commune'],
                    'SIRET': entreprise.get('siret', ''),
                    'Secteur': entreprise.get('secteur_naf', ''),
                    
                    # ❌ SUPPRIMÉ : Score_Pertinence, Niveau_Confiance
                    
                    'Sources_Analysées': ', '.join(result.get('sources', [])),
                    'Mots_Cles_Detectés': ', '.join(set(mots_cles_trouves)),
                    'Détails_Informations': ' | '.join(informations_detaillees),
                    'Liens_Sources': ' | '.join(liens_formattes),
                    'Nombre_Sources': len(liens_uniques),
                    'Première_Source': liens_formattes[0] if liens_formattes else '',
                    'Résumé_Activité': self._extraire_resume_evenement(details_evenements, thematique),
                    'Nombre_Mentions': len(details_evenements),
                    'Date_Analyse': entreprise.get('date_analyse', ''),
                    'Site_Web_Entreprise': entreprise.get('site_web', '')
                }
                donnees_thematique.append(ligne)
                
        return pd.DataFrame(donnees_thematique)
    
    def _extraire_resume_evenement(self, details_evenements: List[Dict], thematique: str) -> str:
        """Extraction d'un résumé intelligent de l'événement"""
        if not details_evenements:
            return ""
        
        # Combinaison des contenus pour créer un résumé
        contenus = []
        for detail in details_evenements[:3]:  # Top 3 détails
            contenu = detail.get('contenu', '')
            if contenu and len(contenu) > 20:  # Contenu significatif
                contenus.append(contenu)
        
        if not contenus:
            return ""
        
        # Résumé intelligent selon la thématique
        if thematique == 'recrutements':
            return f"Recrutement détecté: {' | '.join(contenus)}"
        elif thematique == 'evenements':
            return f"Événement identifié: {' | '.join(contenus)}"
        elif thematique == 'innovations':
            return f"Innovation repérée: {' | '.join(contenus)}"
        elif thematique == 'vie_entreprise':
            return f"Développement entreprise: {' | '.join(contenus)}"
        else:
            return f"Activité {thematique}: {' | '.join(contenus)}"
        
    def _creer_dataframe_communes(self, entreprises: List[Dict]) -> pd.DataFrame:
        """Résumé par commune SANS SCORES - Seulement communes avec activité"""
        communes_stats = {}
        
        # ✅ FILTRAGE : Seulement entreprises actives
        entreprises_actives = [e for e in entreprises if e.get('score_global', 0) > 0.1]
        
        for entreprise in entreprises_actives:  # Seulement les actives
            commune = entreprise.get('commune', 'Inconnue')
            
            if commune not in communes_stats:
                communes_stats[commune] = {
                    'entreprises': [],
                    'thematiques_count': {thematique: 0 for thematique in self.thematiques}
                }
                
            communes_stats[commune]['entreprises'].append(entreprise)
            
            # Comptage par thématique
            analyse = entreprise.get('analyse_thematique', {})
            for thematique in self.thematiques:
                if analyse.get(thematique, {}).get('trouve', False):
                    communes_stats[commune]['thematiques_count'][thematique] += 1
                    
        # Création du DataFrame
        donnees_communes = []
        for commune, stats in communes_stats.items():
            entreprises_commune = stats['entreprises']
            
            ligne = {
                'Commune': commune,
                'Nb_Entreprises_Actives': len(entreprises_commune),
                
                # ❌ SUPPRIMÉ : Score_Moyen, Entreprises_Actives (basé sur score > 0.5)
                
                # ✅ AJOUTÉ : Informations descriptives
                'Entreprises_Noms': ', '.join([e['nom'] for e in entreprises_commune]),
                'Secteurs_Présents': ', '.join(list(set([
                    e.get('secteur_naf', 'Non spécifié').split(' ')[0]  # Premier mot du secteur
                    for e in entreprises_commune
                ]))),
            }
            
            # Ajout des comptages par thématique (inchangé)
            for thematique in self.thematiques:
                ligne[f'{thematique}_Count'] = stats['thematiques_count'][thematique]
                
            # Thématique dominante (sans référence au score)
            thematique_dominante = max(stats['thematiques_count'].items(), key=lambda x: x[1])
            ligne['Thématique_Dominante'] = thematique_dominante[0] if thematique_dominante[1] > 0 else 'Aucune'
            
            donnees_communes.append(ligne)
            
        return pd.DataFrame(donnees_communes)

    def _creer_dataframe_synthese(self, entreprises: List[Dict]) -> pd.DataFrame:
        """Synthèse SANS SCORES - Focus quantitatif et qualitatif"""
        donnees_synthese = []
        
        # ✅ FILTRAGE : Seulement entreprises actives
        entreprises_actives = [e for e in entreprises if e.get('score_global', 0) > 0.1]
        
        for thematique in self.thematiques:
            entreprises_concernees = [
                e for e in entreprises_actives
                if e.get('analyse_thematique', {}).get(thematique, {}).get('trouve', False)
            ]
            
            if entreprises_concernees:
                ligne = {
                    'Thématique': thematique.replace('_', ' ').title(),
                    'Nb_Entreprises_Actives': len(entreprises_concernees),
                    'Pourcentage_du_Total': round((len(entreprises_concernees) / len(entreprises)) * 100, 1),
                    'Pourcentage_des_Actives': round((len(entreprises_concernees) / len(entreprises_actives)) * 100, 1),
                    
                    # ❌ SUPPRIMÉ : Score_Moyen, Score_Max
                    
                    # ✅ AJOUTÉ : Informations qualitatives
                    'Entreprises_Concernées': ', '.join([
                        e['nom'] for e in entreprises_concernees[:5]  # Top 5 au lieu de tri par score
                    ]),
                    'Secteurs_Représentés': ', '.join(list(set([
                        e.get('secteur_naf', 'Non spécifié')[:30] + '...' 
                        if len(e.get('secteur_naf', '')) > 30 
                        else e.get('secteur_naf', 'Non spécifié')
                        for e in entreprises_concernees
                    ])))
                }
                donnees_synthese.append(ligne)
                
        return pd.DataFrame(donnees_synthese)

    def generer_rapport_html(self, entreprises_enrichies: List[Dict]) -> str:
        """✅ Génération HTML SANS SCORES - Version adaptée"""
        print("🌐 Génération du rapport HTML (sans scores)")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"rapport_veille_{timestamp}.html"
        chemin_fichier = self.dossier_sortie / nom_fichier
        
        # ✅ Statistiques globales SANS SCORES
        stats_globales = self._calculer_statistiques_sans_scores(entreprises_enrichies)
        
        # ✅ Génération du HTML SANS SCORES
        html_content = self._generer_html_template_sans_scores(entreprises_enrichies, stats_globales)
        
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ Rapport HTML généré: {chemin_fichier}")
        return str(chemin_fichier)
    
    def _calculer_statistiques_sans_scores(self, entreprises: List[Dict]) -> Dict:
        """✅ Calcul des statistiques globales SANS SCORES"""
        # Filtrage entreprises actives (avec activité détectée)
        entreprises_actives = [e for e in entreprises if e.get('score_global', 0) > 0.1]
        
        stats = {
            'nb_total': len(entreprises),
            'nb_actives': len(entreprises_actives),
            # ❌ SUPPRIMÉ : 'score_moyen' - remplacé par pourcentage d'activité
            'pourcentage_actives': round((len(entreprises_actives) / len(entreprises)) * 100, 1) if len(entreprises) > 0 else 0,
            'nb_communes': len(set(e.get('commune', '') for e in entreprises)),
            'thematiques_stats': {}
        }
        
        for thematique in self.thematiques:
            nb_entreprises = sum(
                1 for e in entreprises 
                if e.get('analyse_thematique', {}).get(thematique, {}).get('trouve', False)
            )
            stats['thematiques_stats'][thematique] = {
                'count': nb_entreprises,
                'percentage': round((nb_entreprises / len(entreprises)) * 100, 1)
            }
            
        return stats
        
    def _generer_html_template_sans_scores(self, entreprises: List[Dict], stats: Dict) -> str:
        """✅ Génération du template HTML SANS SCORES"""
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport de Veille Économique</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
                .thematique {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }}
                .entreprise {{ margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-radius: 3px; }}
                .activite {{ font-weight: bold; color: #27ae60; }}
                .info-entreprise {{ color: #34495e; font-size: 0.9em; margin-top: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏢 Rapport de Veille Économique Territoriale</h1>
                <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>{stats['nb_total']}</h3>
                    <p>Entreprises analysées</p>
                </div>
                <div class="stat-box">
                    <h3>{stats['nb_actives']}</h3>
                    <p>Entreprises avec activité</p>
                </div>
                <div class="stat-box">
                    <h3>{stats['pourcentage_actives']}%</h3>
                    <p>Taux d'activité détectée</p>
                </div>
                <div class="stat-box">
                    <h3>{stats['nb_communes']}</h3>
                    <p>Communes représentées</p>
                </div>
            </div>
            
            <h2>📊 Synthèse par Thématique</h2>
            {self._generer_section_thematiques_sans_scores(entreprises, stats)}
            
            <h2>🏘️ Résumé par Commune</h2>
            {self._generer_section_communes_sans_scores(entreprises)}
            
            <h2>📋 Détail des Entreprises</h2>
            {self._generer_section_entreprises_sans_scores(entreprises)}
            
        </body>
        </html>
        """
        return html
        
    def _generer_section_thematiques_sans_scores(self, entreprises: List[Dict], stats: Dict) -> str:
        """✅ Génération de la section thématiques SANS SCORES"""
        html = ""
        
        for thematique in self.thematiques:
            thematique_stats = stats['thematiques_stats'][thematique]
            entreprises_thematique = [
                e for e in entreprises 
                if e.get('analyse_thematique', {}).get(thematique, {}).get('trouve', False)
            ]
            
            if entreprises_thematique:
                html += f"""
                <div class="thematique">
                    <h3>{thematique.replace('_', ' ').title()}</h3>
                    <p><strong>{thematique_stats['count']} entreprises</strong> ({thematique_stats['percentage']}%)</p>
                    <div style="margin-top: 10px;">
                """
                
                # ✅ Top entreprises SANS SCORES (par ordre alphabétique)
                top_entreprises = sorted(entreprises_thematique, key=lambda x: x.get('nom', ''))[:3]
                
                for entreprise in top_entreprises:
                    # ✅ Extraction d'informations détaillées au lieu du score
                    analyse = entreprise.get('analyse_thematique', {})
                    details_thematique = analyse.get(thematique, {}).get('details', [])
                    
                    # Résumé de l'activité pour cette thématique
                    resume_activite = "Activité détectée"
                    if details_thematique:
                        info = details_thematique[0].get('informations', {})
                        extraits = info.get('extraits_textuels', [])
                        if extraits and extraits[0].get('titre'):
                            resume_activite = extraits[0]['titre'][:50] + "..."
                    
                    html += f"""
                    <div class="entreprise">
                        <strong>{entreprise['nom']}</strong> ({entreprise['commune']})
                        <div class="activite">{resume_activite}</div>
                    </div>
                    """
                    
                html += "</div></div>"
                
        return html
        
    def _generer_section_communes_sans_scores(self, entreprises: List[Dict]) -> str:
        """✅ Génération de la section communes SANS SCORES"""
        communes_data = {}
        
        # Seulement les entreprises avec activité
        entreprises_actives = [e for e in entreprises if e.get('score_global', 0) > 0.1]
        
        for entreprise in entreprises_actives:
            commune = entreprise.get('commune', 'Inconnue')
            if commune not in communes_data:
                communes_data[commune] = []
            communes_data[commune].append(entreprise)
            
        html = "<table><tr><th>Commune</th><th>Entreprises</th><th>Activités Principales</th><th>Thématiques Actives</th></tr>"
        
        for commune, entreprises_commune in communes_data.items():
            # ✅ Thématiques actives SANS SCORES
            thematiques_actives = set()
            activites_principales = []
            
            for entreprise in entreprises_commune:
                analyse = entreprise.get('analyse_thematique', {})
                for thematique in self.thematiques:
                    if analyse.get(thematique, {}).get('trouve', False):
                        thematiques_actives.add(thematique.replace('_', ' ').title())
                
                # Activité principale de l'entreprise
                thematiques_entreprise = [
                    t for t in self.thematiques 
                    if analyse.get(t, {}).get('trouve', False)
                ]
                if thematiques_entreprise:
                    activites_principales.append(thematiques_entreprise[0].replace('_', ' ').title())
            
            # ✅ Résumé des activités principales
            from collections import Counter
            activites_counter = Counter(activites_principales)
            top_activites = [f"{act} ({count})" for act, count in activites_counter.most_common(3)]
            
            html += f"""
            <tr>
                <td><strong>{commune}</strong></td>
                <td>{len(entreprises_commune)} entreprises actives</td>
                <td>{', '.join(top_activites) if top_activites else 'Aucune'}</td>
                <td>{len(thematiques_actives)} thématiques</td>
            </tr>
            """
            
        html += "</table>"
        return html

    def _generer_section_entreprises_sans_scores(self, entreprises: List[Dict]) -> str:
        """✅ Section entreprises HTML SANS SCORES - Seulement les actives"""
        html = ""
        
        # ✅ FILTRAGE : Seulement entreprises actives
        entreprises_actives = [e for e in entreprises if e.get('score_global', 0) > 0.1]
        
        # Tri par nom au lieu de score
        entreprises_triees = sorted(entreprises_actives, key=lambda x: x.get('nom', ''))
        
        for entreprise in entreprises_triees:
            html += f"""
            <div class="entreprise" style="margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h4 style="color: #2c3e50; margin-bottom: 10px;">
                    {entreprise['nom']} ({entreprise['commune']})
                </h4>
                <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                    <div><strong>Secteur:</strong> {entreprise.get('secteur_naf', 'Non spécifié')}</div>
                    <div><strong>SIRET:</strong> {entreprise.get('siret', 'N/A')}</div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>Activités détectées:</strong> {', '.join(entreprise.get('thematiques_principales', []))}
                </div>
            """
            
            # ✅ DÉTAILS PAR THÉMATIQUE SANS SCORES
            analyse = entreprise.get('analyse_thematique', {})
            thematiques_trouvees = [t for t in self.thematiques if t in analyse and analyse[t].get('trouve', False)]
            
            if thematiques_trouvees:
                html += f"""
                <div style="margin-top: 20px;">
                    <strong style="color: #2c3e50;">📋 Détails des activités détectées:</strong>
                """
                
                for thematique in thematiques_trouvees:
                    result = analyse[thematique]
                    
                    html += f"""
                    <div style="margin: 15px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #3498db;">
                        <h5 style="color: #2c3e50; margin: 0 0 10px 0;">
                            {thematique.replace('_', ' ').title()}
                        </h5>
                    """
                    
                    # Extraction des informations détaillées SANS SCORES
                    details_info = []
                    liens_sources = []
                    
                    for detail in result.get('details', []):
                        info = detail.get('informations', {})
                        
                        # Extraits textuels avec sources
                        if 'extraits_textuels' in info:
                            for extrait in info['extraits_textuels']:
                                details_info.append({
                                    'type': 'web',
                                    'titre': extrait.get('titre', ''),
                                    'contenu': extrait.get('description', ''),
                                    'url': extrait.get('url', '')
                                })
                    
                    # Affichage des détails SANS SCORES
                    if details_info:
                        html += "<div style='margin-top: 10px;'>"
                        
                        for i, detail in enumerate(details_info[:3], 1):
                            icon = "🌐" if detail['type'] == 'web' else "📱"
                            
                            html += f"""
                            <div style="margin: 8px 0; padding: 8px; background-color: white; border-radius: 4px;">
                                <div style="font-weight: bold; color: #34495e;">
                                    {icon} {detail['titre']}
                                </div>
                                <div style="margin: 5px 0; color: #2c3e50;">
                                    {detail['contenu'][:300]}{'...' if len(detail['contenu']) > 300 else ''}
                                </div>
                            """
                            
                            if detail['url']:
                                html += f"""
                                <div style="margin-top: 5px;">
                                    <a href="{detail['url']}" target="_blank" style="color: #3498db; text-decoration: none; font-size: 0.9em;">
                                        🔗 Voir la source
                                    </a>
                                </div>
                                """
                            
                            html += "</div>"
                        
                        html += "</div>"
                    
                    html += "</div>"  # Fin de la thématique
                
                html += "</div>"  # Fin des détails
            
            # Site web de l'entreprise (inchangé)
            if entreprise.get('site_web'):
                html += f"""
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ecf0f1;">
                    <strong>🌐 Site web:</strong> 
                    <a href="{entreprise['site_web']}" target="_blank" style="color: #3498db;">
                        {entreprise['site_web']}
                    </a>
                </div>
                """
            
            html += "</div>"  # Fin de l'entreprise
            
        return html

    def generer_export_json(self, entreprises_enrichies: List[Dict]) -> str:
        """Export des données en format JSON avec gestion des types non sérialisables"""
        print("📄 Export JSON")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"veille_data_{timestamp}.json"
        chemin_fichier = self.dossier_sortie / nom_fichier
        
        # Préparation des données pour l'export avec nettoyage
        donnees_export = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'nb_entreprises': len(entreprises_enrichies),
                'version': '1.0.0'
            },
            'entreprises': self._nettoyer_pour_json(entreprises_enrichies),
            # ✅ Statistiques SANS SCORES pour JSON
            'statistiques': self._calculer_statistiques_sans_scores(entreprises_enrichies)
        }
        
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            json.dump(donnees_export, f, ensure_ascii=False, indent=2, default=self._json_serializer)
            
        print(f"✅ Export JSON généré: {chemin_fichier}")
        return str(chemin_fichier)
        
    def _nettoyer_pour_json(self, data):
        """Nettoyage récursif des données pour la sérialisation JSON"""
        if isinstance(data, dict):
            return {key: self._nettoyer_pour_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._nettoyer_pour_json(item) for item in data]
        elif hasattr(data, 'isoformat'):  # datetime, Timestamp
            return data.isoformat()
        elif hasattr(data, 'item'):  # numpy types
            return data.item()
        elif str(type(data)).startswith('<class \'pandas'):  # pandas types
            return str(data)
        else:
            return data
            
    def _json_serializer(self, obj):
        """Sérialiseur personnalisé pour JSON"""
        import pandas as pd
        import numpy as np
        
        # Gestion des types pandas
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Custom objects
            return obj.__dict__
        else:
            return str(obj)
        
    def generer_alertes_communes(self, entreprises_enrichies: List[Dict]) -> str:
        """✅ Génération d'alertes ciblées par commune SANS SCORES"""
        print("🚨 Génération d'alertes par commune")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"alertes_communes_{timestamp}.json"
        chemin_fichier = self.dossier_sortie / nom_fichier
        
        alertes = {}
        
        # Groupement par commune
        communes_data = {}
        for entreprise in entreprises_enrichies:
            commune = entreprise.get('commune', 'Inconnue')
            if commune not in communes_data:
                communes_data[commune] = []
            communes_data[commune].append(entreprise)
            
        # Génération des alertes SANS SCORES
        for commune, entreprises_commune in communes_data.items():
            alertes_commune = []
            
            # ✅ Alertes pour nouvelles activités (basées sur présence d'activité, pas score)
            entreprises_actives = [e for e in entreprises_commune if e.get('score_global', 0) > 0.1]
            
            for entreprise in entreprises_actives:
                thematiques_actives = [
                    thematique for thematique in self.thematiques
                    if entreprise.get('analyse_thematique', {}).get(thematique, {}).get('trouve', False)
                    and thematique in ['recrutements', 'innovations', 'vie_entreprise']
                ]
                
                if thematiques_actives:
                    # ✅ Priorité basée sur nombre de thématiques, pas sur score
                    priorite = 'haute' if len(thematiques_actives) >= 2 else 'moyenne'
                    
                    alertes_commune.append({
                        'type': 'activite_detectee',
                        'entreprise': entreprise['nom'],
                        'thematiques': thematiques_actives,
                        'nb_thematiques': len(thematiques_actives),
                        'priorite': priorite
                    })
                        
            # ✅ Alertes spécifiques par thématique SANS SCORES
            for thematique in ['recrutements', 'innovations']:
                entreprises_thematique = [
                    e for e in entreprises_commune
                    if e.get('analyse_thematique', {}).get(thematique, {}).get('trouve', False)
                ]
                
                if len(entreprises_thematique) > 2:  # Seuil d'alerte
                    alertes_commune.append({
                        'type': f'concentration_{thematique}',
                        'nb_entreprises': len(entreprises_thematique),
                        'entreprises': [e['nom'] for e in entreprises_thematique],
                        'priorite': 'moyenne'
                    })
                    
            if alertes_commune:
                alertes[commune] = {
                    'nb_alertes': len(alertes_commune),
                    'alertes': alertes_commune,
                    'timestamp': datetime.now().isoformat()
                }
                
        # Sauvegarde avec gestion des types non sérialisables
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            json.dump(alertes, f, ensure_ascii=False, indent=2, default=self._json_serializer)
            
        print(f"✅ Alertes générées: {chemin_fichier}")
        return str(chemin_fichier)
        
    def generer_tous_rapports(self, entreprises_enrichies: List[Dict]) -> Dict[str, str]:
        """Génération de tous les rapports avec gestion d'erreurs individuelles"""
        print("📊 Génération de tous les rapports")
        
        rapports = {}
        
        # 1. Rapport Excel (prioritaire) - AVEC SCORES
        try:
            print("📊 Génération rapport Excel...")
            rapports['excel'] = self.generer_rapport_excel(entreprises_enrichies)
        except Exception as e:
            print(f"❌ Erreur rapport Excel: {str(e)}")
            rapports['excel'] = f"ERREUR: {str(e)}"
        
        # 2. Rapport HTML - ✅ SANS SCORES
        try:
            print("🌐 Génération rapport HTML (sans scores)...")
            rapports['html'] = self.generer_rapport_html(entreprises_enrichies)
        except Exception as e:
            print(f"❌ Erreur rapport HTML: {str(e)}")
            rapports['html'] = f"ERREUR: {str(e)}"
        
        # 3. Export JSON (avec gestion spéciale des Timestamp) - SANS SCORES pour statistiques
        try:
            print("📄 Génération export JSON...")
            rapports['json'] = self.generer_export_json(entreprises_enrichies)
        except Exception as e:
            print(f"❌ Erreur export JSON: {str(e)}")
            rapports['json'] = f"ERREUR: {str(e)}"
        
        # 4. Alertes communes - SANS SCORES
        try:
            print("🚨 Génération alertes communes...")
            rapports['alertes'] = self.generer_alertes_communes(entreprises_enrichies)
        except Exception as e:
            print(f"❌ Erreur alertes: {str(e)}")
            rapports['alertes'] = f"ERREUR: {str(e)}"
        
        # Compte des rapports générés avec succès
        rapports_reussis = len([r for r in rapports.values() if not r.startswith("ERREUR:")])
        print(f"✅ {rapports_reussis}/{len(rapports)} rapports générés avec succès")
        
        return rapports