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
        """Version ÉQUILIBRÉE - Élimine seulement les cas vraiment non recherchables"""
        
        entreprises_recherchables = []
        
        # ❌ EXCLUSIONS STRICTES (vraiment non recherchables)
        exclusions_strictes = [
            # Personnes physiques évidentes
            'MADAME ', 'MONSIEUR ', 'M. ', 'MME ', 'MLLE ',
            
            # Informations non diffusibles
            'INFORMATION NON-DIFFUSIBLE', 'NON DIFFUSIBLE', 'CONFIDENTIEL',
            
            # Organismes sans activité web
            'BIBLIOTHEQUE NATIONALE DE FRANCE',  # Très spécifique
            'CENTRE TECHNIQUE DU LIVRE',  # Très spécifique
        ]
        
        # ✅ ORGANISATIONS À GARDER (ont une activité économique/communication)
        organisations_actives = [
            'SYNDICAT', 'INTERCOMMUNAL', 'MIXTE',  # Projets, développements
            'AGENCE', 'OFFICE',  # Recrutements, événements
            'CENTRE HOSPITALIER',  # Recrutements massifs
            'FRANCE TRAVAIL',  # Actualités emploi
            'ETABLISSEMENT PUBLIC'  # Projets, innovations
        ]
        
        stats = {'total': len(entreprises), 'exclus': 0, 'gardes': 0}
        
        for entreprise in entreprises:
            try:
                nom = entreprise.get('nom', '')
                if not isinstance(nom, str):
                    nom = str(nom) if nom is not None else ''
                
                nom = nom.strip().upper()
                
                # ❌ TEST 1: Exclusions strictes seulement
                est_non_recherchable = any(exclusion in nom for exclusion in exclusions_strictes)
                
                if est_non_recherchable:
                    stats['exclus'] += 1
                    print(f"❌ Non recherchable: {nom[:50]}...")
                    continue
                
                # ❌ TEST 2: Noms trop courts ou vides
                if len(nom) < 3:
                    stats['exclus'] += 1
                    print(f"❌ Nom trop court: {nom}")
                    continue
                
                # ❌ TEST 3: Personnes physiques (test plus fin)
                if self._est_personne_physique_stricte(nom):
                    stats['exclus'] += 1
                    print(f"❌ Personne physique: {nom[:50]}...")
                    continue
                
                # ✅ VALIDATION: Toutes les autres organisations sont gardées
                entreprises_recherchables.append(entreprise)
                stats['gardes'] += 1
                
                # Classification pour information
                if any(org in nom for org in organisations_actives):
                    print(f"✅ Organisation active gardée: {nom[:50]}...")
                else:
                    print(f"✅ Entreprise gardée: {nom[:50]}...")
                
            except Exception as e:
                print(f"❌ Erreur filtrage: {e}")
                stats['exclus'] += 1
                continue
        
        # Statistiques finales
        print(f"\n📊 FILTRAGE RECHERCHABLE ÉQUILIBRÉ:")
        print(f"   📋 Total analysé: {stats['total']}")
        print(f"   ❌ Non recherchables exclus: {stats['exclus']}")
        print(f"   ✅ Entreprises/Organisations gardées: {stats['gardes']}")
        
        return entreprises_recherchables

    def _est_personne_physique_stricte(self, nom: str) -> bool:
        """Test strict pour personnes physiques uniquement"""
        
        # Civilités au début
        civilites = ['MADAME ', 'MONSIEUR ', 'M. ', 'MME ', 'MLLE ']
        
        for civilite in civilites:
            if nom.startswith(civilite):
                nom_apres = nom.replace(civilite, '').strip()
                mots = nom_apres.split()
                
                # Si seulement prénom + nom (max 2 mots) = personne physique
                if len(mots) <= 2:
                    return True
                
                # Si pas d'indicateur d'entreprise = personne physique
                indicateurs_entreprise = [
                    'SARL', 'SAS', 'SASU', 'EURL', 'SA', 'SNC',
                    'ENTREPRISE', 'SOCIETE', 'CABINET', 'ATELIER'
                ]
                
                if not any(indic in nom_apres for indic in indicateurs_entreprise):
                    return True
        
        return False

    def _est_nom_commercial(self, nom: str) -> bool:
        """Détection nom commercial vs administratif"""
        # Noms commerciaux = plus recherchables sur le web
        mots_commerciaux = [
            'BOULANGERIE', 'RESTAURANT', 'CAFE', 'HOTEL', 'GARAGE',
            'COIFFURE', 'PHARMACIE', 'OPTIQUE', 'MAGASIN', 'BOUTIQUE',
            'CENTRE', 'INSTITUT', 'STUDIO', 'ATELIER', 'MAISON'
        ]
        
        return any(mot in nom for mot in mots_commerciaux)
    
    def filtrer_organismes_publics(self, entreprises: List[Dict]) -> List[Dict]:
        """AJOUT SIMPLE : Élimine les organismes publics et parapublics"""
        
        # ❌ EXCLUSIONS des organismes publics
        exclusions_organismes_publics = [
            'FRANCE TRAVAIL', 'POLE EMPLOI', 'PREFECTURE', 'MAIRIE',
            'CONSEIL GENERAL', 'CONSEIL DEPARTEMENTAL', 'CONSEIL REGIONAL',
            'BIBLIOTHEQUE NATIONALE', 'CENTRE TECHNIQUE DU LIVRE',
            'CENTRE HOSPITALIER', 'HOPITAL', 'CLINIQUE PUBLIQUE',
            'SYNDICAT MIXTE', 'SYNDICAT INTERCOMMUNAL', 'COMMUNAUTE DE COMMUNES',
            'ETABLISSEMENT PUBLIC', 'REGIE MUNICIPALE', 'SEM ', 'SEMOP',
            'ASSOCIATION POUR', 'FONDATION POUR', 'FEDERATION',
            'UNION NATIONALE', 'COMITE DEPARTEMENTAL'
        ]
        
        entreprises_privees = []
        exclus = 0
        
        for entreprise in entreprises:
            nom = entreprise.get('nom', '').upper().strip()
            
            # Test d'exclusion
            est_organisme_public = any(exclusion in nom for exclusion in exclusions_organismes_publics)
            
            if not est_organisme_public:
                entreprises_privees.append(entreprise)
            else:
                exclus += 1
                print(f"❌ Organisme public exclu: {nom[:50]}...")
        
        print(f"🔄 Filtrage organismes publics: {exclus} exclus, {len(entreprises_privees)} entreprises privées gardées")

        return entreprises_privees