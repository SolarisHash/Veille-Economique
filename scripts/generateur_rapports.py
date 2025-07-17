#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de génération de rapports pour la veille économique
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
        """Création du DataFrame principal avec toutes les données"""
        donnees = []
        
        for entreprise in entreprises:
            ligne = {
                # Données de base
                'SIRET': entreprise.get('siret', ''),
                'Nom': entreprise.get('nom', ''),
                'Enseigne': entreprise.get('enseigne', ''),
                'Commune': entreprise.get('commune', ''),
                'Secteur_NAF': entreprise.get('secteur_naf', ''),
                'Code_NAF': entreprise.get('code_naf', ''),
                'Site_Web': entreprise.get('site_web', ''),
                'Dirigeant': entreprise.get('dirigeant', ''),
                
                # Scores d'analyse
                'Score_Global': round(entreprise.get('score_global', 0), 2),
                'Thematiques_Principales': ', '.join(entreprise.get('thematiques_principales', [])),
                'Date_Analyse': entreprise.get('date_analyse', ''),
            }
            
            # ✅ AJOUT : Résumé textuel global
            tous_extraits = []
            analyse = entreprise.get('analyse_thematique', {})
            
            for thematique in self.thematiques:
                if thematique in analyse and analyse[thematique].get('trouve', False):
                    result = analyse[thematique]
                    
                    # Extraction des informations textuelles pour le résumé
                    for detail in result.get('details', []):
                        info = detail.get('informations', {})
                        if 'extraits_textuels' in info:
                            for extrait in info['extraits_textuels']:
                                tous_extraits.append(f"{thematique}: {extrait['description']}")
                    
                    ligne[f'{thematique}_Trouvé'] = 'Oui'
                    ligne[f'{thematique}_Score'] = round(result['score_pertinence'], 2)
                    ligne[f'{thematique}_Confiance'] = result.get('niveau_confiance', 'N/A')
                    ligne[f'{thematique}_Sources'] = ', '.join(result.get('sources', []))
                else:
                    ligne[f'{thematique}_Trouvé'] = 'Non'
                    ligne[f'{thematique}_Score'] = 0.0
                    ligne[f'{thematique}_Confiance'] = 'N/A'
                    ligne[f'{thematique}_Sources'] = ''
            
            # ✅ AJOUT : Résumé textuel global
            ligne['Resume_Informations'] = ' | '.join(tous_extraits[:3])
            ligne['Nombre_Total_Mentions'] = len(tous_extraits)
            
            donnees.append(ligne)
            
        return pd.DataFrame(donnees)
        
    def _creer_dataframe_synthese(self, entreprises: List[Dict]) -> pd.DataFrame:
        """Création du DataFrame de synthèse thématique"""
        donnees_synthese = []
        
        for thematique in self.thematiques:
            entreprises_concernees = [
                e for e in entreprises 
                if e.get('analyse_thematique', {}).get(thematique, {}).get('trouve', False)
            ]
            
            if entreprises_concernees:
                scores = [
                    e['analyse_thematique'][thematique]['score_pertinence']
                    for e in entreprises_concernees
                ]
                
                ligne = {
                    'Thématique': thematique.replace('_', ' ').title(),
                    'Nb_Entreprises': len(entreprises_concernees),
                    'Pourcentage': round((len(entreprises_concernees) / len(entreprises)) * 100, 1),
                    'Score_Moyen': round(sum(scores) / len(scores), 2),
                    'Score_Max': round(max(scores), 2),
                    'Entreprises_Principales': ', '.join([
                        e['nom'] for e in sorted(entreprises_concernees, 
                                               key=lambda x: x['analyse_thematique'][thematique]['score_pertinence'], 
                                               reverse=True)[:3]
                    ])
                }
                donnees_synthese.append(ligne)
                
        return pd.DataFrame(donnees_synthese)
        
    def _creer_dataframe_thematique(self, entreprises: List[Dict], thematique: str) -> pd.DataFrame:
        """Création du DataFrame détaillé pour une thématique avec contenu textuel"""
        donnees_thematique = []
        
        for entreprise in entreprises:
            analyse = entreprise.get('analyse_thematique', {})
            if thematique in analyse and analyse[thematique].get('trouve', False):
                
                result = analyse[thematique]
                
                # ✅ CORRECTION : Extraction des informations textuelles
                extraits_textuels = []
                mots_cles_trouves = []
                
                for detail in result.get('details', []):
                    info = detail.get('informations', {})
                    
                    # Mots-clés trouvés
                    if 'mots_cles' in info:
                        mots_cles_trouves.extend(info['mots_cles'])
                    
                    # Extraits contextuels du site officiel
                    if 'extraits_contextuels' in info:
                        for extrait in info['extraits_contextuels']:
                            extraits_textuels.append(f"[{extrait['mot_cle']}] {extrait['contexte']}")
                    
                    # Extraits des recherches web
                    if 'extraits_textuels' in info:
                        for extrait in info['extraits_textuels']:
                            extraits_textuels.append(f"[Web] {extrait['titre']} - {extrait['description']}")
                    
                    # Résumé de contenu
                    if 'resume_contenu' in info:
                        extraits_textuels.append(f"[Résumé] {info['resume_contenu']}")
                    
                    # Extrait simple (ancien format)
                    if 'extrait' in info and info['extrait']:
                        extraits_textuels.append(f"[Source] {info['extrait']}")
                
                ligne = {
                    'Entreprise': entreprise['nom'],
                    'Commune': entreprise['commune'],
                    'SIRET': entreprise.get('siret', ''),
                    'Secteur': entreprise.get('secteur_naf', ''),
                    'Score_Pertinence': round(result['score_pertinence'], 2),
                    'Niveau_Confiance': result.get('niveau_confiance', 'N/A'),
                    'Sources': ', '.join(result.get('sources', [])),
                    'Mots_Cles_Trouves': ', '.join(set(mots_cles_trouves)),  # ✅ MOTS-CLÉS
                    'Informations_Textuelles': ' | '.join(extraits_textuels[:5]),  # ✅ CONTENU TEXTUEL !
                    'Nombre_Mentions': len(extraits_textuels),
                    'Date_Analyse': entreprise.get('date_analyse', ''),
                    'Site_Web': entreprise.get('site_web', '')
                }
                donnees_thematique.append(ligne)
                
        return pd.DataFrame(donnees_thematique)
        
    def _creer_dataframe_communes(self, entreprises: List[Dict]) -> pd.DataFrame:
        """Création du DataFrame de résumé par commune"""
        communes_stats = {}
        
        for entreprise in entreprises:
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
            scores = [e.get('score_global', 0) for e in entreprises_commune]
            
            ligne = {
                'Commune': commune,
                'Nb_Entreprises': len(entreprises_commune),
                'Score_Moyen': round(sum(scores) / len(scores) if scores else 0, 2),
                'Entreprises_Actives': len([e for e in entreprises_commune if e.get('score_global', 0) > 0.5]),
            }
            
            # Ajout des comptages par thématique
            for thematique in self.thematiques:
                ligne[f'{thematique}_Count'] = stats['thematiques_count'][thematique]
                
            # Thématique dominante
            thematique_dominante = max(stats['thematiques_count'].items(), key=lambda x: x[1])
            ligne['Thématique_Dominante'] = thematique_dominante[0] if thematique_dominante[1] > 0 else 'Aucune'
            
            donnees_communes.append(ligne)
            
        return pd.DataFrame(donnees_communes)
        
    def generer_rapport_html(self, entreprises_enrichies: List[Dict]) -> str:
        """Génération d'un rapport HTML interactif"""
        print("🌐 Génération du rapport HTML")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"rapport_veille_{timestamp}.html"
        chemin_fichier = self.dossier_sortie / nom_fichier
        
        # Statistiques globales
        stats_globales = self._calculer_statistiques_globales(entreprises_enrichies)
        
        # Génération du HTML
        html_content = self._generer_html_template(entreprises_enrichies, stats_globales)
        
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ Rapport HTML généré: {chemin_fichier}")
        return str(chemin_fichier)
        
    def _calculer_statistiques_globales(self, entreprises: List[Dict]) -> Dict:
        """Calcul des statistiques globales"""
        stats = {
            'nb_total': len(entreprises),
            'nb_actives': len([e for e in entreprises if e.get('score_global', 0) > 0.3]),
            'score_moyen': round(sum(e.get('score_global', 0) for e in entreprises) / len(entreprises), 2),
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
        
    def _generer_html_template(self, entreprises: List[Dict], stats: Dict) -> str:
        """Génération du template HTML"""
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
                .score {{ font-weight: bold; }}
                .score.high {{ color: #27ae60; }}
                .score.medium {{ color: #f39c12; }}
                .score.low {{ color: #e74c3c; }}
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
                    <p>Entreprises actives</p>
                </div>
                <div class="stat-box">
                    <h3>{stats['score_moyen']}</h3>
                    <p>Score moyen</p>
                </div>
                <div class="stat-box">
                    <h3>{stats['nb_communes']}</h3>
                    <p>Communes représentées</p>
                </div>
            </div>
            
            <h2>📊 Synthèse par Thématique</h2>
            {self._generer_section_thematiques(entreprises, stats)}
            
            <h2>🏘️ Résumé par Commune</h2>
            {self._generer_section_communes(entreprises)}
            
            <h2>📋 Détail des Entreprises</h2>
            {self._generer_section_entreprises(entreprises)}
            
        </body>
        </html>
        """
        return html
        
    def _generer_section_thematiques(self, entreprises: List[Dict], stats: Dict) -> str:
        """Génération de la section thématiques"""
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
                
                # Top 3 des entreprises
                top_entreprises = sorted(
                    entreprises_thematique, 
                    key=lambda x: x['analyse_thematique'][thematique]['score_pertinence'], 
                    reverse=True
                )[:3]
                
                for entreprise in top_entreprises:
                    score = entreprise['analyse_thematique'][thematique]['score_pertinence']
                    score_class = self._get_score_class(score)
                    
                    html += f"""
                    <div class="entreprise">
                        <strong>{entreprise['nom']}</strong> ({entreprise['commune']})
                        <span class="score {score_class}">Score: {score:.2f}</span>
                    </div>
                    """
                    
                html += "</div></div>"
                
        return html
        
    def _generer_section_communes(self, entreprises: List[Dict]) -> str:
        """Génération de la section communes"""
        communes_data = {}
        
        for entreprise in entreprises:
            commune = entreprise.get('commune', 'Inconnue')
            if commune not in communes_data:
                communes_data[commune] = []
            communes_data[commune].append(entreprise)
            
        html = "<table><tr><th>Commune</th><th>Entreprises</th><th>Score Moyen</th><th>Thématiques Actives</th></tr>"
        
        for commune, entreprises_commune in communes_data.items():
            scores = [e.get('score_global', 0) for e in entreprises_commune]
            score_moyen = sum(scores) / len(scores) if scores else 0
            
            # Comptage thématiques actives
            thematiques_actives = set()
            for entreprise in entreprises_commune:
                analyse = entreprise.get('analyse_thematique', {})
                for thematique in self.thematiques:
                    if analyse.get(thematique, {}).get('trouve', False):
                        thematiques_actives.add(thematique)
                        
            html += f"""
            <tr>
                <td><strong>{commune}</strong></td>
                <td>{len(entreprises_commune)}</td>
                <td><span class="score {self._get_score_class(score_moyen)}">{score_moyen:.2f}</span></td>
                <td>{len(thematiques_actives)}</td>
            </tr>
            """
            
        html += "</table>"
        return html
        
    def _generer_section_entreprises(self, entreprises: List[Dict]) -> str:
        """Génération de la section détail entreprises"""
        html = ""
        
        # Tri par score décroissant
        entreprises_triees = sorted(
            entreprises, 
            key=lambda x: x.get('score_global', 0), 
            reverse=True
        )
        
        for entreprise in entreprises_triees:
            score_global = entreprise.get('score_global', 0)
            score_class = self._get_score_class(score_global)
            
            html += f"""
            <div class="entreprise">
                <h4>{entreprise['nom']} ({entreprise['commune']})</h4>
                <p><strong>Score global:</strong> <span class="score {score_class}">{score_global:.2f}</span></p>
                <p><strong>Secteur:</strong> {entreprise.get('secteur_naf', 'Non spécifié')}</p>
                <p><strong>Thématiques principales:</strong> {', '.join(entreprise.get('thematiques_principales', []))}</p>
                
                <div style="margin-top: 10px;">
                    <strong>Détails thématiques:</strong>
                    <ul>
            """
            
            # Détails par thématique
            analyse = entreprise.get('analyse_thematique', {})
            for thematique in self.thematiques:
                if thematique in analyse and analyse[thematique].get('trouve', False):
                    result = analyse[thematique]
                    html += f"""
                    <li>{thematique.replace('_', ' ').title()}: 
                        <span class="score {self._get_score_class(result['score_pertinence'])}">{result['score_pertinence']:.2f}</span>
                        ({result.get('niveau_confiance', 'N/A')})
                    </li>
                    """
                    
            html += "</ul></div></div>"
            
        return html
        
    def _get_score_class(self, score: float) -> str:
        """Détermination de la classe CSS selon le score"""
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
            
    def generer_export_json(self, entreprises_enrichies: List[Dict]) -> str:
        """Export des données en format JSON"""
        print("📄 Export JSON")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"veille_data_{timestamp}.json"
        chemin_fichier = self.dossier_sortie / nom_fichier
        
        # Préparation des données pour l'export
        donnees_export = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'nb_entreprises': len(entreprises_enrichies),
                'version': '1.0.0'
            },
            'entreprises': entreprises_enrichies,
            'statistiques': self._calculer_statistiques_globales(entreprises_enrichies)
        }
        
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            json.dump(donnees_export, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Export JSON généré: {chemin_fichier}")
        return str(chemin_fichier)
        
    def generer_alertes_communes(self, entreprises_enrichies: List[Dict]) -> str:
        """Génération d'alertes ciblées par commune"""
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
            
        # Génération des alertes
        for commune, entreprises_commune in communes_data.items():
            alertes_commune = []
            
            # Alertes pour nouvelles activités
            for entreprise in entreprises_commune:
                if entreprise.get('score_global', 0) > 0.6:
                    thematiques_actives = [
                        thematique for thematique in entreprise.get('thematiques_principales', [])
                        if thematique in ['recrutements', 'innovations', 'vie_entreprise']
                    ]
                    
                    if thematiques_actives:
                        alertes_commune.append({
                            'type': 'activite_elevee',
                            'entreprise': entreprise['nom'],
                            'score': entreprise['score_global'],
                            'thematiques': thematiques_actives,
                            'priorite': 'haute' if entreprise['score_global'] > 0.8 else 'moyenne'
                        })
                        
            # Alertes spécifiques par thématique
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
                
        # Sauvegarde
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            json.dump(alertes, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Alertes générées: {chemin_fichier}")
        return str(chemin_fichier)
        
    def generer_tous_rapports(self, entreprises_enrichies: List[Dict]) -> Dict[str, str]:
        """Génération de tous les rapports"""
        print("📊 Génération de tous les rapports")
        
        rapports = {
            'excel': self.generer_rapport_excel(entreprises_enrichies),
            'html': self.generer_rapport_html(entreprises_enrichies),
            'json': self.generer_export_json(entreprises_enrichies),
            'alertes': self.generer_alertes_communes(entreprises_enrichies)
        }
        
        print("✅ Tous les rapports générés avec succès")
        return rapports