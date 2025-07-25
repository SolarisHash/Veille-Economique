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
    
    def validate_search_result(self, entreprise: Dict, search_result: Dict, theme: str) -> ValidationResult:
        """
        Validation IA d'un résultat de recherche pour une entreprise et thématique données
        
        Args:
            entreprise: Données de l'entreprise (nom, commune, secteur)
            search_result: Résultat de recherche (titre, description, url)
            theme: Thématique recherchée (recrutements, evenements, etc.)
        
        Returns:
            ValidationResult: Résultat détaillé de la validation
        """
        
        # Préparation du prompt optimisé
        prompt = self._build_validation_prompt(entreprise, search_result, theme)
        
        try:
            # Appel API GPT-4o-mini
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_validation_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parsing de la réponse
            result_json = json.loads(response.choices[0].message.content)
            
            # Mise à jour des compteurs
            self.api_calls_count += 1
            self.tokens_used += response.usage.total_tokens
            
            # Construction du résultat
            return ValidationResult(
                is_relevant=result_json.get('is_relevant', False),
                confidence_score=result_json.get('confidence_score', 0.0),
                explanation=result_json.get('explanation', ''),
                extracted_info=result_json.get('extracted_info', {}),
                themes_detected=result_json.get('themes_detected', [])
            )
            
        except Exception as e:
            print(f"❌ Erreur validation IA: {e}")
            # Fallback : validation conservatrice
            return ValidationResult(
                is_relevant=False,
                confidence_score=0.0,
                explanation=f"Erreur IA: {str(e)}",
                extracted_info={},
                themes_detected=[]
            )
    
    def _get_validation_system_prompt(self) -> str:
        """Prompt système optimisé pour la validation de veille économique"""
        return """Tu es un expert en veille économique territoriale française. 

Ta mission : analyser si un résultat de recherche web est VRAIMENT pertinent pour une entreprise et une thématique données.

ATTENTION aux faux positifs courants :
- Sites de définitions/dictionnaires mentionnant juste le nom
- Forums linguistiques (wordreference, etc.)
- Résultats génériques sans lien réel avec l'entreprise
- Articles parlant d'autres entreprises avec nom similaire

CRITÈRES DE VALIDATION STRICTE :
1. Le contenu doit VRAIMENT parler de l'entreprise spécifique
2. L'information doit être en rapport avec la thématique demandée
3. Le contexte doit être professionnel/économique
4. La source doit être fiable

THÉMATIQUES ACCEPTÉES :
- recrutements : offres emploi, embauches, CDI/CDD
- evenements : portes ouvertes, salons, conférences
- innovations : nouveaux produits/services, R&D, brevets
- vie_entreprise : développement, partenariats, implantations
- exportations : commerce international, marchés étrangers
- aides_subventions : financements publics, subventions
- fondation_sponsor : mécénat, actions sociales

Réponds TOUJOURS en JSON valide avec cette structure :
{
  "is_relevant": boolean,
  "confidence_score": float (0.0 à 1.0),
  "explanation": "Explication détaillée de ta décision",
  "extracted_info": {
    "key_facts": ["fait1", "fait2"],
    "date_mentioned": "date si trouvée",
    "location_mentioned": "lieu si mentionné"
  },
  "themes_detected": ["thématique1", "thématique2"]
}"""

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

    def batch_validate_results(self, entreprise: Dict, results_by_theme: Dict) -> Dict[str, List[Dict]]:
        """
        Validation par lot avec correction automatique de qualité
        
        Args:
            entreprise: Données de l'entreprise
            results_by_theme: Dict {thématique: données_thematique}
        
        Returns:
            Dict avec résultats validés et enrichis
        """
        
        print(f"🤖 Validation IA avec correction qualité pour {entreprise.get('nom', 'N/A')}")
        
        # 🔧 ÉTAPE 1: Correction automatique de la qualité des données
        try:
            from data_quality_fixer import DataQualityFixer
            quality_fixer = DataQualityFixer()
            results_corriges = quality_fixer.corriger_donnees_thematiques(entreprise, results_by_theme)
            print(f"   ✅ Correction qualité appliquée")
        except ImportError:
            print(f"   ⚠️ DataQualityFixer non disponible - utilisation données brutes")
            results_corriges = results_by_theme
        except Exception as e:
            print(f"   ⚠️ Erreur correction qualité: {e} - utilisation données brutes")
            results_corriges = results_by_theme
        
        # 🤖 ÉTAPE 2: Validation IA sur données corrigées
        validated_results = {}
        total_results = 0
        current_result = 0
        
        # Comptage total et préparation des résultats
        for theme, donnees_thematique in results_corriges.items():
            if isinstance(donnees_thematique, dict):
                extraits = donnees_thematique.get('extraits_textuels', [])
                if isinstance(extraits, list):
                    total_results += len(extraits)
        
        print(f"   📊 {total_results} extraits de qualité à valider par l'IA")
        
        for theme, donnees_thematique in results_corriges.items():
            validated_results[theme] = []
            
            if isinstance(donnees_thematique, dict):
                extraits = donnees_thematique.get('extraits_textuels', [])
                qualite_globale = donnees_thematique.get('qualite_score', 'INCONNUE')
                
                print(f"   🎯 {theme} - Qualité: {qualite_globale}")
                
                if isinstance(extraits, list):
                    for extrait in extraits:
                        current_result += 1
                        print(f"     🔍 Validation {current_result}/{total_results}")
                        
                        # Les extraits sont maintenant garantis d'être au format dict
                        if isinstance(extrait, dict):
                            result_for_ai = extrait
                        else:
                            # Fallback au cas où
                            result_for_ai = {
                                'titre': str(extrait),
                                'description': '',
                                'url': ''
                            }
                        
                        # 🤖 Validation IA avec seuil adaptatif selon la qualité
                        try:
                            validation = self.validate_search_result(entreprise, result_for_ai, theme)
                            
                            # Seuil adaptatif selon la qualité des données
                            qualite_score = extrait.get('qualite_score', 0) if isinstance(extrait, dict) else 0
                            seuil_adaptatif = 0.3 if qualite_score > 0.5 else 0.5
                            
                            # Validation avec seuil adaptatif
                            if validation.is_relevant or validation.confidence_score > seuil_adaptatif:
                                enriched_result = result_for_ai.copy()
                                enriched_result.update({
                                    'ai_validated': True,
                                    'ai_confidence': validation.confidence_score,
                                    'ai_explanation': validation.explanation,
                                    'ai_extracted_info': validation.extracted_info,
                                    'ai_themes': validation.themes_detected,
                                    'validation_timestamp': datetime.now().isoformat(),
                                    'qualite_pre_ia': qualite_score,
                                    'seuil_utilise': seuil_adaptatif
                                })
                                validated_results[theme].append(enriched_result)
                                print(f"       ✅ Validé (confiance: {validation.confidence_score:.2f}, seuil: {seuil_adaptatif})")
                            else:
                                print(f"       ❌ Rejeté: {validation.explanation[:50]}...")
                                
                        except Exception as e:
                            print(f"       ⚠️ Erreur validation IA: {e}")
                            # En cas d'erreur IA, garder les extraits de bonne qualité
                            if isinstance(extrait, dict) and extrait.get('qualite_score', 0) > 0.6:
                                print(f"       🔄 Fallback: Gardé car bonne qualité")
                                extrait['ai_validated'] = False
                                extrait['ai_fallback'] = True
                                validated_results[theme].append(extrait)
                        
                        # Délai pour éviter les rate limits
                        time.sleep(0.1)  # Réduit pour plus de rapidité
        
        # 📊 Statistiques finales
        total_validated = sum(len(results) for results in validated_results.values())
        rejection_rate = (1 - total_validated / max(total_results, 1)) * 100
        
        print(f"   📊 Résultats finaux: {total_validated}/{total_results} validés ({rejection_rate:.1f}% rejetés)")
        
        # 🔄 Mode fallback si trop peu de résultats validés
        if total_validated == 0 and total_results > 0:
            print(f"   🔄 FALLBACK: IA trop stricte, récupération des meilleurs extraits")
            
            # Récupération des extraits de meilleure qualité sans validation IA
            for theme, donnees_thematique in results_corriges.items():
                if isinstance(donnees_thematique, dict):
                    extraits = donnees_thematique.get('extraits_textuels', [])
                    # Récupération des extraits avec qualité_score > 0.4
                    extraits_qualite = [
                        e for e in extraits 
                        if isinstance(e, dict) and e.get('qualite_score', 0) > 0.4
                    ]
                    
                    if extraits_qualite:
                        for extrait in extraits_qualite[:2]:  # Top 2 par thématique
                            extrait.update({
                                'ai_validated': False,
                                'ai_fallback_quality': True,
                                'fallback_reason': 'IA trop stricte - récupération par qualité',
                                'qualite_score': extrait.get('qualite_score', 0)
                            })
                            validated_results[theme].append(extrait)
                        
                        print(f"     🔄 {theme}: {len(extraits_qualite[:2])} extraits récupérés par qualité")
            
            # Nouveau décompte après fallback
            total_validated = sum(len(results) for results in validated_results.values())
            print(f"   📊 Après fallback: {total_validated} extraits récupérés")
        
        return validated_results
    
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