#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intégration LinkedIn pour le système de veille économique
Module pour automatiser la collecte des posts LinkedIn via Tampermonkey
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
import subprocess
import webbrowser
from pathlib import Path
import os

class LinkedInVeilleIntegration:
    """
    Intégration LinkedIn pour la veille économique
    Utilise Tampermonkey + API pour automatiser la collecte
    """
    
    def __init__(self, webhook_url: str = None):
        """Initialisation avec webhook pour recevoir les données"""
        self.webhook_url = webhook_url or "http://localhost:8080/linkedin-webhook"  # Serveur local
        self.linkedin_data = {}
        self.queue_urls = []
        
        # Dossiers de sortie
        Path("data/linkedin").mkdir(parents=True, exist_ok=True)
        Path("data/linkedin/queue").mkdir(parents=True, exist_ok=True)
        Path("data/linkedin/results").mkdir(parents=True, exist_ok=True)
        
        print("🔗 LinkedInVeilleIntegration initialisé")
        print(f"📡 Webhook: {self.webhook_url}")
    
    def rechercher_profils_linkedin_entreprises(self, entreprises: List[Dict]) -> Dict:
        """
        Recherche les profils LinkedIn des entreprises
        Utilise le système de recherche existant
        """
        try:
            print("🔍 Recherche des profils LinkedIn pour les entreprises")
            
            resultats_linkedin = {}
            
            for i, entreprise in enumerate(entreprises, 1):
                print(f"\n🏢 Entreprise {i}/{len(entreprises)}: {entreprise['nom']}")
                
                # Recherche spécifique LinkedIn
                urls_linkedin = self._rechercher_linkedin_entreprise(entreprise)
                
                if urls_linkedin:
                    resultats_linkedin[entreprise['nom']] = {
                        'entreprise_data': entreprise,
                        'linkedin_urls': urls_linkedin,
                        'status': 'found',
                        'priorite': self._evaluer_priorite_entreprise(entreprise)
                    }
                    print(f"   ✅ {len(urls_linkedin)} URL(s) LinkedIn trouvée(s)")
                else:
                    print(f"   ❌ Aucun profil LinkedIn trouvé")
                
                time.sleep(2)  # Délai entre recherches
            
            return resultats_linkedin
            
        except Exception as e:
            print(f"❌ Erreur recherche LinkedIn: {e}")
            return {}
    
    def _rechercher_linkedin_entreprise(self, entreprise: Dict) -> List[str]:
        """Recherche LinkedIn spécifique pour une entreprise"""
        try:
            from scripts.recherche_web import RechercheWeb  # Import de votre module existant
            
            recherche = RechercheWeb(periode_recherche=None)
            nom_entreprise = entreprise['nom']
            
            # Requêtes spécialisées LinkedIn
            requetes_linkedin = [
                f'"{nom_entreprise}" site:linkedin.com/company',
                f'"{nom_entreprise}" site:linkedin.com/in',  # Parfois des dirigeants
                f'{nom_entreprise} linkedin entreprise',
            ]
            
            urls_trouvees = []
            
            for requete in requetes_linkedin:
                try:
                    print(f"      🔎 Requête: {requete}")
                    resultats = recherche._rechercher_moteur(requete)
                    
                    if resultats:
                        for resultat in resultats:
                            url = resultat.get('url', '')
                            if self._valider_url_linkedin(url, nom_entreprise):
                                urls_trouvees.append(url)
                                print(f"      ✅ URL validée: {url}")
                    
                    time.sleep(3)  # Délai anti-spam
                    
                except Exception as e:
                    print(f"      ⚠️ Erreur requête: {e}")
                    continue
            
            # Dédupliquation
            return list(set(urls_trouvees))
            
        except Exception as e:
            print(f"❌ Erreur recherche LinkedIn entreprise: {e}")
            return []
    
    def _valider_url_linkedin(self, url: str, nom_entreprise: str) -> bool:
        """Validation que l'URL LinkedIn correspond bien à l'entreprise"""
        if not url or 'linkedin.com' not in url:
            return False
        
        # Validation pour pages entreprise
        if '/company/' in url:
            # Vérifier que le nom de l'entreprise est dans l'URL ou proche
            url_lower = url.lower()
            nom_parts = nom_entreprise.lower().replace(' ', '-').replace('.', '')
            
            # Correspondance approximative
            if any(part in url_lower for part in nom_parts.split('-') if len(part) > 3):
                return True
        
        # Validation pour profils dirigeants (bonus)
        elif '/in/' in url:
            return True  # À valider manuellement plus tard
        
        return False
    
    def _evaluer_priorite_entreprise(self, entreprise: Dict) -> int:
        """Évalue la priorité de l'entreprise pour la collecte LinkedIn"""
        score = 0
        
        # Critères de priorisation
        secteur = entreprise.get('secteur_naf', '').lower()
        
        # Secteurs prioritaires pour LinkedIn
        secteurs_prioritaires = [
            'conseil', 'informatique', 'technologie', 'innovation',
            'marketing', 'communication', 'formation', 'finance'
        ]
        
        if any(s in secteur for s in secteurs_prioritaires):
            score += 3
        
        # Site web présent = plus de chances d'avoir LinkedIn actif
        if entreprise.get('site_web'):
            score += 2
        
        # Taille approximative (par SIRET/données)
        if len(str(entreprise.get('siret', ''))) == 14:
            score += 1
        
        return min(score, 5)  # Maximum 5
    
    def generer_queue_linkedin(self, resultats_linkedin: Dict, max_urls: int = 10) -> str:
        """
        Génère une queue de traitement pour le script Tampermonkey
        Priorise les entreprises les plus importantes
        """
        try:
            print(f"📋 Génération queue LinkedIn (max {max_urls} URLs)")
            
            # Tri par priorité
            entreprises_triees = sorted(
                resultats_linkedin.items(),
                key=lambda x: x[1]['priorite'],
                reverse=True
            )
            
            queue_data = {
                'timestamp': datetime.now().isoformat(),
                'total_entreprises': len(entreprises_triees),
                'max_urls': max_urls,
                'webhook_url': self.webhook_url,
                'urls_to_process': []
            }
            
            urls_ajoutees = 0
            
            for nom_entreprise, data in entreprises_triees:
                if urls_ajoutees >= max_urls:
                    break
                
                for url in data['linkedin_urls'][:2]:  # Max 2 URLs par entreprise
                    if urls_ajoutees >= max_urls:
                        break
                    
                    queue_data['urls_to_process'].append({
                        'url': url,
                        'entreprise': nom_entreprise,
                        'siret': data['entreprise_data'].get('siret', ''),
                        'commune': data['entreprise_data'].get('commune', ''),
                        'priorite': data['priorite'],
                        'status': 'pending'
                    })
                    
                    urls_ajoutees += 1
                    print(f"   ✅ Ajouté: {nom_entreprise} - {url}")
            
            # Sauvegarde de la queue
            queue_file = f"data/linkedin/queue/queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, ensure_ascii=False, indent=2)
            
            print(f"📄 Queue sauvée: {queue_file}")
            print(f"🎯 {urls_ajoutees} URLs à traiter")
            
            return queue_file
            
        except Exception as e:
            print(f"❌ Erreur génération queue: {e}")
            return ""
    
    def generer_script_tampermonkey_adapte(self, queue_file: str) -> str:
        """
        Génère le script Tampermonkey adapté pour les posts d'entreprises
        Basé sur votre script existant mais pour les pages /company/
        """
        try:
            # Lecture de la queue
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue_data = json.load(f)
            
            webhook_url = queue_data['webhook_url']
            
            script_content = f'''// ==UserScript==
// @name         LinkedIn Posts Scraper - Veille Économique
// @namespace    http://tampermonkey.net/
// @version      2024-01-01
// @description  Extraction automatique posts LinkedIn pour veille économique
// @author       VeilleEco
// @match        https://www.linkedin.com/company/*
// @match        https://www.linkedin.com/company/*/posts/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=linkedin.com
// @grant        GM_xmlhttpRequest
// ==/UserScript==

(async function() {{
    'use strict';
    
    console.log("🤖 LinkedIn Posts Scraper - Veille Économique activé");
    
    const WEBHOOK_URL = "{webhook_url}";
    const MAX_POSTS = 10;
    const QUEUE_URLS = {json.dumps([item['url'] for item in queue_data['urls_to_process']])};
    
    let postsExtracted = [];
    let currentCompanyData = null;
    
    // Attendre le chargement de la page
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Détection automatique si on est sur une page de la queue
    function isTargetPage() {{
        const currentUrl = window.location.href;
        return QUEUE_URLS.some(url => {{
            const cleanCurrentUrl = currentUrl.split('?')[0].split('#')[0];
            const cleanTargetUrl = url.split('?')[0].split('#')[0];
            return cleanCurrentUrl.includes(cleanTargetUrl.replace('https://www.linkedin.com', ''));
        }});
    }}
    
    // Extraction des informations de l'entreprise
    function extractCompanyInfo() {{
        const companyName = document.querySelector('h1[data-test-id="org-name"]')?.innerText?.trim() || 
                           document.querySelector('.org-top-card-summary__title')?.innerText?.trim() || 
                           'Entreprise non identifiée';
        
        const followersElement = document.querySelector('.org-top-card-summary__follower-count') ||
                                document.querySelector('[data-test-id="follower-count"]');
        const followers = followersElement?.innerText?.trim() || '0';
        
        const industryElement = document.querySelector('.org-top-card-summary__industry') ||
                               document.querySelector('[data-test-id="industry"]');
        const industry = industryElement?.innerText?.trim() || 'Non spécifié';
        
        return {{
            name: companyName,
            followers: followers,
            industry: industry,
            url: window.location.href,
            extraction_date: new Date().toISOString()
        }};
    }}
    
    // Extraction des posts
    function extractPosts() {{
        console.log("📊 Extraction des posts...");
        
        const posts = document.querySelectorAll('.feed-shared-update-v2, [data-test-id="post"]');
        console.log(`Nombre de posts trouvés: ${{posts.length}}`);
        
        const extractedPosts = [];
        
        for (let i = 0; i < Math.min(posts.length, MAX_POSTS); i++) {{
            try {{
                const post = posts[i];
                
                // Texte du post
                const textElement = post.querySelector('.feed-shared-text, .update-components-text') ||
                                   post.querySelector('.feed-shared-update-v2__description-wrapper');
                const postText = textElement?.innerText?.trim() || 'Texte non accessible';
                
                // Date de publication
                const dateElement = post.querySelector('.feed-shared-actor__sub-description, .update-components-actor__sub-description');
                const publishDate = dateElement?.innerText?.trim() || 'Date non accessible';
                
                // Interactions
                const likeElement = post.querySelector('.social-counts-reactions__count');
                const likeCount = likeElement?.innerText?.trim() || '0';
                
                // Type de contenu
                let contentType = 'text';
                if (post.querySelector('.feed-shared-image, .update-components-image')) {{
                    contentType = 'image';
                }} else if (post.querySelector('.feed-shared-video, .update-components-video')) {{
                    contentType = 'video';
                }} else if (post.querySelector('.feed-shared-article, .update-components-article')) {{
                    contentType = 'article';
                }}
                
                // URL du post
                const linkElement = post.querySelector('a[href*="/feed/update/"]');
                const postUrl = linkElement?.href || '';
                
                const postData = {{
                    post_number: i + 1,
                    text: postText.substring(0, 500), // Limitation pour éviter les gros volumes
                    publish_date: publishDate,
                    like_count: likeCount,
                    content_type: contentType,
                    post_url: postUrl,
                    extracted_at: new Date().toISOString()
                }};
                
                extractedPosts.push(postData);
                console.log(`✅ Post ${{i+1}} extrait: ${{postText.substring(0, 50)}}...`);
                
            }} catch (error) {{
                console.log(`❌ Erreur extraction post ${{i+1}}: ${{error}}`);
            }}
        }}
        
        return extractedPosts;
    }}
    
    // Envoi des données au webhook
    function sendToWebhook(data) {{
        console.log("📡 Envoi vers webhook...");
        
        GM_xmlhttpRequest({{
            method: 'POST',
            url: WEBHOOK_URL,
            headers: {{
                'Content-Type': 'application/json'
            }},
            data: JSON.stringify(data),
            onload: function(response) {{
                console.log("✅ Données envoyées avec succès");
                displaySuccessMessage(data.posts.length);
            }},
            onerror: function(error) {{
                console.log("❌ Erreur envoi webhook:", error);
                copyToClipboard(JSON.stringify(data, null, 2));
            }}
        }});
    }}
    
    // Message de succès
    function displaySuccessMessage(postCount) {{
        const message = document.createElement('div');
        message.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            background: #28a745; color: white; padding: 15px 20px;
            border-radius: 5px; font-family: Arial; font-size: 14px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;
        message.innerHTML = `✅ ${{postCount}} posts LinkedIn extraits et envoyés !`;
        document.body.appendChild(message);
        
        setTimeout(() => message.remove(), 5000);
    }}
    
    // Copie de secours
    function copyToClipboard(text) {{
        navigator.clipboard.writeText(text).then(() => {{
            console.log("📋 Données copiées dans le presse-papiers (secours)");
        }});
    }}
    
    // Création du bouton d'extraction
    function createExtractButton() {{
        const button = document.createElement('button');
        button.innerHTML = '📊 Extraire Posts LinkedIn';
        button.style.cssText = `
            position: fixed; bottom: 20px; left: 20px; z-index: 9999;
            padding: 12px 20px; border: none; border-radius: 5px;
            background: #0077b5; color: white; cursor: pointer;
            font-family: Arial; font-size: 14px; font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: background 0.3s;
        `;
        
        button.addEventListener('click', async () => {{
            button.disabled = true;
            button.innerHTML = '⏳ Extraction en cours...';
            
            try {{
                // Navigation vers les posts si nécessaire
                if (!window.location.href.includes('/posts/')) {{
                    const postsUrl = window.location.href.replace(/\/$/, '') + '/posts/';
                    window.location.href = postsUrl;
                    return;
                }}
                
                // Attendre le chargement des posts
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Scroll pour charger plus de posts
                for (let i = 0; i < 3; i++) {{
                    window.scrollTo(0, document.body.scrollHeight);
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }}
                
                // Extraction
                const companyInfo = extractCompanyInfo();
                const posts = extractPosts();
                
                const data = {{
                    company: companyInfo,
                    posts: posts,
                    total_posts: posts.length,
                    extraction_metadata: {{
                        timestamp: new Date().toISOString(),
                        url: window.location.href,
                        user_agent: navigator.userAgent
                    }}
                }};
                
                // Envoi
                sendToWebhook(data);
                
            }} catch (error) {{
                console.log("❌ Erreur générale:", error);
            }} finally {{
                button.disabled = false;
                button.innerHTML = '📊 Extraire Posts LinkedIn';
            }}
        }});
        
        document.body.appendChild(button);
        console.log("🔧 Bouton d'extraction ajouté");
    }}
    
    // Auto-activation sur les pages ciblées
    if (isTargetPage()) {{
        console.log("🎯 Page ciblée détectée - Activation automatique");
        
        // Message d'information
        const info = document.createElement('div');
        info.style.cssText = `
            position: fixed; top: 20px; left: 20px; z-index: 10000;
            background: #ffc107; color: #333; padding: 10px 15px;
            border-radius: 5px; font-family: Arial; font-size: 12px;
            max-width: 300px;
        `;
        info.innerHTML = '🤖 Script de veille économique actif<br>Cliquez sur le bouton pour extraire les posts';
        document.body.appendChild(info);
        
        setTimeout(() => info.remove(), 8000);
    }}
    
    // Création du bouton dans tous les cas
    createExtractButton();
    
}})();'''
            
            # Sauvegarde du script
            script_file = f"data/linkedin/tampermonkey_linkedin_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.user.js"
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"📄 Script Tampermonkey généré: {script_file}")
            return script_file
            
        except Exception as e:
            print(f"❌ Erreur génération script: {e}")
            return ""
    
    def demarrer_serveur_webhook(self, port: int = 8080):
        """
        Démarre un serveur webhook local pour recevoir les données
        Serveur simple avec Flask
        """
        try:
            from flask import Flask, request, jsonify
            
            app = Flask(__name__)
            
            @app.route('/linkedin-webhook', methods=['POST'])
            def receive_linkedin_data():
                try:
                    data = request.json
                    
                    # Sauvegarde des données reçues
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    company_name = data.get('company', {}).get('name', 'unknown').replace(' ', '_')
                    filename = f"data/linkedin/results/linkedin_{company_name}_{timestamp}.json"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ Données LinkedIn reçues: {filename}")
                    print(f"🏢 Entreprise: {data.get('company', {}).get('name')}")
                    print(f"📊 Posts: {len(data.get('posts', []))}")
                    
                    return jsonify({"status": "success", "message": "Données reçues"})
                    
                except Exception as e:
                    print(f"❌ Erreur webhook: {e}")
                    return jsonify({"status": "error", "message": str(e)}), 500
            
            @app.route('/status', methods=['GET'])
            def status():
                return jsonify({"status": "running", "timestamp": datetime.now().isoformat()})
            
            print(f"🚀 Serveur webhook démarré sur http://localhost:{port}/linkedin-webhook")
            app.run(host='localhost', port=port, debug=False)
            
        except ImportError:
            print("❌ Flask non installé. Installez avec: pip install flask")
            return False
        except Exception as e:
            print(f"❌ Erreur serveur webhook: {e}")
            return False
    
    def workflow_complet(self, entreprises: List[Dict], max_urls: int = 5):
        """
        Workflow complet d'intégration LinkedIn
        1. Recherche des profils LinkedIn
        2. Génération de la queue
        3. Création du script Tampermonkey
        4. Instructions pour l'utilisateur
        """
        try:
            print("🚀 WORKFLOW COMPLET - INTÉGRATION LINKEDIN")
            print("=" * 60)
            
            # 1. Recherche des profils LinkedIn
            print("\n📍 ÉTAPE 1/4 - Recherche profils LinkedIn")
            resultats_linkedin = self.rechercher_profils_linkedin_entreprises(entreprises)
            
            if not resultats_linkedin:
                print("❌ Aucun profil LinkedIn trouvé")
                return False
            
            print(f"✅ {len(resultats_linkedin)} entreprises avec LinkedIn trouvées")
            
            # 2. Génération de la queue
            print("\n📍 ÉTAPE 2/4 - Génération queue de traitement")
            queue_file = self.generer_queue_linkedin(resultats_linkedin, max_urls)
            
            if not queue_file:
                print("❌ Erreur génération queue")
                return False
            
            # 3. Génération du script Tampermonkey
            print("\n📍 ÉTAPE 3/4 - Génération script Tampermonkey")
            script_file = self.generer_script_tampermonkey_adapte(queue_file)
            
            if not script_file:
                print("❌ Erreur génération script")
                return False
            
            # 4. Instructions utilisateur
            print("\n📍 ÉTAPE 4/4 - Instructions d'utilisation")
            self._afficher_instructions(queue_file, script_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur workflow complet: {e}")
            return False
    
    def _afficher_instructions(self, queue_file: str, script_file: str):
        """Affiche les instructions pour l'utilisateur"""
        print("📋 INSTRUCTIONS D'UTILISATION:")
        print("=" * 50)
        
        print("1️⃣ INSTALLATION SCRIPT TAMPERMONKEY:")
        print(f"   📄 Fichier généré: {script_file}")
        print("   • Ouvrez Tampermonkey dans Chrome/Firefox")
        print("   • Cliquez 'Créer un nouveau script'")
        print(f"   • Copiez-collez le contenu de {script_file}")
        print("   • Sauvegardez le script")
        
        print("\n2️⃣ DÉMARRAGE SERVEUR WEBHOOK:")
        print("   • Ouvrez un terminal")
        print("   • Lancez: python -m votre_module.demarrer_serveur_webhook()")
        print("   • Le serveur écoute sur http://localhost:8080")
        
        print("\n3️⃣ NAVIGATION LINKEDIN:")
        print("   • Connectez-vous à LinkedIn")
        print("   • Visitez les pages suivantes (le script détecte automatiquement):")
        
        # Lecture de la queue pour afficher les URLs
        try:
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue_data = json.load(f)
                
            for i, item in enumerate(queue_data['urls_to_process'][:5], 1):
                print(f"   {i}. {item['entreprise']}: {item['url']}")
                
            if len(queue_data['urls_to_process']) > 5:
                print(f"   ... et {len(queue_data['urls_to_process']) - 5} autres")
        except:
            pass
        
        print("\n4️⃣ EXTRACTION:")
        print("   • Sur chaque page, cliquez le bouton '📊 Extraire Posts LinkedIn'")
        print("   • Attendez la confirmation de succès")
        print("   • Les données sont automatiquement sauvées")
        
        print("\n5️⃣ RÉSULTATS:")
        print("   📁 Dossier de sortie: data/linkedin/results/")
        print("   📊 Format: JSON avec posts et métadonnées")
        
        print("\n💡 CONSEILS:")
        print("   • Naviguez manuellement (plus sûr)")
        print("   • Pausez 10-20 secondes entre les pages")
        print("   • Vérifiez les résultats après chaque extraction")
        
        print("\n🎯 INTÉGRATION AVEC VOTRE VEILLE:")
        print("   • Les données JSON peuvent être importées dans vos rapports")
        print("   • Format compatible avec votre analyseur thématique")
        print("   • Enrichissement automatique des profils d'entreprises")

# Fonction d'utilisation dans votre système principal
def integrer_linkedin_veille(entreprises: List[Dict], max_entreprises: int = 5):
    """
    Fonction d'intégration dans votre système principal
    À appeler depuis main.py ou un module dédié
    """
    try:
        print("🔗 INTÉGRATION LINKEDIN - VEILLE ÉCONOMIQUE")
        
        # Initialisation
        linkedin_integration = LinkedInVeilleIntegration()
        
        # Limitation pour test
        entreprises_limitees = entreprises[:max_entreprises]
        print(f"🎯 Traitement de {len(entreprises_limitees)} entreprises")
        
        # Workflow complet
        success = linkedin_integration.workflow_complet(entreprises_limitees)
        
        if success:
            print("\n✅ INTÉGRATION LINKEDIN PRÊTE !")
            print("Suivez les instructions ci-dessus pour collecter les posts LinkedIn.")
            return True
        else:
            print("\n❌ Échec de l'intégration LinkedIn")
            return False
            
    except Exception as e:
        print(f"❌ Erreur intégration LinkedIn: {e}")
        return False

# Serveur webhook standalone
def demarrer_serveur_webhook_standalone():
    """Serveur webhook à lancer séparément"""
    integration = LinkedInVeilleIntegration()
    integration.demarrer_serveur_webhook()