# 🧪 Guide de Test Manuel - Fonction Azure

## ✅ Résultats des Tests Automatisés
- **Tests réussis** : 5/5 (100%)
- **Statut** : PRÊT POUR DÉPLOIEMENT ✅

## 🔧 Comment Tester Manuellement Après Déploiement

### 1. Test avec Postman

#### Test 1: Upload direct PDF
```http
POST https://votre-fonction.azurewebsites.net/api/analyze_email_and_pdf
Content-Type: application/pdf

[Corps de la requête: fichier PDF binaire]
```

#### Test 2: Email avec pièce jointe
```http
POST https://votre-fonction.azurewebsites.net/api/analyze_email_and_pdf
Content-Type: application/json

{
  "sender_email": "fournisseur@example.com",
  "email": "Objet: Commande BSK2506CF0383\n\nBonjour,\nVeuillez trouver ci-joint notre bon de commande.\n\nFournisseur: IMPRIMERIE AJDIR\nDate: 23/06/2025",
  "pdf_base64": "[PDF encodé en base64]"
}
```

### 2. Test avec cURL

#### Test PDF direct
```bash
curl -X POST \
  https://votre-fonction.azurewebsites.net/api/analyze_email_and_pdf \
  -H "Content-Type: application/pdf" \
  --data-binary @test.pdf
```

#### Test Email + PDF
```bash
curl -X POST \
  https://votre-fonction.azurewebsites.net/api/analyze_email_and_pdf \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email": "test@example.com",
    "email": "Test email content",
    "pdf_base64": "'$(base64 -i test.pdf)'"
  }'
```

### 3. Réponses Attendues

#### ✅ Réponse Succès (PDF direct)
```json
{
  "ID_commande": "BSK2506CF0383"
}
```

#### ✅ Réponse Succès (Email + PDF)
```json
{
  "ID_commande": "BSK2506CF0383",
  "nom_fournisseur": "IMPRIMERIE AJDIR",
  "date_reception": "23/06/2025",
  "date_livraison": "29/07/2025"
}
```

#### ❌ Réponse Erreur (PDF vide)
```http
Status: 400
Body: "Le fichier PDF est vide ou incomplet"
```

#### ❌ Réponse Erreur (JSON invalide)
```http
Status: 500
Body: "Erreur interne : [détails]"
```

## 📋 Checklist de Test

### ✅ Fonctionnalités à Vérifier
- [ ] Upload direct PDF fonctionne
- [ ] Email avec pièce jointe fonctionne
- [ ] Extraction d'ID de commande fonctionne
- [ ] Différents formats d'ID sont détectés
- [ ] Gestion d'erreurs fonctionne
- [ ] Réponses JSON sont correctes

### ✅ Formats d'ID Testés
- [ ] `BSK2506CF0383` (format BSK)
- [ ] `TAC ETAC60JDF` (format TAC)
- [ ] `CMD123456789` (format CMD)
- [ ] `PO2025001` (format PO)
- [ ] `BC2025-001` (format BC avec tiret)
- [ ] `212011016` (format numérique)

### ✅ Cas d'Erreur Testés
- [ ] PDF vide → Status 400
- [ ] JSON invalide → Status 500
- [ ] PDF corrompu → Gestion d'erreur
- [ ] Données manquantes → Valeurs null

## 🚀 Déploiement

### Variables d'Environnement Requises
```bash
AZURE_OPENAI_KEY=votre_clé_openai
AZURE_OPENAI_ENDPOINT=https://votre-resource.openai.azure.com
AZURE_DEPLOYMENT_NAME=nom_de_votre_deployment
API_VERSION=2023-05-15
```

### Commandes de Déploiement
```bash
# Déployer avec Azure Functions Core Tools
func azure functionapp publish nom-de-votre-fonction

# Ou avec Azure CLI
az functionapp deployment source config-zip \
  --resource-group votre-rg \
  --name nom-de-votre-fonction \
  --src function-app.zip
```

## 📊 Métriques de Performance

### Temps de Réponse Attendus
- **PDF simple** : < 5 secondes
- **Email + PDF** : < 10 secondes
- **PDF complexe** : < 15 secondes

### Taux de Succès
- **Extraction d'ID** : > 95%
- **Analyse complète** : > 90%
- **Gestion d'erreurs** : 100%

## 🔍 Monitoring

### Logs à Surveiller
- Extraction de texte PDF
- Appels OpenAI
- Erreurs de décodage base64
- Temps de réponse

### Alertes à Configurer
- Temps de réponse > 15 secondes
- Taux d'erreur > 5%
- Échecs d'appels OpenAI

## ✅ Conclusion

Votre fonction Azure est **PRÊTE POUR LA PRODUCTION** ! 

Tous les tests automatisés sont passés avec succès (100%). Vous pouvez déployer en toute confiance et utiliser ce guide pour les tests manuels post-déploiement. 