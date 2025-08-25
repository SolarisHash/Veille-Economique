#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de validation IA spécialisé pour éliminer les faux positifs
Analyse le contenu réel pour vérifier la pertinence thématique
"""

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
class ValidationContentResult:
    """Résultat de validation du contenu par l'IA"""
    is_relevant: bool
    confidence_score: float
    explanation: str
    theme_match: bool
    enterprise_match: bool
    content_summary: str
    decision_reason: str

class AIContentValidator:
    """Validateur IA spécialisé dans l'analyse de contenu pour éliminer les faux positifs"""
    
    def __init__(self, env_file_path: str = ".env"):
        """Initialisation avec clé API"""
        self.load_api_config(env_file_path)
        
        # Configuration du client OpenAI
        if self.is_azure:
            self.client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint
            )
        else:
            self.client = openai.OpenAI(api_key=self.api_key)
        
        # Configuration
        self.max_tokens = 600
        self.temperature = 0.1  # Très bas pour plus de consistance
        
        # Compteurs
        self.validations_count = 0
        self.false_positives_eliminated = 0
        
        print("🤖 Validateur IA de contenu initialisé - Anti-faux positifs")
    
    def load_api_config(self, env_file_path: str):
        """Chargement de la configuration API"""
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file_path)
            
            azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
            openai_api_key = os.getenv('OPENAI_API_KEY')
            
            if azure_api_key:
                self.is_azure = True
                self.api_key = azure_api_key
                self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
                self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
                self.model = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
            elif openai_api_key:
                self.is_azure = False
                self.api_key = openai_api_key
                self.model = os.getenv('AI_MODEL', 'gpt-4o-mini')
            else:
                raise ValueError("Aucune clé API trouvée dans .env")
                
        except Exception as e:
            print(f"❌ Erreur configuration API: {e}")
            raise
    
    def validate_content_relevance(self, content: str, entreprise: Dict, thematique: str) -> ValidationContentResult:
        """
        🎯 VALIDATION PRINCIPALE : Analyse le contenu pour éliminer les faux positifs
        
        Args:
            content: Le contenu textuel à analyser (titre + description + extrait)
            entreprise: Informations sur l'entreprise
            thematique: La thématique recherchée (recrutements, événements, etc.)
        
        Returns:
            ValidationContentResult avec la décision de l'IA
        """
        
        self.validations_count += 1
        nom_entreprise = entreprise.get('nom', 'Entreprise')
        commune = entreprise.get('commune', '')
        
        print(f"🔍 Validation IA #{self.validations_count}: {nom_entreprise} / {thematique}")
        
        try:
            # Construction du prompt spécialisé
            prompt = self._build_content_validation_prompt(content, nom_entreprise, commune, thematique)
            
            # Appel à l'IA
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_content_validation_system_prompt()
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
            
            # Parse de la réponse
            result_data = json.loads(response.choices[0].message.content)
            
            # Création du résultat
            validation_result = ValidationContentResult(
                is_relevant=result_data.get('is_relevant', False),
                confidence_score=result_data.get('confidence_score', 0.0),
                explanation=result_data.get('explanation', ''),
                theme_match=result_data.get('theme_match', False),
                enterprise_match=result_data.get('enterprise_match', False),
                content_summary=result_data.get('content_summary', ''),
                decision_reason=result_data.get('decision_reason', '')
            )
            
            # Logging du résultat
            if validation_result.is_relevant:
                print(f"   ✅ VALIDÉ (conf: {validation_result.confidence_score:.2f})")
                print(f"      💡 {validation_result.decision_reason}")
            else:
                print(f"   ❌ REJETÉ (conf: {validation_result.confidence_score:.2f})")
                print(f"      🚫 {validation_result.decision_reason}")
                self.false_positives_eliminated += 1
            
            return validation_result
            
        except Exception as e:
            print(f"   ⚠️ Erreur validation IA: {e}")
            
            # Fallback en cas d'erreur : validation basique
            return self._fallback_validation(content, nom_entreprise, thematique)
    
    def _get_content_validation_system_prompt(self) -> str:
        """Prompt système spécialisé pour la validation de contenu"""
        return """Tu es un expert en analyse de contenu spécialisé dans la détection des faux positifs.

🎯 MISSION CRITIQUE : Éliminer les faux positifs en analysant si le contenu parle VRAIMENT de l'entreprise et de la thématique demandée.

🔍 MÉTHODE D'ANALYSE :

1️⃣ LECTURE ATTENTIVE : Lis entièrement le contenu fourni
2️⃣ IDENTIFICATION ENTREPRISE : Vérifie si le contenu mentionne explicitement l'entreprise
3️⃣ VÉRIFICATION THÉMATIQUE : Vérifie si le contenu traite vraiment de la thématique
4️⃣ DÉTECTION FAUX POSITIFS : Identifie les contenus non pertinents

❌ FAUX POSITIFS TYPIQUES À REJETER :
- Dictionnaires, définitions, traductions (ex: WordReference, Larousse)
- Forums linguistiques ou cours de langue
- Pages Wikipedia générales
- Contenus qui mentionnent juste le nom sans contexte entrepreneurial
- Articles sur des homonymes (autres entreprises avec nom similaire)
- Contenus génériques sans lien réel avec l'entreprise

✅ VRAIS POSITIFS À GARDER :
- Articles de presse mentionnant spécifiquement l'entreprise
- Communiqués de l'entreprise sur la thématique
- Offres d'emploi de l'entreprise (pour thématique recrutements)
- Annonces d'événements de l'entreprise (pour thématique événements)
- Informations business réelles sur l'entreprise

🎯 RÈGLE D'OR : Si tu as le moindre doute sur la pertinence, REJETTE. Mieux vaut manquer un vrai résultat que laisser passer un faux positif.

Réponds TOUJOURS en JSON avec cette structure exacte :
{
  "is_relevant": true/false,
  "confidence_score": 0.0-1.0,
  "explanation": "Explication détaillée de ton analyse",
  "theme_match": true/false,
  "enterprise_match": true/false,
  "content_summary": "Résumé en 1 phrase de ce dont parle vraiment le contenu",
  "decision_reason": "Raison principale de ta décision (acceptation ou rejet)"
}"""

    def _build_content_validation_prompt(self, content: str, nom_entreprise: str, commune: str, thematique: str) -> str:
        """Construction du prompt de validation personnalisé"""
        
        # Nettoyage du contenu
        content_clean = self._clean_content_for_analysis(content)
        
        # Définitions des thématiques
        theme_definitions = {
            'recrutements': 'offres d\'emploi, embauches, recherche de personnel, CDI, CDD, stages',
            'evenements': 'événements, portes ouvertes, salons, conférences, inaugurations, manifestations',
            'innovations': 'nouveaux produits/services, R&D, technologies, brevets, modernisation',
            'vie_entreprise': 'développement, expansion, partenariats, ouvertures, restructurations',
            'exportations': 'ventes internationales, marchés étrangers, export',
            'aides_subventions': 'financements publics, subventions, aides gouvernementales',
            'fondation_sponsor': 'mécénat, sponsoring, actions caritatives, fondations'
        }
        
        theme_definition = theme_definitions.get(thematique, thematique)
        
        return f"""ANALYSE DE PERTINENCE DEMANDÉE

🏢 ENTREPRISE RECHERCHÉE :
Nom : "{nom_entreprise}"
Commune : {commune}

🎯 THÉMATIQUE RECHERCHÉE : {thematique}
Définition : {theme_definition}

📄 CONTENU À ANALYSER :
{content_clean}

❓ QUESTIONS D'ANALYSE :

1. Ce contenu mentionne-t-il explicitement l'entreprise "{nom_entreprise}" ?
2. Ce contenu parle-t-il réellement de {thematique} ({theme_definition}) ?
3. Y a-t-il un lien direct entre l'entreprise et la thématique dans ce contenu ?
4. Ce contenu est-il pertinent pour la veille économique de cette entreprise ?

🚨 ATTENTION AUX PIÈGES :
- Dictionnaires ou traductions mentionnant le mot (ex: "recrutement" dans un dictionnaire)
- Forums linguistiques (ex: WordReference)
- Homonymes (autres entreprises avec un nom similaire)
- Contenus génériques sans lien réel avec l'entreprise

ANALYSE ET RÉPONDS EN JSON :"""

    def _clean_content_for_analysis(self, content: str) -> str:
        """Nettoyage du contenu pour l'analyse IA"""
        if not content:
            return "Contenu vide"
        
        # Limitation de taille pour éviter les tokens excessifs
        if len(content) > 2000:
            content = content[:2000] + "...[contenu tronqué]"
        
        # Nettoyage basique
        content = re.sub(r'\s+', ' ', content)  # Espaces multiples
        content = content.strip()
        
        return content
    
    def _fallback_validation(self, content: str, nom_entreprise: str, thematique: str) -> ValidationContentResult:
        """Validation de fallback en cas d'erreur IA"""
        
        content_lower = content.lower()
        nom_lower = nom_entreprise.lower()
        
        # Vérifications basiques
        enterprise_mentioned = nom_lower in content_lower
        
        # Détection faux positifs évidents
        obvious_false_positives = [
            'wordreference.com', 'dictionary', 'dictionnaire', 'translation',
            'wikipedia.org', 'definition', 'cours de', 'grammaire'
        ]
        
        is_false_positive = any(fp in content_lower for fp in obvious_false_positives)
        
        # Décision
        is_relevant = enterprise_mentioned and not is_false_positive
        confidence = 0.3 if is_relevant else 0.1  # Faible confiance pour le fallback
        
        return ValidationContentResult(
            is_relevant=is_relevant,
            confidence_score=confidence,
            explanation=f"Validation fallback: entreprise {'mentionnée' if enterprise_mentioned else 'non mentionnée'}, faux positif {'détecté' if is_false_positive else 'non détecté'}",
            theme_match=enterprise_mentioned,
            enterprise_match=enterprise_mentioned,
            content_summary="Validation automatique en cas d'erreur IA",
            decision_reason="Fallback automatique - IA indisponible"
        )
    
    def batch_validate_contents(self, resultats_by_theme: Dict[str, List[Dict]], entreprise: Dict) -> Dict[str, List[Dict]]:
        """
        🔄 VALIDATION EN LOT : Valide tous les contenus d'une entreprise
        
        Args:
            resultats_by_theme: Résultats organisés par thématique
            entreprise: Informations sur l'entreprise
            
        Returns:
            Dict avec seulement les résultats validés par l'IA
        """
        
        nom_entreprise = entreprise.get('nom', 'N/A')
        print(f"\n🤖 Validation IA complète pour: {nom_entreprise}")
        
        validated_results = {}
        total_processed = 0
        total_validated = 0
        
        for theme, theme_data in resultats_by_theme.items():
            print(f"  🎯 Validation {theme}...")
            
            validated_results[theme] = []
            
            # Extraction des extraits à valider
            if isinstance(theme_data, dict):
                extraits = theme_data.get('extraits_textuels', [])
            else:
                extraits = theme_data if isinstance(theme_data, list) else []
            
            if not extraits:
                print(f"    ⚪ Aucun contenu à valider pour {theme}")
                continue
            
            # Validation de chaque extrait
            for i, extrait in enumerate(extraits):
                total_processed += 1
                
                # Construction du contenu à analyser
                content_to_analyze = self._extract_content_from_result(extrait)
                
                if len(content_to_analyze) < 20:  # Contenu trop court
                    print(f"    ⚠️ Contenu trop court ignoré")
                    continue
                
                # Validation IA
                try:
                    validation = self.validate_content_relevance(content_to_analyze, entreprise, theme)
                    
                    if validation.is_relevant:
                        # Enrichissement du résultat avec les infos IA
                        enriched_result = extrait.copy() if isinstance(extrait, dict) else {'contenu_original': extrait}
                        enriched_result.update({
                            'ai_validated': True,
                            'ai_confidence': validation.confidence_score,
                            'ai_explanation': validation.explanation,
                            'ai_decision_reason': validation.decision_reason,
                            'ai_content_summary': validation.content_summary,
                            'validation_timestamp': datetime.now().isoformat()
                        })
                        
                        validated_results[theme].append(enriched_result)
                        total_validated += 1
                    else:
                        print(f"    🚫 Extrait {i+1} rejeté par l'IA")
                
                except Exception as e:
                    print(f"    ❌ Erreur validation extrait {i+1}: {e}")
                    continue
                
                # Délai pour éviter rate limiting
                time.sleep(0.5)
            
            print(f"    📊 {theme}: {len(validated_results[theme])} extraits validés")
        
        # Statistiques finales
        print(f"\n📊 VALIDATION IA TERMINÉE:")
        print(f"   📄 Contenus analysés: {total_processed}")
        print(f"   ✅ Contenus validés: {total_validated}")
        print(f"   🚫 Faux positifs éliminés: {total_processed - total_validated}")
        print(f"   📈 Taux de validation: {(total_validated/total_processed*100):.1f}%" if total_processed > 0 else "   📈 Taux de validation: 0%")
        
        return validated_results
    
    def _extract_content_from_result(self, result) -> str:
        """Extraction du contenu textuel depuis un résultat"""
        
        if isinstance(result, str):
            return result
        
        if isinstance(result, dict):
            # Concaténation des champs textuels disponibles
            content_parts = []
            
            text_fields = ['titre', 'description', 'extrait_complet', 'contenu', 'texte']
            for field in text_fields:
                if field in result and result[field]:
                    content_parts.append(str(result[field]))
            
            return ' | '.join(content_parts) if content_parts else str(result)
        
        return str(result)
    
    def get_validation_stats(self) -> Dict:
        """Statistiques de validation"""
        return {
            'total_validations': self.validations_count,
            'false_positives_eliminated': self.false_positives_eliminated,
            'false_positive_rate': (self.false_positives_eliminated / max(self.validations_count, 1)) * 100,
            'efficiency': f"{self.false_positives_eliminated} faux positifs éliminés sur {self.validations_count} analyses"
        }

