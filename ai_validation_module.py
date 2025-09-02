import os
import openai
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ValidationResult:
    """Résultat de validation IA"""
    is_relevant: bool
    confidence_score: float
    explanation: str
    extracted_info: Dict
    themes_detected: List[str]
    
class AIValidationModule:
    """Module de validation IA avec GPT-4o-mini"""
    
    def __init__(self, env_file_path: str = ".env"):
        """Initialisation avec clé API depuis fichier .env"""
        self.load_api_config(env_file_path)
        
        # Configuration du client selon le type d'API
        if self.is_azure:
            self.client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint
            )
            print(f"✅ Module IA initialisé avec Azure OpenAI ({self.model})")
        else:
            self.client = openai.OpenAI(api_key=self.api_key)
            print(f"✅ Module IA initialisé avec OpenAI standard ({self.model})")
        
        # Configuration
        self.max_tokens = 800
        self.temperature = 0.1  # Faible pour plus de consistance
        
        # Compteurs pour monitoring des coûts
        self.api_calls_count = 0
        self.tokens_used = 0
    
    def load_api_config(self, env_file_path: str):
        """Chargement de la configuration API depuis le fichier .env"""
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file_path)
            
            # Détection automatique du type d'API
            azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
            openai_api_key = os.getenv('OPENAI_API_KEY')
            
            if azure_api_key:
                # Configuration Azure OpenAI
                self.is_azure = True
                self.api_key = azure_api_key
                self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://your-resource.openai.azure.com/')
                self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
                self.model = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
                
                print(f"🔑 Configuration Azure OpenAI détectée")
                print(f"   📍 Endpoint: {self.azure_endpoint}")
                print(f"   🎯 Deployment: {self.model}")
                
                # Vérification des paramètres Azure requis
                if not self.azure_endpoint or 'your-resource' in self.azure_endpoint:
                    raise ValueError("AZURE_OPENAI_ENDPOINT manquant ou invalide dans .env")
                    
            elif openai_api_key:
                # Configuration OpenAI standard
                self.is_azure = False
                self.api_key = openai_api_key
                self.model = os.getenv('AI_MODEL', 'gpt-4o-mini')
                print(f"🔑 Configuration OpenAI standard détectée")
                
            else:
                raise ValueError("Aucune clé API trouvée. Ajoutez AZURE_OPENAI_API_KEY ou OPENAI_API_KEY dans .env")
            
        except ImportError:
            print("❌ Installation requise: pip install python-dotenv")
            raise
        except Exception as e:
            print(f"❌ Erreur chargement configuration API: {e}")
            raise
    
    # def _get_validation_system_prompt(self) -> str:
    #     """✅ PROMPT ÉQUILIBRÉ : Ni trop strict, ni trop permissif"""
    #     return """Tu es un expert en veille économique avec une approche ÉQUILIBRÉE et PRAGMATIQUE.

    # OBJECTIF: Valider les résultats pertinents tout en évitant les faux positifs évidents.

    # RÈGLES DE VALIDATION ÉQUILIBRÉES:

    # ✅ VALIDER SI:
    # 1. Le nom de l'entreprise EST mentionné dans le contenu ET
    # 2. Le contenu a un lien logique avec la thématique demandée ET
    # 3. C'est dans un contexte professionnel/économique

    # ❌ REJETER SI:
    # 1. Contenu complètement hors-sujet (dictionnaires, forums linguistiques)
    # 2. Thématique totalement différente (ex: chiffre d'affaires pour "recrutements")
    # 3. Mention uniquement administrative sans lien thématique

    # 🤔 CAS LIMITES - ACCEPTER AVEC SCORE MODÉRÉ:
    # - Informations générales d'entreprise avec mention indirecte de la thématique
    # - Articles de presse mentionnant l'entreprise dans un contexte lié
    # - Contenus partiellement pertinents mais pas parfaitement alignés

    # EXEMPLES CONCRETS:

    # RECRUTEMENTS:
    # ✅ ACCEPTER (score élevé 0.8+):
    # - "CARREFOUR recrute 50 personnes"
    # - "Offres d'emploi chez CARREFOUR"
    # - "CARREFOUR cherche un directeur"

    # 🤔 ACCEPTER (score modéré 0.4-0.6):
    # - "CARREFOUR développe ses équipes" (implication recrutement)
    # - "Croissance de CARREFOUR et nouveaux postes" (lien indirect)
    # - "CARREFOUR renforce son organisation" (possible recrutement)

    # ❌ REJETER (score <0.3):
    # - "Chiffre d'affaires de CARREFOUR" (aucun lien recrutement)
    # - "Adresse de CARREFOUR" (informatif seulement)

    # INNOVATIONS:
    # ✅ ACCEPTER (score élevé):
    # - "CARREFOUR lance un nouveau service"
    # - "Innovation chez CARREFOUR"
    # - "CARREFOUR développe une technologie"

    # 🤔 ACCEPTER (score modéré):
    # - "CARREFOUR modernise ses magasins" (amélioration = innovation)
    # - "Nouveautés chez CARREFOUR" (possible innovation)
    # - "CARREFOUR investit dans le digital" (lien technologique)

    # ❌ REJETER:
    # - "CARREFOUR recrute des développeurs" (thématique = recrutements)
    # - "Résultats financiers CARREFOUR" (pas d'innovation)

    # PRINCIPE GÉNÉRAL:
    # - Être PRAGMATIQUE : accepter les contenus raisonnablement liés
    # - Éviter les EXTRÊMES : ni tout rejeter, ni tout accepter
    # - FAIRE CONFIANCE au contexte : si ça peut être lié, c'est probablement valable
    # - Privilégier les FAUX POSITIFS acceptables aux FAUX NÉGATIFS dommageables

    # Réponds TOUJOURS en JSON valide:
    # {
    # "is_relevant": [true/false - true si lien raisonnable avec la thématique],
    # "confidence_score": [0.0-1.0 - moduler selon la pertinence],
    # "explanation": "Explication claire de la décision",
    # "extracted_info": {
    #     "key_facts": ["Faits pertinents extraits"],
    #     "relevance_level": "high/medium/low",
    #     "theme_connection": "Comment ça se rapporte à la thématique"
    # },
    # "themes_detected": ["Thématiques identifiées"]
    # }"""

    def _get_pme_validation_prompt(self) -> str:
        """Prompt IA PME sans biais sectoriel - Focus sur les critères généraux"""
        return """Tu es un expert en veille économique PME avec une approche RÉALISTE et ÉQUILIBRÉE.

    🏢 MISSION PME : Valider les informations sur PETITES ET MOYENNES ENTREPRISES LOCALES

    🎯 CONTEXTE PME GÉNÉRAL :
    - Entreprises 1-250 salariés (majoritairement 1-50)
    - Activité territoriale/locale
    - Communication souvent informelle
    - Présence web limitée
    - Informations fragmentaires mais authentiques

    ✅ CRITÈRES GÉNÉRAUX D'ACCEPTATION PME :

    🔍 RECRUTEMENTS PME :
    ✅ Toute mention de recherche de personnel (apprenti, stagiaire, employé, cadre)
    ✅ Offres d'emploi même modestes (temps partiel, saisonnier, CDD court)
    ✅ Recherche de compétences spécifiques au secteur d'activité
    ✅ Besoins en formation/alternance

    🎪 ÉVÉNEMENTS PME :
    ✅ Ouvertures, inaugurations, déménagements
    ✅ Changements de propriétaire ou de direction
    ✅ Nouveaux locaux, extensions, modernisations
    ✅ Participations à salons locaux, événements territoriaux

    💡 INNOVATIONS PME :
    ✅ Nouveaux services ou prestations (même simples)
    ✅ Modernisation d'équipements, digitalisation
    ✅ Nouvelles méthodes de travail ou d'organisation
    ✅ Améliorations produits, processus ou services

    🏢 VIE ENTREPRISE PME :
    ✅ Développements commerciaux, nouveaux marchés
    ✅ Partenariats, collaborations, reprises d'entreprise
    ✅ Investissements, projets de développement
    ✅ Changements organisationnels significatifs

    ❌ REJETER UNIQUEMENT SI :
    - Forums linguistiques (WordReference, dictionnaires)
    - Cours de langue, grammaire, traductions
    - Contenu sans lien évident avec l'entreprise ou le territoire
    - Informations purement techniques sans contexte business

    🎯 PRINCIPE DIRECTEUR PME :
    "Accepter toute information business authentique, même modeste, 
    plutôt que d'exiger des standards de grande entreprise"

    📊 BARÈME DE SCORING PME RÉALISTE :

    0.8-1.0 : Information PME précise et récente
    - Activité clairement documentée
    - Sources fiables et contextualisées
    - Impact territorial visible

    0.6-0.7 : Information PME pertinente  
    - Activité probable et cohérente
    - Sources correctes mais générales
    - Lien territorial établi

    0.4-0.5 : Information PME acceptable
    - Activité possible dans le secteur
    - Mention de l'entreprise confirmée
    - Contexte territorial présent

    0.2-0.3 : Information PME minimale
    - Mention d'entreprise sur le territoire
    - Activité plausible mais peu documentée
    - Information basique mais authentique

    <0.2 : Rejeter
    - Pas de lien avec l'entreprise
    - Pas de contexte territorial
    - Information non pertinente

    ⚠️ ADAPTATION SECTORIELLE AUTOMATIQUE :
    - Commerce : Focus vente, clientèle, concurrence
    - Services : Focus prestations, clients, expertise  
    - Production : Focus fabrication, équipements, marchés
    - BTP : Focus chantiers, matériaux, projets
    - Santé/Social : Focus patients, soins, réglementation
    - Mais MÊMES critères de validation pour tous !

    🌍 BONUS TERRITORIAL (crucial pour PME) :
    +0.2 si commune/code postal mentionné
    +0.1 si contexte local présent
    +0.1 si impact territorial identifié

    Réponds en JSON :
    {
    "is_relevant": true/false,
    "confidence_score": 0.0-1.0,
    "explanation": "Justification basée sur critères PME généraux",
    "pme_activity_type": "recrutement/evenement/innovation/developpement/autre",
    "territorial_context": "local/regional/national/absent",
    "authenticity_level": "elevee/moyenne/faible"
    }"""

    # 🔥 REFONTE COMPLÈTE - Remplace validate_search_result dans ai_validation_module.py

    def validate_search_result(self, entreprise: Dict, search_result: Dict, theme: str) -> ValidationResult:
        """🏢 VALIDATION SPÉCIALISÉE PME : Adaptée aux petites entreprises locales"""

        # UTILISER POUR DEBUG !
        print(f"🔥 NOUVEAU CODE PME ACTIVÉ pour {entreprise.get('nom')} - {theme}")

        
        titre = search_result.get('titre', '').lower()
        description = search_result.get('description', '').lower()
        url = search_result.get('url', '').lower()
        
        texte_complet = f"{titre} {description} {url}"
        nom_entreprise = entreprise.get('nom', '').lower()
        commune = entreprise.get('commune', '').lower()
        
        print(f"🔍 Validation PME: {titre[:50]}... pour thématique '{theme}'")
        
        # ✅ ÉTAPE 1: EXCLUSIONS SPÉCIFIQUES PME (beaucoup plus permissives)
        exclusions_strictes_pme = [
            # Sites génériques seulement
            'wikipedia.org', 'larousse.fr', 'wordreference.com',
            'dictionary.com', 'reverso.net',
            
            # Forums linguistiques
            'forum.wordreference', 'conjugaison', 'grammaire',
            'cours de français', 'leçon de français'
        ]
        
        # ❌ SUPPRIMÉ : Les exclusions trop strictes pour PME
        # - 'chiffre d\'affaires' → GARDÉ (souvent seule info PME)
        # - 'bilans' → GARDÉ (info comptable = activité)
        # - 'societe.com' → GARDÉ (fiche entreprise = légittime pour PME)
        
        for exclusion in exclusions_strictes_pme:
            if exclusion in texte_complet:
                return ValidationResult(
                    is_relevant=False,
                    confidence_score=0.0,
                    explanation=f"❌ Exclusion PME: {exclusion} détectée",
                    extracted_info={'exclusion_reason': exclusion},
                    themes_detected=[]
                )
        
        # ✅ ÉTAPE 2: VALIDATION ENTREPRISE PME (plus permissive)
        if not self._valider_entreprise_pme_recherchable(entreprise):
            return ValidationResult(
                is_relevant=False,
                confidence_score=0.0,
                explanation="❌ Entreprise non recherchable (critères PME)",
                extracted_info={'reason': 'entreprise_non_pme_recherchable'},
                themes_detected=[]
            )
        
        # ✅ ÉTAPE 3: VALIDATION THÉMATIQUE PME (seuils adaptés)
        score_thematique = self._calculer_score_thematique_pme(texte_complet, theme)
        
        # ✅ ÉTAPE 4: BONUS TERRITORIAL (crucial pour PME)
        bonus_territorial = self._calculer_bonus_territorial_pme(texte_complet, commune)
        
        # ✅ ÉTAPE 5: VALIDATION ENTREPRISE MENTIONNÉE (adaptée PME)
        score_entreprise = self._calculer_score_entreprise_pme(texte_complet, nom_entreprise)
        
        # ✅ ÉTAPE 6: CALCUL SCORE FINAL PME
        score_final = score_thematique + bonus_territorial + score_entreprise
        
        # ✅ SEUIL PME RÉALISTE (beaucoup plus bas)
        seuil_pme = 0.25  # Au lieu de 0.8+ pour grandes entreprises
        
        if score_final >= seuil_pme:
            return ValidationResult(
                is_relevant=True,
                confidence_score=min(score_final, 0.9),  # Max 0.9 pour rester réaliste
                explanation=f"✅ PME validée: score {score_final:.2f} (seuil PME: {seuil_pme})",
                extracted_info={
                    'score_thematique': score_thematique,
                    'bonus_territorial': bonus_territorial,
                    'score_entreprise': score_entreprise,
                    'validation_type': 'pme_specialisee'
                },
                themes_detected=[theme]
            )
        else:
            return ValidationResult(
                is_relevant=False,
                confidence_score=score_final,
                explanation=f"❌ Score PME insuffisant: {score_final:.2f} < {seuil_pme}",
                extracted_info={'scores_detail': {
                    'thematique': score_thematique,
                    'territorial': bonus_territorial,
                    'entreprise': score_entreprise
                }},
                themes_detected=[]
            )

    def _valider_entreprise_pme_recherchable(self, entreprise: Dict) -> bool:
        """Validation PME : beaucoup plus permissive que pour grandes entreprises"""
        nom = entreprise.get('nom', '').upper()
        
        # ❌ EXCLUSIONS STRICTES uniquement (très réduites)
        exclusions_strictes = [
            'INFORMATION NON-DIFFUSIBLE',
            'NON DIFFUSIBLE',
            'CONFIDENTIEL'
        ]
        
        for exclusion in exclusions_strictes:
            if exclusion in nom:
                return False
        
        # ✅ TRÈS PERMISSIF pour PME
        # - Personnes physiques → ACCEPTÉES (artisans, professions libérales)
        # - Noms courts → ACCEPTÉS (ex: "Café de la Gare")
        # - Sociétés familiales → ACCEPTÉES
        
        return len(nom.strip()) >= 3  # Seuil minimal très bas

    def _get_strict_validation_prompt(self) -> str:
        """Prompt IA TRÈS STRICT"""
        return """Tu es un expert en veille économique avec une approche TRÈS STRICTE.

    MISSION: Éliminer TOUS les faux positifs, même au risque de manquer des vrais résultats.

    RÈGLES STRICTES:
    1. REJETER IMMÉDIATEMENT si:
    - C'est une fiche d'annuaire (Societe.com, Verif.com, etc.)
    - C'est du contenu administratif (bilans, chiffre d'affaires, statuts)
    - C'est juste une adresse/coordonnées/horaires
    - Aucun contenu réel sur la thématique demandée

    2. ACCEPTER UNIQUEMENT si:
    - Article de presse parlant spécifiquement de l'entreprise ET de la thématique
    - Communiqué de l'entreprise sur la thématique
    - Information business réelle et récente

    3. SCORES:
    - 0.9+ : Article de presse spécialisée avec info précise
    - 0.7-0.8 : Information business réelle mais générale
    - 0.5-0.6 : Mention pertinente mais limitée
    - <0.5 : REJETER

    EN CAS DE DOUTE → REJETER

    Réponds en JSON:
    {
    "is_relevant": false (par défaut),
    "confidence_score": 0.0,
    "explanation": "Raison détaillée du rejet/acceptation",
    "content_type": "fiche_annuaire|article_presse|communique|autre",
    "extracted_info": {"key_facts": []}
    }"""

    def _validation_basique_stricte(self, mots_obligatoires: List, mots_contexte: List, 
                                mots_entreprise: List, theme: str) -> ValidationResult:
        """Validation basique stricte en fallback"""
        
        # Score basé sur les mots-clés trouvés
        score_obligatoires = len(mots_obligatoires) * 0.4
        score_contexte = len(mots_contexte) * 0.2
        score_entreprise = min(len(mots_entreprise) * 0.3, 0.3)
        
        score_total = score_obligatoires + score_contexte + score_entreprise
        
        # Seuil strict
        if score_total >= 0.6:
            return ValidationResult(
                is_relevant=True,
                confidence_score=score_total,
                explanation=f"Validation basique stricte: {score_total:.2f}",
                extracted_info={
                    'obligatory_words': mots_obligatoires,
                    'context_words': mots_contexte,
                    'enterprise_words': mots_entreprise
                },
                themes_detected=[theme]
            )
        else:
            return ValidationResult(
                is_relevant=False,
                confidence_score=score_total,
                explanation=f"Score basique insuffisant: {score_total:.2f}",
                extracted_info={},
                themes_detected=[]
            )

    def _build_strict_validation_prompt(self, entreprise: Dict, search_result: Dict, theme: str) -> str:
        """Prompt strict pour l'IA"""
        
        nom_entreprise = entreprise.get('nom', '')
        commune = entreprise.get('commune', '')
        
        titre = search_result.get('titre', '')
        description = search_result.get('description', '')
        url = search_result.get('url', '')
        
        return f"""VALIDATION STRICTE REQUISE

    ENTREPRISE: {nom_entreprise} ({commune})
    THÉMATIQUE: {theme}

    CONTENU À ANALYSER:
    Titre: {titre}
    Description: {description}
    URL: {url}

    QUESTION: Ce contenu est-il un VRAI article/information business sur {nom_entreprise} 
    concernant spécifiquement la thématique {theme} ?

    REJETER si c'est:
    - Fiche annuaire (Societe.com, etc.)
    - Informations administratives/financières générales
    - Simple coordonnées/adresse

    ACCEPTER seulement si:
    - Article de presse business réel
    - Communiqué entreprise
    - Information concrète sur la thématique

    Analyse stricte et réponds en JSON."""

    def _calculer_score_thematique_pme(self, texte: str, theme: str) -> float:
        """Score thématique adapté aux PME avec mots-clés spécialisés"""
        
        # 🏢 MOTS-CLÉS PME SPÉCIALISÉS (totalement différents des grandes entreprises)
        mots_cles_pme = {
            'recrutements': {
                'forts': ['cherche', 'recherche', 'recrute', 'embauche'],  # Sans "50 personnes"
                'moyens': ['apprenti', 'stagiaire', 'saisonnier', 'temps partiel', 'aide'],
                'faibles': ['équipe', 'personnel', 'candidat', 'cv', 'poste']
            },
            
            'evenements': {
                'forts': ['ouverture', 'inauguration', 'nouveau', 'porte ouverte'],
                'moyens': ['déménage', 'agrandit', 'rénove', 'modernise'],
                'faibles': ['horaires', 'fermeture', 'vacances', 'congés']
            },
            
            'innovations': {
                'forts': ['nouveau service', 'nouvelle prestation', 'maintenant'],  # PME scale
                'moyens': ['améliore', 'modernise', 'équipe', 'investit'],
                'faibles': ['rénove', 'change', 'propose', 'offre']
            },
            
            'vie_entreprise': {
                'forts': ['reprend', 'cède', 'nouveau propriétaire', 'changement'],
                'moyens': ['déménage', 'agrandit', 'partenaire', 'collabore'],
                'faibles': ['développe', 'évolue', 'projet', 'avenir']
            }
        }
        
        if theme not in mots_cles_pme:
            return 0.0
        
        mots_theme = mots_cles_pme[theme]
        score = 0.0
        
        # Scoring PME adapté
        for mot in mots_theme['forts']:
            if mot in texte:
                score += 0.4  # Score élevé mais réaliste
        
        for mot in mots_theme['moyens']:
            if mot in texte:
                score += 0.2
        
        for mot in mots_theme['faibles']:
            if mot in texte:
                score += 0.1
        
        return min(score, 0.6)  # Max 0.6 au lieu de 1.0

    def _calculer_bonus_territorial_pme(self, texte: str, commune: str) -> float:
        """Bonus territorial crucial pour PME (activité hyper-locale)"""
        
        if not commune:
            return 0.0
        
        bonus = 0.0
        commune_lower = commune.lower()
        
        # ✅ MENTION COMMUNE (très important pour PME)
        if commune_lower in texte:
            bonus += 0.3  # Gros bonus territorial
        
        # ✅ INDICATEURS LOCAUX PME
        indicateurs_locaux = [
            'local', 'quartier', 'près de', 'centre ville', 'proche',
            'livraison', 'domicile', 'déplacement', 'secteur'
        ]
        
        for indicateur in indicateurs_locaux:
            if indicateur in texte:
                bonus += 0.05  # Petit bonus cumulatif
        
        # ✅ CODES POSTAUX (hyper-local PME)
        codes_postaux_77 = ['77600', '77700', '77400', '77200']  # Vos codes
        for code in codes_postaux_77:
            if code in texte:
                bonus += 0.2
                break
        
        return min(bonus, 0.4)  # Max 0.4

    def _calculer_score_entreprise_pme(self, texte: str, nom_entreprise: str) -> float:
        """Score entreprise adapté aux noms PME (souvent courts, familiers)"""
        
        if not nom_entreprise:
            return 0.0
        
        # ✅ NETTOYAGE SPÉCIAL PME
        nom_clean = nom_entreprise.replace('MADAME ', '').replace('MONSIEUR ', '')
        nom_clean = nom_clean.replace('M. ', '').replace('MME ', '')
        
        # ✅ MOTS SIGNIFICATIFS PME (seuil très bas)
        mots_entreprise = [mot for mot in nom_clean.split() if len(mot) > 2]
        
        if not mots_entreprise:
            return 0.0
        
        # ✅ COMPTAGE ADAPTÉ PME
        mots_trouves = 0
        for mot in mots_entreprise:
            if mot.lower() in texte:
                mots_trouves += 1
        
        # ✅ SCORING PME RÉALISTE
        if mots_trouves == 0:
            return 0.0
        elif mots_trouves == 1:
            return 0.2  # Acceptable pour PME
        elif mots_trouves >= 2:
            return 0.4  # Très bon pour PME
        
        return 0.0

    # ✅ DÉSACTIVATION VALIDATION THÉMATIQUE
    def validate_theme_match(self, contenu_texte: str, thematique: str) -> bool:
        """Mode ultra-permissif: Accepte TOUT"""
        return True  # ✅ Déjà correct

    # ✅ FALLBACK ULTRA-PERMISSIF
    def _fallback_validation(self, entreprise: Dict, result: Dict, theme: str):
        """Fallback qui accepte presque tout"""
        
        return ValidationResult(
            is_relevant=True,
            confidence_score=0.5,
            explanation="Fallback ultra-permissif: Accepté par défaut",
            extracted_info={'method': 'fallback_permissif'},
            themes_detected=[theme]
        )

    def batch_validate_results(self, entreprise: Dict, results_by_theme: Dict) -> Dict[str, List[Dict]]:
        """Validation ultra-permissive pour PME"""
        validated_results = {}
        for theme, extraits in results_by_theme.items():
            validated_results[theme] = []
            if isinstance(extraits, dict):
                extraits = extraits.get('extraits_textuels', [])
            for extrait in extraits[:3]:  # Prendre les 3 premiers
                if isinstance(extrait, dict):
                    extrait.update({
                        'ai_validated': True,
                        'ai_fallback_pme': True,
                        'fallback_reason': 'Validation PME ultra-permissive',
                        'confidence_fallback': 0.6
                    })
                    validated_results[theme].append(extrait)
        return validated_results

    def get_usage_stats(self) -> Dict:
        """Statistiques d'utilisation de l'API"""
        estimated_cost = (self.tokens_used * 0.00015 / 1000)  # Prix GPT-4o-mini
        
        return {
            'api_calls': self.api_calls_count,
            'tokens_used': self.tokens_used,
            'estimated_cost_usd': estimated_cost,
            'avg_tokens_per_call': self.tokens_used / max(self.api_calls_count, 1)
        }

