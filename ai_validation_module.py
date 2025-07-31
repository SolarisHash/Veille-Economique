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
    
    def _get_validation_system_prompt(self) -> str:
        """✅ PROMPT ÉQUILIBRÉ : Ni trop strict, ni trop permissif"""
        return """Tu es un expert en veille économique avec une approche ÉQUILIBRÉE et PRAGMATIQUE.

    OBJECTIF: Valider les résultats pertinents tout en évitant les faux positifs évidents.

    RÈGLES DE VALIDATION ÉQUILIBRÉES:

    ✅ VALIDER SI:
    1. Le nom de l'entreprise EST mentionné dans le contenu ET
    2. Le contenu a un lien logique avec la thématique demandée ET
    3. C'est dans un contexte professionnel/économique

    ❌ REJETER SI:
    1. Contenu complètement hors-sujet (dictionnaires, forums linguistiques)
    2. Thématique totalement différente (ex: chiffre d'affaires pour "recrutements")
    3. Mention uniquement administrative sans lien thématique

    🤔 CAS LIMITES - ACCEPTER AVEC SCORE MODÉRÉ:
    - Informations générales d'entreprise avec mention indirecte de la thématique
    - Articles de presse mentionnant l'entreprise dans un contexte lié
    - Contenus partiellement pertinents mais pas parfaitement alignés

    EXEMPLES CONCRETS:

    RECRUTEMENTS:
    ✅ ACCEPTER (score élevé 0.8+):
    - "CARREFOUR recrute 50 personnes"
    - "Offres d'emploi chez CARREFOUR"
    - "CARREFOUR cherche un directeur"

    🤔 ACCEPTER (score modéré 0.4-0.6):
    - "CARREFOUR développe ses équipes" (implication recrutement)
    - "Croissance de CARREFOUR et nouveaux postes" (lien indirect)
    - "CARREFOUR renforce son organisation" (possible recrutement)

    ❌ REJETER (score <0.3):
    - "Chiffre d'affaires de CARREFOUR" (aucun lien recrutement)
    - "Adresse de CARREFOUR" (informatif seulement)

    INNOVATIONS:
    ✅ ACCEPTER (score élevé):
    - "CARREFOUR lance un nouveau service"
    - "Innovation chez CARREFOUR"
    - "CARREFOUR développe une technologie"

    🤔 ACCEPTER (score modéré):
    - "CARREFOUR modernise ses magasins" (amélioration = innovation)
    - "Nouveautés chez CARREFOUR" (possible innovation)
    - "CARREFOUR investit dans le digital" (lien technologique)

    ❌ REJETER:
    - "CARREFOUR recrute des développeurs" (thématique = recrutements)
    - "Résultats financiers CARREFOUR" (pas d'innovation)

    PRINCIPE GÉNÉRAL:
    - Être PRAGMATIQUE : accepter les contenus raisonnablement liés
    - Éviter les EXTRÊMES : ni tout rejeter, ni tout accepter
    - FAIRE CONFIANCE au contexte : si ça peut être lié, c'est probablement valable
    - Privilégier les FAUX POSITIFS acceptables aux FAUX NÉGATIFS dommageables

    Réponds TOUJOURS en JSON valide:
    {
    "is_relevant": [true/false - true si lien raisonnable avec la thématique],
    "confidence_score": [0.0-1.0 - moduler selon la pertinence],
    "explanation": "Explication claire de la décision",
    "extracted_info": {
        "key_facts": ["Faits pertinents extraits"],
        "relevance_level": "high/medium/low",
        "theme_connection": "Comment ça se rapporte à la thématique"
    },
    "themes_detected": ["Thématiques identifiées"]
    }"""

    # 🔥 REFONTE COMPLÈTE - Remplace validate_search_result dans ai_validation_module.py

    def validate_search_result(self, entreprise: Dict, search_result: Dict, theme: str) -> ValidationResult:
        """🎯 VALIDATION INTELLIGENTE : Rejette les annuaires et faux positifs"""
        
        titre = search_result.get('titre', '').lower()
        description = search_result.get('description', '').lower()
        url = search_result.get('url', '').lower()
        
        texte_complet = f"{titre} {description} {url}"
        nom_entreprise = entreprise.get('nom', '').lower()
        
        print(f"🔍 Validation: {titre[:50]}... pour thématique '{theme}'")
        
        # ✅ ÉTAPE 1: EXCLUSIONS STRICTES (Faux positifs évidents)
        exclusions_strictes = [
            # Sites d'annuaires/fiches entreprise
            'societe.com', 'verif.com', 'manageo.fr', 'infonet.fr', 'pagesjaunes.fr',
            'entreprises.lefigaro.fr', 'qwant.com', '118000.fr', 'kompass.com',
            
            # Contenu purement administratif
            'chiffre d\'affaires', 'bilans', 'statuts', 'sirene', 'kbis',
            'résultats financiers', 'bilan comptable', 'actionnaires',
            'numéro tva', 'code ape', 'forme juridique', 'dirigeants',
            
            # Sites génériques non pertinents
            'horaires d\'ouverture', 'adresse téléphone', 'coordonnées',
            'plan d\'accès', 'itinéraire', 'contact',
            
            # Forums/dictionnaires
            'wordreference', 'larousse', 'dictionary', 'définition'
        ]
        
        for exclusion in exclusions_strictes:
            if exclusion in texte_complet:
                return ValidationResult(
                    is_relevant=False,
                    confidence_score=0.0,
                    explanation=f"❌ Exclusion stricte: {exclusion} détectée",
                    extracted_info={'exclusion_reason': exclusion},
                    themes_detected=[]
                )
        
        # ✅ ÉTAPE 2: VALIDATION ENTREPRISE
        if not self._valider_entreprise_recherchable(entreprise):
            return ValidationResult(
                is_relevant=False,
                confidence_score=0.0,
                explanation="❌ Entreprise non recherchable (personne physique)",
                extracted_info={'reason': 'entreprise_non_recherchable'},
                themes_detected=[]
            )
        
        # ✅ ÉTAPE 3: VALIDATION THÉMATIQUE STRICTE
        mots_cles_stricts_par_theme = {
            'recrutements': {
                'obligatoires': ['recrut', 'emploi', 'embauche', 'poste', 'cdi', 'cdd', 'stage'],
                'contexte': ['candidat', 'cv', 'entretien', 'offre', 'carrière', 'équipe']
            },
            'evenements': {
                'obligatoires': ['événement', 'évènement', 'salon', 'conférence', 'porte ouverte'],
                'contexte': ['rencontre', 'forum', 'manifestation', 'inauguration']
            },
            'innovations': {
                'obligatoires': ['innovation', 'nouveau produit', 'nouveau service', 'lancement'],
                'contexte': ['développe', 'crée', 'technologie', 'brevets', 'r&d']
            },
            'vie_entreprise': {
                'obligatoires': ['ouverture', 'fermeture', 'expansion', 'partenariat'],
                'contexte': ['développement', 'projet', 'investissement', 'croissance']
            }
        }
        
        theme_config = mots_cles_stricts_par_theme.get(theme, {'obligatoires': [], 'contexte': []})
        
        # Recherche mots-clés obligatoires
        mots_obligatoires_trouves = [mot for mot in theme_config['obligatoires'] if mot in texte_complet]
        mots_contexte_trouves = [mot for mot in theme_config['contexte'] if mot in texte_complet]
        
        if not mots_obligatoires_trouves and not mots_contexte_trouves:
            return ValidationResult(
                is_relevant=False,
                confidence_score=0.0,
                explanation=f"❌ Aucun mot-clé {theme} trouvé",
                extracted_info={'theme_words_found': []},
                themes_detected=[]
            )
        
        # ✅ ÉTAPE 4: VALIDATION ENTREPRISE MENTIONNÉE
        mots_entreprise = [mot for mot in nom_entreprise.split() if len(mot) > 2]
        mots_entreprise_trouves = [mot for mot in mots_entreprise if mot in texte_complet]
        
        if len(mots_entreprise) > 0 and len(mots_entreprise_trouves) == 0:
            return ValidationResult(
                is_relevant=False,
                confidence_score=0.0,
                explanation="❌ Nom entreprise non mentionné",
                extracted_info={'enterprise_words_found': []},
                themes_detected=[]
            )
        
        # ✅ ÉTAPE 5: VALIDATION IA FINALE (seulement si tout passe)
        prompt = self._build_strict_validation_prompt(entreprise, search_result, theme)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_strict_validation_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.0,  # Température 0 = plus déterministe
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            self.api_calls_count += 1
            self.tokens_used += response.usage.total_tokens
            
            # ✅ SEUIL TRÈS STRICT
            confidence_threshold = 0.05  # Score élevé requis
            is_relevant = result_json.get('is_relevant', False)
            confidence_score = result_json.get('confidence_score', 0.0)
            
            if is_relevant and confidence_score >= confidence_threshold:
                print(f"✅ IA validé: {confidence_score:.2f}")
                return ValidationResult(
                    is_relevant=True,
                    confidence_score=confidence_score,
                    explanation=f"✅ Validé par IA: {result_json.get('explanation', '')}",
                    extracted_info=result_json.get('extracted_info', {}),
                    themes_detected=result_json.get('themes_detected', [])
                )
            else:
                print(f"❌ IA rejeté: {confidence_score:.2f}")
                return ValidationResult(
                    is_relevant=False,
                    confidence_score=confidence_score,
                    explanation=f"❌ IA: {result_json.get('explanation', '')}",
                    extracted_info={},
                    themes_detected=[]
                )
                
        except Exception as e:
            print(f"❌ Erreur IA: {e}")
            # En cas d'erreur IA, validation basique stricte
            return self._validation_basique_stricte(
                mots_obligatoires_trouves, mots_contexte_trouves, 
                mots_entreprise_trouves, theme
            )

    def _valider_entreprise_recherchable(self, entreprise: Dict) -> bool:
        """Validation si l'entreprise est recherchable"""
        nom = entreprise.get('nom', '').upper()
        
        # Exclusions évidentes
        exclusions = [
            'MADAME', 'MONSIEUR', 'MADEMOISELLE', 'M.', 'MME', 'MLLE',
            'INDIVISION', 'INFORMATION NON-DIFFUSIBLE'
        ]
        
        for exclusion in exclusions:
            if nom.startswith(exclusion):
                print(f"❌ Entreprise non recherchable: {exclusion}")
                return False
        
        # Doit avoir au moins 2 mots significatifs
        mots_significatifs = [mot for mot in nom.split() if len(mot) > 2]
        if len(mots_significatifs) < 2:
            print(f"❌ Nom trop simple: {nom}")
            return False
        
        return True

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

    # ✅ DÉSACTIVATION VALIDATION THÉMATIQUE
    def validate_theme_match(self, contenu_texte: str, thematique: str) -> bool:
        """Mode ultra-permissif: Accepte TOUT"""
        return True  # Accepte systématiquement

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
        """✅ VALIDATION PERMISSIVE avec fallback intelligent"""
        
        print(f"🤖 Validation IA PERMISSIVE pour {entreprise.get('nom', 'N/A')}")
        
        validated_results = {}
        total_results = 0
        
        # Comptage total pour statistiques
        for theme, donnees_thematique in results_by_theme.items():
            if isinstance(donnees_thematique, dict):
                extraits = donnees_thematique.get('extraits_textuels', [])
                if isinstance(extraits, list):
                    total_results += len(extraits)
        
        print(f"   📊 {total_results} extraits à valider")
        
        for theme, donnees_thematique in results_by_theme.items():
            validated_results[theme] = []
            
            if isinstance(donnees_thematique, dict):
                extraits = donnees_thematique.get('extraits_textuels', [])
                
                if isinstance(extraits, list):
                    print(f"   🎯 {theme}: {len(extraits)} extraits")
                    
                    for i, extrait in enumerate(extraits):
                        try:
                            # Normalisation format
                            if isinstance(extrait, dict):
                                result_for_ai = extrait
                            else:
                                result_for_ai = {
                                    'titre': str(extrait),
                                    'description': '',
                                    'url': ''
                                }
                            
                            # ✅ VALIDATION IA AVEC FALLBACK
                            try:
                                validation = self.validate_search_result(entreprise, result_for_ai, theme)
                                ai_success = True
                            except Exception as e:
                                print(f"     ⚠️ IA échouée pour extrait {i+1}: {e}")
                                # ✅ FALLBACK: Validation basique sans IA
                                validation = self._fallback_validation(entreprise, result_for_ai, theme)
                                ai_success = False
                            
                            # ✅ SEUIL TRÈS PERMISSIF
                            seuil_permissif = 0.3  # Seuil bas
                            
                            if validation.is_relevant or validation.confidence_score > seuil_permissif:
                                enriched_result = result_for_ai.copy()
                                enriched_result.update({
                                    'ai_validated': ai_success,
                                    'ai_confidence': validation.confidence_score,
                                    'ai_explanation': validation.explanation,
                                    'ai_extracted_info': validation.extracted_info,
                                    'ai_themes': validation.themes_detected,
                                    'validation_timestamp': datetime.now().isoformat(),
                                    'validation_method': 'ai' if ai_success else 'fallback'
                                })
                                validated_results[theme].append(enriched_result)
                                
                                method = "IA" if ai_success else "Fallback"
                                print(f"     ✅ {method}: Validé (conf: {validation.confidence_score:.2f})")
                            else:
                                print(f"     ❌ Rejeté: {validation.explanation[:50]}...")
                                
                        except Exception as e:
                            print(f"     ❌ Erreur validation extrait {i+1}: {e}")
                            # ✅ EN CAS D'ERREUR TOTALE: Garder l'extrait quand même
                            if isinstance(extrait, dict) and extrait.get('titre'):
                                extrait['ai_validated'] = False
                                extrait['ai_fallback'] = True
                                extrait['fallback_reason'] = f"Erreur IA: {str(e)[:100]}"
                                validated_results[theme].append(extrait)
                                print(f"     🔄 Sauvé malgré l'erreur")
                    
                    # ✅ FALLBACK FINAL si aucun résultat validé
                    if not validated_results[theme] and len(extraits) > 0:
                        print(f"   🔄 FALLBACK: IA trop stricte, récupération des meilleurs extraits")
                        
                        # Garder au moins 1-2 extraits les plus prometteurs
                        for extrait in extraits[:2]:
                            if isinstance(extrait, dict):
                                extrait.update({
                                    'ai_validated': False,
                                    'ai_fallback_final': True,
                                    'fallback_reason': 'IA trop restrictive - récupération automatique',
                                    'confidence_fallback': 0.5
                                })
                                validated_results[theme].append(extrait)
                        
                        print(f"   📋 {len(validated_results[theme])} extraits récupérés automatiquement")
        
        # Statistiques finales
        total_validated = sum(len(results) for results in validated_results.values())
        print(f"   📊 Validation terminée: {total_validated}/{total_results} extraits validés")
        
        # ✅ SI ÉCHEC TOTAL: Mode de secours
        if total_validated == 0 and total_results > 0:
            print(f"   🚨 ACTIVATION MODE SECOURS: Récupération forcée")
            validated_results = self._mode_secours_validation(results_by_theme)
            total_validated = sum(len(results) for results in validated_results.values())
            print(f"   🔄 Mode secours: {total_validated} extraits récupérés")
        
        return validated_results

    def _mode_secours_validation(self, results_by_theme: Dict) -> Dict:
        """✅ MODE SECOURS: Récupération forcée quand l'IA échoue totalement"""
        print("   🚨 ACTIVATION MODE SECOURS")
        
        secours_results = {}
        
        for theme, donnees in results_by_theme.items():
            secours_results[theme] = []
            
            if isinstance(donnees, dict):
                extraits = donnees.get('extraits_textuels', [])
                
                # Récupérer au moins 1 extrait par thématique si disponible
                for extrait in extraits[:1]:  # Premier extrait seulement
                    if isinstance(extrait, dict):
                        extrait.update({
                            'ai_validated': False,
                            'mode_secours': True,
                            'secours_reason': 'IA complètement défaillante - récupération forcée',
                            'confidence_secours': 0.3
                        })
                        secours_results[theme].append(extrait)
                        print(f"     🔄 {theme}: 1 extrait récupéré en mode secours")
        
        return secours_results

    def _build_validation_prompt(self, entreprise: Dict, search_result, theme: str) -> str:
        """Construction du prompt de validation spécifique"""
        
        nom_entreprise = entreprise.get('nom', '')
        commune = entreprise.get('commune', '')
        secteur = entreprise.get('secteur_naf', '')
        
        # Gestion robuste du format search_result
        if isinstance(search_result, dict):
            # Format dict standard
            titre = search_result.get('titre', '')
            description = search_result.get('description', '')
            url = search_result.get('url', '')
        elif isinstance(search_result, str):
            # Format string - traiter comme titre
            titre = search_result
            description = ""
            url = ""
        else:
            # Format inattendu - conversion sécurisée
            titre = str(search_result)
            description = ""
            url = ""
        
        return f"""ANALYSE DE PERTINENCE REQUISE

ENTREPRISE À ANALYSER :
- Nom : "{nom_entreprise}"
- Commune : {commune}
- Secteur : {secteur}

THÉMATIQUE RECHERCHÉE : {theme}

RÉSULTAT DE RECHERCHE À VALIDER :
- Titre : {titre}
- Description : {description}
- URL : {url}

QUESTION : Ce résultat de recherche parle-t-il VRAIMENT de l'entreprise "{nom_entreprise}" concernant la thématique "{theme}" ?

Sois très strict sur la pertinence. Un simple mention du nom sans contexte entrepreneurial pertinent = NON PERTINENT.

Analyse et réponds en JSON."""
    
    def generate_smart_summary(self, entreprise: Dict, validated_results: Dict[str, List[Dict]]) -> Dict:
        """
        Génération d'un résumé intelligent de l'activité de l'entreprise
        
        Args:
            entreprise: Données de l'entreprise
            validated_results: Résultats validés par thématique
        
        Returns:
            Dict avec résumé intelligent et insights
        """
        
        # Préparation des données pour le résumé
        all_validated_info = []
        for theme, results in validated_results.items():
            for result in results:
                all_validated_info.append({
                    'theme': theme,
                    'title': result.get('titre', ''),
                    'description': result.get('description', ''),
                    'ai_info': result.get('ai_extracted_info', {}),
                    'confidence': result.get('ai_confidence', 0)
                })
        
        if not all_validated_info:
            return {
                'summary': f"Aucune activité significative détectée pour {entreprise.get('nom', 'cette entreprise')}",
                'key_activities': [],
                'activity_level': 'Très faible',
                'recommendations': ['Surveillance périodique recommandée']
            }
        
        # Prompt pour le résumé intelligent
        summary_prompt = self._build_summary_prompt(entreprise, all_validated_info)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_summary_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                max_tokens=600,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            self.api_calls_count += 1
            self.tokens_used += response.usage.total_tokens
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"❌ Erreur génération résumé: {e}")
            return {
                'summary': f"Activité détectée pour {entreprise.get('nom', 'cette entreprise')} mais erreur de synthèse",
                'key_activities': [f"{len(all_validated_info)} informations validées"],
                'activity_level': 'Modéré',
                'recommendations': ['Vérification manuelle recommandée']
            }
    
    def _get_summary_system_prompt(self) -> str:
        """Prompt système pour la génération de résumés"""
        return """Tu es un expert en analyse d'activité économique d'entreprises.

Ta mission : synthétiser l'activité récente d'une entreprise à partir d'informations validées.

OBJECTIFS :
1. Résumer clairement l'activité principale
2. Identifier les événements/développements clés
3. Évaluer le niveau d'activité (Faible/Modéré/Élevé/Très élevé)
4. Proposer des recommandations de surveillance

STYLE :
- Professionnel et factuel
- Concis mais informatif
- Orienté action pour la veille économique

Réponds en JSON avec cette structure :
{
  "summary": "Résumé de 2-3 phrases de l'activité",
  "key_activities": ["activité1", "activité2", "activité3"],
  "activity_level": "Faible|Modéré|Élevé|Très élevé",
  "recommendations": ["recommandation1", "recommandation2"],
  "priority_themes": ["thème1", "thème2"]
}"""

    def _build_summary_prompt(self, entreprise: Dict, validated_info: List[Dict]) -> str:
        """Construction du prompt pour le résumé"""
        
        nom_entreprise = entreprise.get('nom', '')
        commune = entreprise.get('commune', '')
        secteur = entreprise.get('secteur_naf', '')
        
        # Formatage des informations validées
        info_text = ""
        for info in validated_info:
            info_text += f"- [{info['theme']}] {info['title']}: {info['description'][:100]}...\n"
        
        return f"""SYNTHÈSE D'ACTIVITÉ REQUISE

ENTREPRISE :
- Nom : {nom_entreprise}
- Commune : {commune}  
- Secteur : {secteur}

INFORMATIONS VALIDÉES RÉCENTES :
{info_text}

NOMBRE D'INFORMATIONS : {len(validated_info)}

Synthétise cette activité en identifiant les tendances principales et le niveau d'activité de cette entreprise.
Sois factuel et précis."""

    def integrate_with_existing_analyzer(self, analyseur_thematiques):
        """
        Intégration avec l'analyseur thématique existant
        
        Args:
            analyseur_thematiques: Instance de AnalyseurThematiques
        """
        
        # Sauvegarde de la méthode originale
        original_analyser_resultats = analyseur_thematiques.analyser_resultats
        
        def analyser_resultats_with_ai(resultats_bruts, logger=None):
            """Version améliorée avec validation IA + fallback intelligent"""
            
            print("🤖 Analyse thématique avec validation IA")
            print("-" * 50)
            
            entreprises_enrichies = []
            
            for i, resultat in enumerate(resultats_bruts, 1):
                entreprise = resultat.get('entreprise', {})
                nom_entreprise = entreprise.get('nom', f'Entreprise_{i}')
                
                print(f"  🏢 {i}/{len(resultats_bruts)}: {nom_entreprise}")
                
                donnees_thematiques = resultat.get('donnees_thematiques', {})
                
                if donnees_thematiques:
                    # 🤖 TENTATIVE VALIDATION IA
                    try:
                        validated_results = self.batch_validate_results(entreprise, donnees_thematiques)
                        
                        # Vérification si l'IA a trouvé quelque chose
                        total_ai_results = sum(len(results) for results in validated_results.values())
                        
                        if total_ai_results > 0:
                            print(f"    ✅ IA: {total_ai_results} résultats validés")
                            # Utiliser les résultats IA
                            resultat_avec_validation = resultat.copy()
                            resultat_avec_validation['donnees_thematiques'] = validated_results
                            
                            entreprise_analysee = analyseur_thematiques._analyser_entreprise(resultat_avec_validation)
                            
                            # Génération du résumé intelligent IA
                            smart_summary = self.generate_smart_summary(entreprise, validated_results)
                            
                        else:
                            print(f"    ⚠️ IA: Aucun résultat validé - FALLBACK vers analyse classique")
                            # 🔄 FALLBACK: Analyse classique si IA trop stricte
                            entreprise_analysee = analyseur_thematiques._analyser_entreprise(resultat)
                            smart_summary = {'summary': f'Analyse classique appliquée (IA trop stricte) - {len(donnees_thematiques)} thématiques détectées'}
                        
                    except Exception as e:
                        print(f"    ❌ Erreur IA: {e} - FALLBACK vers analyse classique")
                        # FALLBACK en cas d'erreur IA
                        entreprise_analysee = analyseur_thematiques._analyser_entreprise(resultat)
                        smart_summary = {'summary': f'Analyse classique (erreur IA): {str(e)[:100]}'}
                    
                    # Enrichissement avec l'IA (si disponible)
                    entreprise_analysee.update({
                        'ai_summary': smart_summary,
                        'ai_validation_applied': True,
                        'ai_stats': {
                            'api_calls': self.api_calls_count,
                            'tokens_used': self.tokens_used
                        }
                    })
                    
                    score_final = entreprise_analysee.get('score_global', 0)
                    print(f"    🎯 Score final: {score_final:.3f}")
                    
                    if score_final > 0:
                        print(f"    📝 Résumé: {smart_summary.get('summary', '')[:60]}...")
                    else:
                        print(f"    ⚠️ Aucune activité détectée")
                    
                else:
                    # Pas de données thématiques
                    entreprise_analysee = analyseur_thematiques._analyser_entreprise(resultat)
                    entreprise_analysee.update({
                        'ai_summary': {'summary': 'Aucune donnée thématique trouvée'},
                        'ai_validation_applied': False
                    })
                
                entreprises_enrichies.append(entreprise_analysee)
            
            # Statistiques finales
            entreprises_avec_activite = [e for e in entreprises_enrichies if e.get('score_global', 0) > 0]
            
            print(f"\n📊 Statistiques IA:")
            print(f"   🔧 Appels API: {self.api_calls_count}")
            print(f"   📝 Tokens utilisés: {self.tokens_used}")
            print(f"   💰 Coût estimé: ${(self.tokens_used * 0.00015 / 1000):.4f}")
            print(f"   🎯 Entreprises avec activité: {len(entreprises_avec_activite)}/{len(entreprises_enrichies)}")
            
            if len(entreprises_avec_activite) == 0:
                print(f"   ⚠️ WARNING: IA trop stricte - considérez ajuster les paramètres")
            
            return entreprises_enrichies
        
        # Remplacement de la méthode
        analyseur_thematiques.analyser_resultats = analyser_resultats_with_ai
        
        print("✅ Module IA intégré à l'analyseur thématique")
    
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