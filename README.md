v# 🏢 Système de Veille Économique Territoriale

## 📋 Description

Système automatisé de veille économique pour analyser les activités des entreprises sur 20 communes selon 7 thématiques prédéfinies.

## 🎯 Thématiques analysées

- **Événements** : portes ouvertes, conférences, rencontres
- **Recrutements** : offres d'emploi, embauches, carrières
- **Vie de l'entreprise** : développement, partenariats, implantations
- **Innovations** : nouveaux produits/services, R&D
- **Exportations** : développement international, marchés étrangers
- **Aides & subventions** : financements publics, soutiens
- **Fondation & sponsor** : mécénat, actions sociales

## 🚀 Installation

### 1. Prérequis
```bash
Python 3.8+
pip (gestionnaire de paquets Python)
```

### 2. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 3. Structure des dossiers
```
Projet_Veille_Economique/
├── data/
│   ├── input/          # Fichiers Excel d'entrée
│   ├── output/         # Rapports générés
│   └── cache/          # Cache des recherches
├── scripts/            # Code source
├── config/             # Configuration
├── logs/               # Logs d'exécution
└── README.md
```

## 📊 Usage

### Phase 1 : Test avec échantillon (10 entreprises)

1. **Placer votre fichier Excel** dans `data/input/entreprises_base.xlsx`
   
2. **Lancement rapide :**
   ```bash
   python run_echantillon.py
   ```

3. **Ou lancement manuel :**
   ```bash
   python main.py
   ```

### Phase 2 : Analyse complète (1000+ entreprises)

Après validation de l'échantillon, modifier `main.py` pour activer le mode complet.

## 📁 Format du fichier Excel requis

Votre fichier Excel doit contenir ces colonnes :

- `SIRET`
- `Nom courant/Dénomination`
- `Enseigne`
- `Adresse - complément d'adresse`
- `Adresse - numéro et voie`
- `Adresse - distribution postale`
- `Adresse - CP et commune`
- `Commune`
- `Code NAF`
- `Libellé NAF`
- `Genre`
- `Nom`
- `Prénom`
- `Site Web établissement`
- `Dirigeant`

## 📊 Résultats générés

### 1. Fichier Excel enrichi
- Données originales + analyse thématique
- Scores de pertinence par thématique
- Niveau de confiance
- Sources d'information

### 2. Rapport HTML interactif
- Visualisations graphiques
- Statistiques par commune
- Entreprises les plus actives

### 3. Export JSON
- Données structurées pour intégration
- API ou applications tierces

### 4. Alertes ciblées
- Notifications par commune
- Priorités selon l'activité

## ⚙️ Configuration

### Fichier `config/parametres.yaml`

```yaml
# Paramètres de traitement
traitement:
  echantillon_test: 10
  periode_recherche_mois: 6
  timeout_requetes_sec: 10

# Ajustement des mots-clés par thématique
mots_cles:
  recrutements:
    - "recrutement"
    - "embauche"
    - "offre emploi"
    # ... personnalisables
```

## 🔧 Architecture technique

### Modules principaux

1. **`main.py`** : Orchestrateur principal
2. **`extracteur_donnees.py`** : Traitement fichier Excel
3. **`recherche_web.py`** : Moteur de recherche web
4. **`analyseur_thematiques.py`** : Classification thématique
5. **`generateur_rapports.py`** : Génération des rapports

### Flux de traitement

```
Excel → Extraction → Recherche Web → Analyse → Rapports
```

## 📈 Exemple de résultats

### Entreprise analysée
- **Nom** : Entreprise XYZ
- **Commune** : Ville ABC
- **Score global** : 0.85
- **Thématiques détectées** :
  - Recrutements : 0.90 (Élevé)
  - Innovations : 0.75 (Moyen)
  - Vie entreprise : 0.60 (Moyen)

## 🔄 Automatisation future

Le système est conçu pour l'automatisation :
- Exécution hebdomadaire
- Détection de nouveautés
- Alertes temps réel
- Intégration avec systèmes existants

## 🛠️ Maintenance

### Nettoyage du cache
```bash
# Nettoyage automatique des fichiers > 24h
# Configurable dans parametres.yaml
```

### Logs
```bash
# Consultation des logs
tail -f logs/veille_economique.log
```

## 📞 Support

Pour toute question ou amélioration :
1. Consultez les logs d'erreur
2. Vérifiez la configuration
3. Testez avec l'échantillon avant l'analyse complète

## 🚧 Roadmap

- [ ] Intégration APIs réseaux sociaux
- [ ] Analyse sentiment des mentions
- [ ] Dashboard temps réel
- [ ] Notifications automatiques
- [ ] Export PowerBI/Tableau

## 🔒 Sécurité & Confidentialité

- Cache local uniquement
- Respect des robots.txt
- Pas de stockage permanent des données web
- Conformité RGPD pour les données entreprises

---

**Version** : 1.0.0  
**Dernière mise à jour** : Juillet 2025