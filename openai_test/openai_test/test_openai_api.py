import requests
import json

# ⚠️ À personnaliser avec vos vraies infos Azure OpenAI :
api_key = "AdPHTHXZNRoeO6SB6w4Q7I9WwZG0MV5av4fdoAerlFML3rsNILHAJQQJ99BGAC5RqLJXJ3w3AAABACOGwp6q"
endpoint = "https://sthaistg.openai.azure.com/openai/deployments/gpt35-pfa/chat/completions?api-version=2023-03-15-preview"


# Exemple d'email fictif à analyser :
email = """
Objet : Bon de commande 12345
Fournisseur : ABC Industries
Date de livraison : 25 juillet 2025
Date de réception : 17 juillet 2025
"""

# Prompt envoyé à Azure OpenAI
prompt = f"""
Voici un e-mail d'un fournisseur. Extrait les éléments suivants :
- ID commande
- Fournisseur
- Date de réception
- Date de livraison

Réponds en JSON.
Texte : {email}
"""

# Envoi de la requête
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

body = {
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0,
    "max_tokens": 500
}

response = requests.post(endpoint, headers=headers, json=body)

# Affichage et sauvegarde du résultat
result = response.json()['choices'][0]['message']['content']

print("Réponse de Azure OpenAI :")
print(result)

with open("resultat.json", "w") as f:
    f.write(result)