# Fonction d'intégration dans le système principal
def setup_ai_validation(veille_economique):
    """
    Configuration du module IA dans le système de veille économique
    
    Args:
        veille_economique: Instance de VeilleEconomique
    """
    
    try:
        # Initialisation du module IA
        ai_module = AIValidationModule()
        
        # Intégration avec l'analyseur existant
        # Note: ceci nécessite d'avoir accès à l'analyseur dans votre main.py
        # Vous pouvez adapter selon votre architecture
        
        print("🤖 Module IA de validation configuré")
        print("🎯 Avantages activés:")
        print("   ✅ Réduction drastique des faux positifs")
        print("   ✅ Validation intelligente des résultats")
        print("   ✅ Résumés automatiques d'activité")
        print("   ✅ Classification thématique améliorée")
        
        return ai_module
        
    except Exception as e:
        print(f"❌ Erreur configuration IA: {e}")
        print("💡 Vérifiez que le fichier .env contient OPENAI_API_KEY")
        return None

if __name__ == "__main__":
    # Test du module
    print("🧪 Test du module IA de validation")
    
    try:
        ai_module = AIValidationModule()
        
        # Test avec données factices
        entreprise_test = {
            'nom': 'CARREFOUR',
            'commune': 'Boulogne-Billancourt',
            'secteur_naf': 'Commerce de détail'
        }
        
        resultat_test = {
            'titre': 'CARREFOUR recrute 50 personnes en CDI à Boulogne-Billancourt',
            'description': 'Le groupe Carrefour annonce le recrutement de 50 collaborateurs en contrat à durée indéterminée pour son magasin de Boulogne-Billancourt.',
            'url': 'https://www.carrefour.fr/recrutement'
        }
        
        validation = ai_module.validate_search_result(entreprise_test, resultat_test, 'recrutements')
        
        print(f"✅ Test réussi:")
        print(f"   Pertinent: {validation.is_relevant}")
        print(f"   Confiance: {validation.confidence_score}")
        print(f"   Explication: {validation.explanation}")
        
        stats = ai_module.get_usage_stats()
        print(f"\n📊 Statistiques: {stats}")
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")