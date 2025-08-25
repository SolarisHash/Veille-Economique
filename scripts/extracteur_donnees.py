#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'extraction et de préparation des données entreprises
"""

import pandas as pd
import re
import random
from typing import List, Dict, Optional

from scripts.filtreur_pme import FiltreurPME


class ExtracteurDonnees:
    """Extraction et nettoyage des données entreprises du fichier Excel"""
    
    def __init__(self, fichier_excel: str):
        """Initialisation avec le fichier Excel"""
        self.fichier_excel = fichier_excel
        self.colonnes_requises = [
            'SIRET', 'Nom courant/Dénomination', 'Enseigne', 
            'Adresse - complément dʼadresse', 'Adresse - numéro et voie',
            'Adresse - distribution postale', 'Adresse - CP et commune',
            'Commune', 'Code NAF', 'Libellé NAF', 'Genre', 'Nom', 
            'Prénom', 'Site Web établissement', 
            # 'Dirigeant'
        ]
        self.df = None
        
    def charger_donnees(self) -> pd.DataFrame:
        """Chargement du fichier Excel"""
        try:
            self.df = pd.read_excel(self.fichier_excel, sheet_name=0)
            print(f"📊 Fichier chargé: {len(self.df)} lignes")
            return self.df
        except Exception as e:
            raise Exception(f"Erreur chargement fichier: {str(e)}")
            
    def valider_structure(self) -> bool:
        """Validation de la structure du fichier"""
        if self.df is None:
            self.charger_donnees()
    
        print("📋 Colonnes trouvées dans le fichier:")
        for col in self.df.columns:
            print(f"   - '{col}'")

        colonnes_presentes = set(self.df.columns)
        colonnes_manquantes = set(self.colonnes_requises) - colonnes_presentes
        
        if colonnes_manquantes:
            print(f"⚠️  Colonnes manquantes: {colonnes_manquantes}")
            
            # Tentative de mapping automatique pour les apostrophes
            colonnes_mappees = {}
            for col_manquante in colonnes_manquantes:
                for col_presente in colonnes_presentes:
                    # Normalisation des apostrophes pour comparaison
                    col_manquante_norm = col_manquante.replace('ʼ', "'").replace(''', "'").replace('`', "'")
                    col_presente_norm = col_presente.replace('ʼ', "'").replace(''', "'").replace('`', "'")
                    if col_manquante_norm == col_presente_norm:
                        colonnes_mappees[col_manquante] = col_presente
                        print(f"✅ Mapping trouvé: '{col_manquante}' -> '{col_presente}'")
    
            # Mise à jour de la liste des colonnes requises
            for ancien, nouveau in colonnes_mappees.items():
                index = self.colonnes_requises.index(ancien)
                self.colonnes_requises[index] = nouveau
            
            # Nouvelle vérification
            colonnes_manquantes = set(self.colonnes_requises) - colonnes_presentes
            
            if colonnes_manquantes:
                print(f"❌ Colonnes toujours manquantes: {colonnes_manquantes}")
                return False
                
        print("✅ Structure du fichier validée")
        return True
        
    def nettoyer_donnees(self) -> pd.DataFrame:
        """Nettoyage des données avec gestion des NaN"""
        if not self.valider_structure():
            raise Exception("Structure du fichier invalide")
            
        # Suppression des lignes vides
        self.df = self.df.dropna(subset=['SIRET', 'Nom courant/Dénomination'])
        
        # Nettoyage des champs texte
        self.df['nom_normalise'] = self.df['Nom courant/Dénomination'].apply(self._nettoyer_nom)
        self.df['enseigne_normalise'] = self.df['Enseigne'].apply(self._nettoyer_nom)
        self.df['commune_normalise'] = self.df['Commune'].apply(self._nettoyer_commune)
        
        # Validation SIRET
        self.df['siret_valide'] = self.df['SIRET'].apply(self._valider_siret)
        
        # Nettoyage site web
        self.df['site_web_propre'] = self.df['Site Web établissement'].apply(self._nettoyer_url)
        
        # Remplacez les colonnes textuelles contenant des NaN
        colonnes_texte = ['nom', 'commune', 'secteur_naf', 'site_web']
        for col in colonnes_texte:
            if col in self.df.columns:
                # Remplacer NaN par chaîne vide et s'assurer que c'est du texte
                self.df[col] = self.df[col].fillna('').astype(str)
    
        print(f"🧹 Données nettoyées: {len(self.df)} entreprises valides")
        return self.df
        
    def _nettoyer_nom(self, nom: str) -> str:
        """Nettoyage d'un nom d'entreprise"""
        if pd.isna(nom):
            return ""
        
        # Suppression caractères spéciaux, espaces multiples
        nom_propre = re.sub(r'[^\w\s&.-]', '', str(nom))
        nom_propre = re.sub(r'\s+', ' ', nom_propre).strip()
        
        return nom_propre
        
    def _nettoyer_commune(self, commune: str) -> str:
        """Nettoyage nom de commune"""
        if pd.isna(commune):
            return ""
            
        # Suppression codes postaux et caractères spéciaux
        commune_propre = re.sub(r'^\d{5}\s*', '', str(commune))
        commune_propre = re.sub(r'[^\w\s-]', '', commune_propre)
        commune_propre = commune_propre.strip().title()
        
        return commune_propre
        
    def _valider_siret(self, siret: str) -> bool:
        """Validation basique du SIRET"""
        if pd.isna(siret):
            return False
            
        siret_str = str(siret).replace(' ', '')
        return len(siret_str) == 14 and siret_str.isdigit()
        
    def _nettoyer_url(self, url: str) -> str:
        """Nettoyage et validation URL"""
        if pd.isna(url):
            return ""
            
        url_str = str(url).strip()
        
        # Ajout https:// si manquant
        if url_str and not url_str.startswith(('http://', 'https://')):
            url_str = 'https://' + url_str
            
        return url_str

    def extraire_echantillon(self, nb_entreprises: int = 10) -> List[Dict]:
        """Version robuste avec filtrage PME/territoire non bloquant."""
        donnees_propres = self.nettoyer_donnees()

        # Filtrage standard
        entreprises_completes = donnees_propres[
            (donnees_propres['siret_valide'] == True) &
            (donnees_propres['nom_normalise'] != "") &
            (~donnees_propres['nom_normalise'].str.contains('NON-DIFFUSIBLE', case=False, na=False))
        ]

        # Essayer d'importer le filtreur PME – si absent, continuer sans bloquer
        filtreur = None
        try:
            from scripts.filtreur_pme import FiltreurPME
            filtreur = FiltreurPME()
        except Exception as e:
            print(f"⚠️  FiltreurPME indisponible ({e}) → poursuite sans filtre spécifique")

        # Conversion en liste de dicts
        entreprises_list = []
        for _, row in entreprises_completes.iterrows():
            entreprise = {
                'siret': row['SIRET'],
                'nom': row['nom_normalise'],
                'enseigne': row['enseigne_normalise'],
                'commune': row['commune_normalise'],
                'adresse_complete': self._construire_adresse(row),
                'secteur_naf': row['Libellé NAF'],
                'code_naf': row['Code NAF'],
                'dirigeant': self._construire_dirigeant(row),
                'site_web': row['site_web_propre'],
                'donnees_brutes': row.to_dict()
            }
            entreprises_list.append(entreprise)

        entreprises_filtrees = entreprises_list

        # Filtrage territoire + PME si disponible
        if filtreur is not None:
            try:
                entreprises_territoire = filtreur.filtrer_par_territoire(entreprises_list)
                pme_recherchables = filtreur.filtrer_pme_recherchables(entreprises_territoire)

                # ✅ Fallback progressif si ça vide tout
                if len(pme_recherchables) > 0:
                    entreprises_filtrees = pme_recherchables
                elif len(entreprises_territoire) > 0:
                    print("⚠️  Filtre PME trop restrictif → fallback aux entreprises du territoire")
                    entreprises_filtrees = entreprises_territoire
                else:
                    print("⚠️  Filtre territoire vide → on garde la liste complète")
                    entreprises_filtrees = entreprises_list
            except Exception as e:
                print(f"⚠️  Erreur filtrage PME/territoire ({e}) → on garde la liste complète")

        # Sélection finale
        entreprises_finales = entreprises_filtrees[:nb_entreprises]

        print("📊 Total → Territoire → PME → Final")
        if filtreur is not None:
            try:
                print(f"📊 {len(entreprises_list)} → "
                    f"{len(entreprises_territoire)} → "
                    f"{len(pme_recherchables)} → "
                    f"{len(entreprises_finales)}")
            except:
                print(f"📊 {len(entreprises_list)} → ? → ? → {len(entreprises_finales)}")
        else:
            print(f"📊 {len(entreprises_list)} → (pas de filtre) → {len(entreprises_finales)}")

        return entreprises_finales


    def _selection_stratifiee(self, df: pd.DataFrame, nb_total: int) -> pd.DataFrame:
        """Sélection stratifiée par commune pour représentativité"""
        communes = df['commune_normalise'].value_counts()
        
        # Calcul du nombre d'entreprises par commune
        echantillon_final = []
        
        for commune, count in communes.items():
            nb_commune = max(1, int(nb_total * count / len(df)))
            echantillon_commune = df[df['commune_normalise'] == commune].sample(
                min(nb_commune, count), random_state=42
            )
            echantillon_final.append(echantillon_commune)
            
        # Fusion et limitation au nombre demandé
        resultat = pd.concat(echantillon_final).sample(
            min(nb_total, len(pd.concat(echantillon_final))), 
            random_state=42
        )
        
        return resultat
        
    def _construire_adresse(self, row: pd.Series) -> str:
        """Construction de l'adresse complète"""
        elements = [
            row.get('Adresse - numéro et voie', ''),
            row.get('Adresse - complément dʼadresse', ''),
            row.get('Adresse - distribution postale', ''),
            row.get('Adresse - CP et commune', '')
        ]
        
        adresse = ', '.join([str(elem).strip() for elem in elements if pd.notna(elem) and str(elem).strip()])
        return adresse
        
    def _construire_dirigeant(self, row: pd.Series) -> str:
        """Construction du nom du dirigeant"""
        if pd.notna(row.get('Dirigeant')):
            return str(row['Dirigeant'])
            
        # Reconstruction à partir des champs séparés
        nom = row.get('Nom', '')
        prenom = row.get('Prénom', '')
        
        if pd.notna(prenom) and pd.notna(nom):
            return f"{prenom} {nom}".strip()
            
        return ""
        
    def obtenir_statistiques(self) -> Dict:
        """Statistiques sur les données"""
        if self.df is None:
            self.charger_donnees()
            
        stats = {
            'total_entreprises': len(self.df),
            'entreprises_avec_siret': len(self.df[self.df['SIRET'].notna()]),
            'entreprises_avec_site': len(self.df[self.df['Site Web établissement'].notna()]),
            'communes_uniques': self.df['Commune'].nunique(),
            'secteurs_naf': self.df['Libellé NAF'].nunique()
        }
        
        return stats