# INTÉGRATION DANS VOTRE SYSTÈME EXISTANT
def integrate_content_validator_in_main():
    """
    Code d'intégration dans votre main.py ou analyseur_thematiques.py
    """
    
    integration_code = '''
# Dans votre analyseur_thematiques.py ou main.py :

from ai_content_validator import AIContentValidator

class AnalyseurThematiques:
    def __init__(self, thematiques_config):
        # Votre code existant...
        
        # ✅ AJOUT du validateur de contenu IA
        try:
            self.content_validator = AIContentValidator()
            self.use_ai_validation = True
            print("✅ Validateur IA de contenu activé - Anti-faux positifs")
        except Exception as e:
            print(f"⚠️ Validateur IA non disponible: {e}")
            self.use_ai_validation = False
    
    def analyser_resultats(self, resultats_bruts: List[Dict], logger=None) -> List[Dict]:
        """Version avec validation IA anti-faux positifs"""
        
        entreprises_enrichies = []
        
        for i, resultat in enumerate(resultats_bruts, 1):
            entreprise = resultat.get('entreprise', {})
            nom_entreprise = entreprise.get('nom', f'Entreprise_{i}')
            
            print(f"  📊 Analyse {i}/{len(resultats_bruts)}: {nom_entreprise}")
            
            donnees_thematiques = resultat.get('donnees_thematiques', {})
            
            if donnees_thematiques and self.use_ai_validation:
                # ✅ VALIDATION IA ANTI-FAUX POSITIFS
                print(f"    🤖 Validation IA des contenus...")
                
                try:
                    validated_data = self.content_validator.batch_validate_contents(
                        donnees_thematiques, entreprise
                    )
                    
                    # Remplacer les données par les données validées
                    donnees_thematiques = validated_data
                    
                    # Stats de validation
                    stats = self.content_validator.get_validation_stats()
                    if i % 10 == 0:  # Afficher les stats tous les 10
                        print(f"    📊 Stats IA: {stats['efficiency']}")
                        
                except Exception as e:
                    print(f"    ⚠️ Erreur validation IA: {e}")
                    # Continuer avec les données non validées
            
            # Suite de votre analyse normale...
            entreprise_analysee = self._analyser_entreprise({
                'entreprise': entreprise,
                'donnees_thematiques': donnees_thematiques  # Données validées IA
            })
            
            entreprises_enrichies.append(entreprise_analysee)
        
        return entreprises_enrichies
'''
    
    return integration_code

