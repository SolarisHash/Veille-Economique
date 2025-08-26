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
        entreprises_actives = [e for e in entreprises if e.get('score_global', 0) > 0.1]

        for e in entreprises_actives:
            commune = e.get('commune', 'Inconnue')
            if commune not in communes_stats:
                communes_stats[commune] = {
                    'entreprises': {},  # <- dict pour dédup SIRET+Nom
                    'thematiques_count': {thematique: 0 for thematique in self.thematiques}
                }
            cle = f"{e.get('siret','')}_{e.get('nom','')}".strip('_')
            communes_stats[commune]['entreprises'][cle] = e  # overwrite safe (dédup)

            analyse = e.get('analyse_thematique', {})
            for thematique in self.thematiques:
                if analyse.get(thematique, {}).get('trouve', False):
                    communes_stats[commune]['thematiques_count'][thematique] += 1

        # Création du DataFrame
        donnees_communes = []
        for commune, stats in communes_stats.items():
            entreprises_commune = list(stats['entreprises'].values())

            # Noms sans doublon et triés alpha pour la lisibilité
            noms_uniques = sorted({ec['nom'] for ec in entreprises_commune})

            ligne = {
                'Commune': commune,
                'Nb_Entreprises_Actives': len(entreprises_commune),
                'Entreprises_Noms': ', '.join(noms_uniques),  # <- plus de doublons "X, X"
                'Secteurs_Présents': ', '.join(list(set([
                    ec.get('secteur_naf', 'Non spécifié').split(' ')[0]
                    for ec in entreprises_commune
                ]))),
            }
            for thematique in self.thematiques:
                ligne[f'{thematique}_Count'] = stats['thematiques_count'][thematique]

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
            # Ensemble d'entreprises uniques (SIRET+Nom) concernées par la thématique
            uniques_par_theme = {}
            for e in entreprises_actives:
                et = e.get('analyse_thematique', {}).get(thematique, {})
                if et.get('trouve', False):
                    cle = f"{e.get('siret','')}_{e.get('nom','')}".strip('_')
                    if cle not in uniques_par_theme:
                        uniques_par_theme[cle] = e

            entreprises_concernees = list(uniques_par_theme.values())

            if entreprises_concernees:
                # Liste des noms sans doublon
                noms_uniques = []
                vus = set()
                for e in entreprises_concernees:
                    nom = e['nom']
                    if nom not in vus:
                        vus.add(nom)
                        noms_uniques.append(nom)
                ligne = {
                    'Thématique': thematique.replace('_', ' ').title(),
                    'Nb_Entreprises_Actives': len(entreprises_concernees),
                    'Pourcentage_du_Total': round((len(entreprises_concernees) / len(entreprises)) * 100, 1) if len(entreprises) else 0,
                    'Pourcentage_des_Actives': round((len(entreprises_concernees) / len(entreprises_actives)) * 100, 1) if len(entreprises_actives) else 0,
                    'Entreprises_Concernées': ', '.join(noms_uniques[:5]),
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
            
        # Génération du HTML
        html_content = self._generer_html_template_sans_scores(entreprises_enrichies, stats_globales)

        # 🔧 Post-traitement HTML (suppression des petites répétitions)
        from report_fixer import post_process_html  # import local pour éviter cycles si besoin
        html_content = post_process_html(html_content)

        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(html_content)
       
        print(f"✅ Rapport HTML généré: {chemin_fichier}")
        return str(chemin_fichier)
    
    def _calculer_statistiques_sans_scores(self, entreprises: List[Dict]) -> Dict:
        """✅ Stats globales corrigées : 'actives' = au moins UNE thématique trouvée
        (on ne dépend plus uniquement d'un seuil de score_global)."""
        def est_active(e: Dict) -> bool:
            res = e.get('analyse_thematique', {})
            return any(v.get('trouve', False) for v in res.values())

        nb_total = len(entreprises)
        entreprises_actives = [e for e in entreprises if est_active(e)]

        stats = {
            'nb_total': nb_total,
            'nb_actives': len(entreprises_actives),
            'pourcentage_actives': round((len(entreprises_actives) / nb_total) * 100, 1) if nb_total else 0.0,
            'nb_communes': len({(e.get('commune') or '').strip() for e in entreprises if (e.get('commune') or '').strip()}),
            'thematiques_stats': {}
        }

        for thematique in self.thematiques:
            nb_entreprises = sum(
                1 for e in entreprises
                if e.get('analyse_thematique', {}).get(thematique, {}).get('trouve', False)
            )
            stats['thematiques_stats'][thematique] = {
                'count': nb_entreprises,
                'percentage': round((nb_entreprises / nb_total) * 100, 1) if nb_total else 0.0
            }

        return stats
    
    def _calcul_stats_globales(self, entreprises_enrichies: list) -> dict:
        # Unicité par SIRET si dispo, sinon (nom, commune)
        def _key(e):
            siret = str(e.get('siret') or e.get('SIRET') or '').strip()
            if siret:
                return ('SIRET', siret)
            return ('NC', (e.get('nom') or '').strip().lower(), (e.get('commune') or '').strip().lower())

        uniques = {}
        for e in entreprises_enrichies:
            uniques[_key(e)] = e
        uniq_list = list(uniques.values())

        actives = [e for e in uniq_list if self._est_active(e)]

        return {
            'total_entreprises': len(uniq_list),
            'entreprises_actives': len(actives),
            'taux_activite': round(100.0 * len(actives) / len(uniq_list), 1) if uniq_list else 0.0,
            'communes_uniques': len({(e.get('commune') or '').strip().lower() for e in uniq_list if (e.get('commune') or '').strip()})
        }

        
    def _generer_html_template_sans_scores(self, entreprises: List[Dict], stats: Dict) -> str:
        """✅ Template HTML amélioré avec résumé IA, résumé par commune au début et graphique camembert"""
        
        # Génération du résumé IA de la page
        resume_ia = self._generer_resume_ia_global(entreprises, stats)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport de Veille Économique</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                
                .resume-ia {{ background: linear-gradient(135deg, #e8f5e8, #f0f8f0); border-left: 5px solid #27ae60; margin: 20px; padding: 20px; border-radius: 8px; }}
                .resume-ia h2 {{ color: #27ae60; margin-top: 0; display: flex; align-items: center; }}
                .resume-ia h2::before {{ content: "🤖"; margin-right: 10px; }}
                .resume-points {{ list-style: none; padding: 0; }}
                .resume-points li {{ padding: 8px 0; border-bottom: 1px solid #e0e0e0; }}
                .resume-points li:last-child {{ border-bottom: none; }}
                .resume-points li::before {{ content: "▶"; color: #27ae60; margin-right: 10px; font-weight: bold; }}
                
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px; }}
                .stat-box {{ background: linear-gradient(135deg, #ecf0f1, #ffffff); padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat-box h3 {{ margin: 0; font-size: 2em; color: #2c3e50; }}
                .stat-box p {{ margin: 5px 0 0 0; color: #7f8c8d; font-weight: 500; }}
                
                .section {{ margin: 20px; }}
                .section h2 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; display: flex; align-items: center; }}
                .section h2::before {{ margin-right: 10px; font-size: 1.2em; }}
                
                .communes-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }}
                .commune-card {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                .commune-card h4 {{ margin: 0 0 15px 0; color: #2c3e50; font-size: 1.3em; }}
                .commune-stats {{ display: flex; justify-content: space-between; margin-bottom: 15px; }}
                .commune-stat {{ text-align: center; }}
                .commune-stat .number {{ font-size: 1.5em; font-weight: bold; color: #3498db; }}
                .commune-stat .label {{ font-size: 0.9em; color: #7f8c8d; }}
                
                .chart-container {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                .chart-wrapper {{ position: relative; height: 400px; }}
                
                .entreprise {{ margin: 20px 0; padding: 25px; background: white; border: 1px solid #e0e0e0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                .entreprise h4 {{ color: #2c3e50; margin: 0 0 15px 0; font-size: 1.4em; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
                .entreprise-info {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; background: #f8f9fa; padding: 15px; border-radius: 6px; }}
                .info-item {{ display: flex; flex-direction: column; }}
                .info-label {{ font-weight: bold; color: #34495e; font-size: 0.9em; }}
                .info-value {{ color: #2c3e50; margin-top: 5px; }}
                
                .activites {{ margin: 15px 0; }}
                .activites-list {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
                .activite-tag {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 6px 12px; border-radius: 20px; font-size: 0.9em; font-weight: 500; }}
                
                .details-thematiques {{ margin-top: 25px; }}
                .thematique-detail {{ margin: 15px 0; padding: 20px; background: #f8f9fa; border-left: 4px solid #3498db; border-radius: 0 6px 6px 0; }}
                .thematique-detail h5 {{ color: #2c3e50; margin: 0 0 15px 0; font-size: 1.1em; }}
                .detail-item {{ margin: 10px 0; padding: 12px; background: white; border-radius: 6px; border: 1px solid #e9ecef; }}
                .detail-title {{ font-weight: bold; color: #34495e; margin-bottom: 8px; }}
                .detail-content {{ color: #2c3e50; line-height: 1.5; }}
                .detail-source {{ margin-top: 8px; }}
                .detail-source a {{ color: #3498db; text-decoration: none; font-size: 0.9em; }}
                .detail-source a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏢 Rapport de Veille Économique Territoriale</h1>
                    <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
                </div>
                
                <!-- NOUVEAU: Résumé IA Global -->
                <div class="resume-ia">
                    <h2>Résumé Intelligent de l'Analyse</h2>
                    {resume_ia}
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
                
                <!-- NOUVEAU: Résumé par commune AU DÉBUT -->
                <div class="section">
                    <h2>🏘️ Résumé par Commune</h2>
                    {self._generer_section_communes_sans_scores(entreprises)}
                </div>
                
                <!-- MODIFIÉ: Synthèse par thématique avec graphique -->
                <div class="section">
                    <h2>📊 Synthèse par Thématique</h2>
                    <div class="chart-container">
                        <h3 style="text-align: center; margin-bottom: 20px;">Répartition des Activités par Thématique</h3>
                        <div class="chart-wrapper">
                            <canvas id="thematiquesChart"></canvas>
                        </div>
                    </div>
                    {self._generer_section_thematiques_detaillee_sans_scores(entreprises, stats)}
                </div>
                
                <!-- Détail des entreprises (existant, gardé à la fin) -->
                <div class="section">
                    <h2>📋 Détail des Entreprises</h2>
                    {self._generer_section_entreprises_sans_scores(entreprises)}
                </div>
            </div>
            
            <!-- Script pour le graphique camembert -->
            <script>
                const ctx = document.getElementById('thematiquesChart').getContext('2d');
                const thematiquesData = {json.dumps(self._generer_donnees_camembert(stats))};
                
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: thematiquesData.labels,
                        datasets: [{{
                            data: thematiquesData.values,
                            backgroundColor: [
                                '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
                                '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
                            ],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'right',
                                labels: {{
                                    usePointStyle: true,
                                    padding: 20,
                                    font: {{
                                        size: 14
                                    }}
                                }}
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((context.parsed * 100) / total).toFixed(1);
                                        return context.label + ': ' + context.parsed + ' entreprises (' + percentage + '%)';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
        return html

    def _generer_resume_ia_global(self, entreprises: List[Dict], stats: Dict) -> str:
        """Génère un résumé intelligent de toute l'analyse"""
        
        # Collecte des informations clés
        entreprises_actives = [e for e in entreprises if e.get('score_global', 0) > 0.1]
        
        # Analyse des thématiques dominantes
        thematiques_count = {}
        for entreprise in entreprises_actives:
            for thematique in entreprise.get('thematiques_principales', []):
                thematiques_count[thematique] = thematiques_count.get(thematique, 0) + 1
        
        thematiques_top = sorted(thematiques_count.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Analyse géographique
        communes_actives = {}
        for entreprise in entreprises_actives:
            commune = entreprise.get('commune', 'Inconnue')
            communes_actives[commune] = communes_actives.get(commune, 0) + 1
        
        commune_plus_active = max(communes_actives.items(), key=lambda x: x[1]) if communes_actives else ("Aucune", 0)
        
        # Génération des points de résumé
        points_resume = []
        
        # Point 1: Vue d'ensemble
        if stats['pourcentage_actives'] > 70:
            points_resume.append(f"<strong>Territoire très dynamique</strong> : {stats['pourcentage_actives']}% des entreprises analysées présentent une activité détectable, soit {stats['nb_actives']} sur {stats['nb_total']} entreprises.")
        elif stats['pourcentage_actives'] > 40:
            points_resume.append(f"<strong>Activité modérée</strong> : {stats['pourcentage_actives']}% des entreprises montrent des signes d'activité ({stats['nb_actives']} sur {stats['nb_total']}), avec des opportunités d'amélioration.")
        else:
            points_resume.append(f"<strong>Territoire à potentiel</strong> : {stats['pourcentage_actives']}% d'activité détectée ({stats['nb_actives']} entreprises), nécessitant une approche ciblée pour stimuler le dynamisme économique.")
        
        # Point 2: Thématiques dominantes
        if thematiques_top:
            thematiques_str = ", ".join([f"{t[0].replace('_', ' ').title()} ({t[1]} entreprises)" for t in thematiques_top])
            points_resume.append(f"<strong>Secteurs d'activité prioritaires</strong> : {thematiques_str}. Ces domaines concentrent la majorité de l'activité économique détectée.")
        
        # Point 3: Répartition géographique
        if commune_plus_active[1] > 0:
            points_resume.append(f"<strong>Pôle économique principal</strong> : {commune_plus_active[0]} se distingue avec {commune_plus_active[1]} entreprises actives, représentant un centre névralgique du territoire.")
        
        # Point 4: Recommandations
        if stats['pourcentage_actives'] > 60:
            points_resume.append("<strong>Opportunités identifiées</strong> : Le territoire présente un bon dynamisme. Focus recommandé sur l'accompagnement des entreprises moins visibles et le renforcement des synergies entre secteurs.")
        else:
            points_resume.append("<strong>Axes de développement</strong> : Potentiel d'amélioration significatif. Recommandations : renforcement de la communication des entreprises, développement de l'écosystème local et accompagnement ciblé.")
        
        # Formatage HTML
        html_resume = '<ul class="resume-points">'
        for point in points_resume:
            html_resume += f'<li>{point}</li>'
        html_resume += '</ul>'
        
        return html_resume

    def _generer_donnees_camembert(self, stats: Dict) -> Dict:
        """Génère les données pour le graphique camembert"""
        
        # Extraction des données thématiques
        thematiques_data = stats.get('thematiques_stats', {})
        
        # Tri par nombre d'entreprises
        thematiques_triees = sorted(
            thematiques_data.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        # Filtrage des thématiques avec au moins 1 entreprise
        thematiques_actives = [(nom, data) for nom, data in thematiques_triees if data['count'] > 0]
        
        if not thematiques_actives:
            return {'labels': ['Aucune activité'], 'values': [1]}
        
        # Préparation des données pour Chart.js
        labels = [nom.replace('_', ' ').title() for nom, _ in thematiques_actives]
        values = [data['count'] for _, data in thematiques_actives]
        
        return {
            'labels': labels,
            'values': values
        }

    def _generer_section_thematiques_detaillee_sans_scores(self, entreprises: List[Dict], stats: Dict) -> str:
        """Génère une section thématiques détaillée sous le graphique"""
        
        html = '<div style="margin-top: 30px;">'
        
        thematiques_stats = stats.get('thematiques_stats', {})
        thematiques_triees = sorted(
            thematiques_stats.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        for thematique, data in thematiques_triees:
            if data['count'] > 0:
                entreprises_thematique = [
                    e for e in entreprises 
                    if e.get('analyse_thematique', {}).get(thematique, {}).get('trouve', False)
                ][:3]  # Top 3
                
                html += f'''
                <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3498db;">
                    <h4 style="margin: 0 0 15px 0; color: #2c3e50;">
                        {thematique.replace('_', ' ').title()} 
                        <span style="color: #7f8c8d; font-weight: normal;">({data['count']} entreprises)</span>
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                '''
                
                for entreprise in entreprises_thematique:
                    html += f'''
                    <div style="background: white; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef;">
                        <div style="font-weight: bold; color: #2c3e50;">{entreprise['nom']}</div>
                        <div style="color: #7f8c8d; font-size: 0.9em; margin-top: 5px;">{entreprise['commune']}</div>
                    </div>
                    '''
                
                html += '</div></div>'
        
        html += '</div>'
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
        """✅ Section communes améliorée avec cartes visuelles"""
        communes_data = {}
        
        # Seulement les entreprises avec activité
        entreprises_actives = [e for e in entreprises if e.get('score_global', 0) > 0.1]
        
        for entreprise in entreprises_actives:
            commune = entreprise.get('commune', 'Inconnue')
            if commune not in communes_data:
                communes_data[commune] = {
                    'entreprises': [],
                    'thematiques': set(),
                    'secteurs': set()
                }
            
            communes_data[commune]['entreprises'].append(entreprise)
            
            # Collecte des thématiques
            thematiques_entreprise = entreprise.get('thematiques_principales', [])
            communes_data[commune]['thematiques'].update(thematiques_entreprise)
            
            # Collecte des secteurs (simplifié)
            secteur = entreprise.get('secteur_naf', '')
            if secteur:
                secteur_simplifie = secteur.split()[0] if secteur else 'Autre'
                communes_data[commune]['secteurs'].add(secteur_simplifie)
        
        # Tri des communes par nombre d'entreprises actives
        communes_triees = sorted(communes_data.items(), key=lambda x: len(x[1]['entreprises']), reverse=True)
        
        html = '<div class="communes-grid">'
        
        for commune, data in communes_triees:
            nb_entreprises = len(data['entreprises'])
            nb_thematiques = len(data['thematiques'])
            nb_secteurs = len(data['secteurs'])
            
            # Entreprises exemple (top 3)
            entreprises_exemple = [e['nom'] for e in data['entreprises'][:3]]
            
            # Thématiques principales
            thematiques_liste = list(data['thematiques'])[:3]
            thematiques_affichage = ', '.join([t.replace('_', ' ').title() for t in thematiques_liste])
            
            html += f'''
            <div class="commune-card">
                <h4>📍 {commune}</h4>
                
                <div class="commune-stats">
                    <div class="commune-stat">
                        <div class="number">{nb_entreprises}</div>
                        <div class="label">Entreprises</div>
                    </div>
                    <div class="commune-stat">
                        <div class="number">{nb_thematiques}</div>
                        <div class="label">Thématiques</div>
                    </div>
                    <div class="commune-stat">
                        <div class="number">{nb_secteurs}</div>
                        <div class="label">Secteurs</div>
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <div style="font-weight: bold; color: #34495e; margin-bottom: 8px;">🏢 Entreprises actives :</div>
                    <div style="font-size: 0.9em; color: #2c3e50; line-height: 1.4;">
                        {', '.join(entreprises_exemple)}
                        {f' et {nb_entreprises - 3} autres...' if nb_entreprises > 3 else ''}
                    </div>
                </div>
                
                {f'''
                <div>
                    <div style="font-weight: bold; color: #34495e; margin-bottom: 8px;">🎯 Activités principales :</div>
                    <div style="font-size: 0.9em; color: #2c3e50;">
                        {thematiques_affichage}
                    </div>
                </div>
                ''' if thematiques_affichage else ''}
            </div>
            '''
        
        html += '</div>'
        
        if not communes_triees:
            html = '<div style="text-align: center; padding: 40px; color: #7f8c8d;">Aucune commune avec activité détectée</div>'
        
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
    
    # --- AJOUT UTILITAIRES SIREN/SIRET ---
    def _key_siren(self, ent):
        return (ent.get('siren') or '').strip()

    def group_by_siren(self, entreprises):
        """Retourne dict {siren: [entreprises (établissements)]} en ignorant siren vide."""
        from collections import defaultdict
        g = defaultdict(list)
        for e in entreprises:
            siren = self._key_siren(e)
            if siren:
                g[siren].append(e)
        return g

    def entreprise_label_unite_legale(self, siren, etablissements):
        """Libellé 'Entreprise (SIREN) - Nom principal', agrège le 'meilleur' nom."""
        noms = [e.get('nom') or e.get('enseigne') or '' for e in etablissements]
        nom = max(noms, key=len) if noms else f"SIREN {siren}"
        return f"{nom} — SIREN {siren}"

    def _est_active(self, ent: dict) -> bool:
        at = ent.get('analyse_thematique', {})
        return any(v.get('trouve') for v in at.values())

    def _synthese_par_thematique(self, entreprises_enrichies: list) -> dict:
        # clé d’unicité
        def _key(e):
            siret = str(e.get('siret') or e.get('SIRET') or '').strip()
            if siret:
                return ('SIRET', siret)
            return ('NC', (e.get('nom') or '').strip().lower(), (e.get('commune') or '').strip().lower())

        # uniques
        uniques = {}
        for e in entreprises_enrichies:
            uniques[_key(e)] = e
        uniq_list = list(uniques.values())

        out = {}  # thematique -> {'nb': int, 'entreprises': [(nom, commune)]}
        for e in uniq_list:
            at = e.get('analyse_thematique', {})
            for th, v in (at or {}).items():
                if v.get('trouve'):
                    out.setdefault(th, {'set': set(), 'entreprises': []})
                    k = ( (e.get('nom') or '').strip(), (e.get('commune') or '').strip() )
                    if k not in out[th]['set']:
                        out[th]['set'].add(k)
                        out[th]['entreprises'].append(k)

        # convertir en comptages
        for th, d in out.items():
            d['nb'] = len(d['entreprises'])
            d.pop('set', None)

        return out

    def _resume_par_commune(self, entreprises_enrichies: list) -> dict:
        # Regroupement par commune
        communes = {}
        for e in entreprises_enrichies:
            com = (e.get('commune') or '').strip()
            if not com:
                continue
            communes.setdefault(com, []).append(e)

        resume = {}
        for com, ents in communes.items():
            # dé-dup par SIRET puis par nom normalisé
            seen = set()
            uniques = []
            for e in ents:
                siret = str(e.get('siret') or e.get('SIRET') or '').strip()
                nom = (e.get('nom') or '').strip().lower()
                key = ('SIRET', siret) if siret else ('NOM', nom)
                if key in seen:
                    continue
                seen.add(key)
                uniques.append(e)

            # thematiques dominantes (sur uniques)
            from collections import Counter
            c = Counter()
            for e in uniques:
                at = e.get('analyse_thematique', {})
                for th, v in (at or {}).items():
                    if v.get('trouve'):
                        c[th] += 1

            resume[com] = {
                'nb_entreprises': len(uniques),
                'entreprises': [( (e.get('nom') or '').strip(), (e.get('commune') or '').strip() ) for e in uniques],
                'thematiques_dominantes': [t for t,_ in c.most_common(3)]
            }

        return resume
