from typing import Dict, List


class FiltreurPME:
    """Filtrage spécifique pour identifier les vraies PME de votre territoire"""
    
    def __init__(self, config_path="config/parametres.yaml"):
        self.config = self._charger_config_territoire(config_path)
        
    def _charger_config_territoire(self, config_path):
        """Chargement des codes postaux et critères PME"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except:
            # Configuration par défaut si fichier manquant
            return {
                'territoire': {
                    'codes_postaux_cibles': ['77600', '77700'],
                    'communes_prioritaires': ['Bussy-Saint-Georges']
                },
                'filtrage_pme': {
                    'effectif_max': 249,
                    'secteurs_prioritaires': ['commerce', 'services']
                }
            }
    
    def filtrer_par_territoire(self, entreprises: List[Dict]) -> List[Dict]:
        """🎯 Filtrage par codes postaux de votre territoire"""
        
        codes_postaux_cibles = self.config.get('territoire', {}).get('codes_postaux_cibles', [])
        communes_prioritaires = self.config.get('territoire', {}).get('communes_prioritaires', [])
        
        print(f"🎯 FILTRAGE TERRITORIAL:")
        print(f"   📮 Codes postaux cibles: {codes_postaux_cibles}")
        print(f"   🏘️  Communes prioritaires: {communes_prioritaires}")
        
        entreprises_territoire = []
        
        for entreprise in entreprises:
            adresse = entreprise.get('adresse_complete', '')
            commune = entreprise.get('commune', '')
            
            # Extraction du code postal de l'adresse
            code_postal_trouve = self._extraire_code_postal(adresse)
            
            est_dans_territoire = False
            raison_selection = ""
            
            # Vérification code postal
            if code_postal_trouve in codes_postaux_cibles:
                est_dans_territoire = True
                raison_selection = f"Code postal {code_postal_trouve}"
                entreprise['code_postal_detecte'] = code_postal_trouve
                
            # Vérification commune
            elif commune in communes_prioritaires:
                est_dans_territoire = True
                raison_selection = f"Commune {commune}"
                
            # Vérification proximité (codes postaux proches)
            elif self._est_code_postal_proche(code_postal_trouve, codes_postaux_cibles):
                est_dans_territoire = True
                raison_selection = f"Proximité {code_postal_trouve}"
                entreprise['code_postal_detecte'] = code_postal_trouve
            
            if est_dans_territoire:
                entreprise['raison_selection_territoire'] = raison_selection
                entreprises_territoire.append(entreprise)
                print(f"   ✅ {entreprise['nom'][:30]} - {raison_selection}")
            else:
                print(f"   ❌ {entreprise['nom'][:30]} - Hors territoire")
        
        print(f"\n📊 Résultat filtrage territorial: {len(entreprises_territoire)}/{len(entreprises)} entreprises")
        return entreprises_territoire
    
    def _extraire_code_postal(self, adresse: str) -> str:
        """Extraction du code postal depuis l'adresse"""
        import re
        
        # Recherche pattern code postal français (5 chiffres)
        match = re.search(r'\b(\d{5})\b', adresse)
        return match.group(1) if match else ""
    
    def _est_code_postal_proche(self, code_postal: str, codes_cibles: List[str]) -> bool:
        """Vérification si code postal est proche géographiquement"""
        if not code_postal or len(code_postal) != 5:
            return False
            
        for code_cible in codes_cibles:
            if len(code_cible) == 5:
                # Codes postaux proches = même département + proche numériquement
                if (code_postal[:2] == code_cible[:2] and  # Même département
                    abs(int(code_postal) - int(code_cible)) <= 100):  # Proximité numérique
                    return True
        return False
    
    def filtrer_pme_recherchables(self, entreprises: List[Dict]) -> List[Dict]:
        """Filtrage des PME recherchables avec vérification des types"""
        pme_valides = []
        
        for entreprise in entreprises:
            try:
                # Vérification sécurisée du nom
                nom = entreprise.get('nom', '')
                if not isinstance(nom, str):
                    nom = str(nom) if nom is not None else ''
                
                nom = nom.strip().upper()
                
                # Vérification des exclusions
                exclusions = ['MADAME', 'MONSIEUR', 'M.', 'MME']
                if any(nom.startswith(excl) for excl in exclusions):
                    continue
                    
                pme_valides.append(entreprise)
                
            except Exception as e:
                print(f"❌ Erreur filtrage PME: {e}")
                continue
        
        return pme_valides
    
    def _est_nom_commercial(self, nom: str) -> bool:
        """Détection nom commercial vs administratif"""
        # Noms commerciaux = plus recherchables sur le web
        mots_commerciaux = [
            'BOULANGERIE', 'RESTAURANT', 'CAFE', 'HOTEL', 'GARAGE',
            'COIFFURE', 'PHARMACIE', 'OPTIQUE', 'MAGASIN', 'BOUTIQUE',
            'CENTRE', 'INSTITUT', 'STUDIO', 'ATELIER', 'MAISON'
        ]
        
        return any(mot in nom for mot in mots_commerciaux)