if __name__ == "__main__":
    print("🧪 Test du Validateur IA de Contenu")
    
    try:
        validator = AIContentValidator()
        
        # Test avec un vrai faux positif
        faux_positif = {
            'titre': 'Recrutement - Définition et synonymes',
            'description': 'Définition du mot recrutement dans le dictionnaire français. Synonymes et antonymes.',
            'url': 'https://www.larousse.fr/dictionnaires/francais/recrutement'
        }
        
        entreprise_test = {
            'nom': 'CARREFOUR',
            'commune': 'Boulogne-Billancourt'
        }
        
        content = f"{faux_positif['titre']} - {faux_positif['description']}"
        
        result = validator.validate_content_relevance(content, entreprise_test, 'recrutements')
        
        print(f"\n✅ Test terminé:")
        print(f"   Pertinent: {result.is_relevant}")
        print(f"   Confiance: {result.confidence_score}")
        print(f"   Raison: {result.decision_reason}")
        
        # Test avec un vrai positif
        vrai_positif = {
            'titre': 'CARREFOUR recrute 50 personnes en CDI',
            'description': 'Le groupe Carrefour annonce le recrutement de 50 collaborateurs en CDI pour son magasin de Boulogne-Billancourt',
            'url': 'https://www.carrefour.fr/recrutement'
        }
        
        content2 = f"{vrai_positif['titre']} - {vrai_positif['description']}"
        result2 = validator.validate_content_relevance(content2, entreprise_test, 'recrutements')
        
        print(f"\n✅ Test vrai positif:")
        print(f"   Pertinent: {result2.is_relevant}")
        print(f"   Confiance: {result2.confidence_score}")
        print(f"   Raison: {result2.decision_reason}")
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")