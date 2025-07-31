import azure.functions as func
import logging
import os
import requests
import fitz  # PyMuPDF
import json
import time
import base64
import re  # Importation de la bibliothèque regex pour extraire l'ID de commande
# tbadel4
# Configuration via variables d'environnement
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
API_VERSION = os.getenv("API_VERSION")
HEADERS = {
    "api-key": AZURE_OPENAI_KEY,
    "Content-Type": "application/json"
}

# Instruction donnée à OpenAI pour l'extraction des informations
LONG_INSTRUCTION = (
    "Tu es un assistant expert en gestion des commandes fournisseurs. "
    "Ton objectif est d'extraire **uniquement** les informations suivantes à partir du texte d’un email ou d’un bon de commande (BC), "
    "y compris les pièces jointes PDF :\n"
    "- **ID de la commande** (exemple : BSK2506CF0383). L'ID de commande peut être trouvé dans l'email ou dans le contenu du PDF attaché.\n"
    "- **Nom du fournisseur** (exemple : 'IMPRIMERIE AJDIR'). Le nom du fournisseur peut être mentionné dans l'email ou dans le bon de commande.\n"
    "- **Date de réception** de la commande (exemple : '23/06/2025'). Cette date peut être indiquée dans l'email ou dans le bon de commande.\n"
    "- **Date de livraison prévue** (exemple : '29/07/2025'). Cette date peut être indiquée dans l'email, le bon de commande ou dans la pièce jointe PDF.\n"
    "\n"
    "Tu ne dois extraire **que ces informations spécifiques** et ignorer les autres détails du bon de commande ou de l'email. "
    "L'ID de commande, le nom du fournisseur, la date de réception et la date de livraison doivent être les seules informations retournées dans la réponse.\n"
    "\n"
    "Si une information est absente dans l'email, vérifie si une pièce jointe PDF est présente et analyse-la pour tenter de retrouver ces informations. "
    "Si tu trouves des informations dans la pièce jointe qui manquaient dans l'email, complète le JSON avec ces données. "
    "Si une information reste absente après analyse de l'email et de la pièce jointe, indique la valeur `null` dans le JSON.\n"
    "\n"
    "Le format attendu pour la réponse est un JSON structuré comme suit :\n"
    "{\n"
    "  \"ID_commande\": \"BSK2506CF0383\",  # L'ID de la commande extrait\n"
    "  \"nom_fournisseur\": \"IMPRIMERIE AJDIR\",  # Le nom du fournisseur extrait\n"
    "  \"date_reception\": \"23/06/2025\",  # La date de réception de la commande\n"
    "  \"date_livraison\": \"29/07/2025\"  # La date de livraison prévue\n"
    "}\n"
    "\n"
    "Si l'une de ces informations est absente dans l'email et dans le PDF, tu dois retourner `null` pour ce champ spécifique.\n"
    "\n"
    "Exemple de données attendues :\n"
    "{\n"
    "  \"ID_commande\": \"BSK2506CF0383\",\n"
    "  \"nom_fournisseur\": \"IMPRIMERIE AJDIR\",\n"
    "  \"date_reception\": \"23/06/2025\",\n"
    "  \"date_livraison\": \"29/07/2025\"\n"
    "}\n"
    "Assure-toi que les informations retournées soient **exactes et dans ce format précis**.\n"
)

# Fonction pour envoyer la requête à OpenAI
def query_azure_openai(user_content: str):
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"
    body = {
        "messages": [
            {"role": "system", "content": LONG_INSTRUCTION},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    retry_delay = 5
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=HEADERS, json=body, timeout=30)
            response.raise_for_status()
            return response.json()  # Retourner le JSON de la réponse
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                time.sleep(retry_delay * (attempt + 1))
                continue
            logging.error(f"Erreur OpenAI: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Erreur de connexion: {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay * (attempt + 1))

# Fonction pour extraire le texte d'un PDF
def extract_text_from_pdf(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = []
    for page in doc:
        text = page.get_text("text").strip()  # Extraction du texte brut
        if text:
            all_text.append(text)
    return "\n".join(all_text)

# Fonction pour extraire l'ID de commande
def extract_order_id_from_pdf(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = []
    for page in doc:
        text = page.get_text("text").strip()  # Extraction du texte brut
        if text:
            all_text.append(text)
    
    # Combiner tout le texte extrait pour chercher l'ID de commande
    full_text = "\n".join(all_text)
    
    # Expression régulière pour extraire différents formats d'ID de commande
    # Formats supportés : BSK, TAC, CMD, PO, BC, ORDER, REF, et formats numériques
    patterns = [
        r"\bBSK[A-Z0-9]{10}\b",  # Format BSK standard
        r"\bTAC\s+[A-Z0-9]+\b",  # Format TAC (ex: TAC ETAC60JDF)
        r"\b[A-Z]{2,4}[0-9]{6,12}\b",  # Format générique : 2-4 lettres + 6-12 chiffres
        r"\b[A-Z]{2,4}[0-9]{3,4}[-]?[0-9]{3}\b",  # Format avec tiret (ex: BC2025-001)
        r"\b[A-Z0-9]{8,15}\b",  # Format générique : 8-15 caractères alphanumériques
        r"\b[0-9]{9,12}\b",  # Format numérique pur (ex: 212011016)
        r"\b[A-Z0-9]{6,20}\b",  # Format très générique : 6-20 caractères alphanumériques
        r"\b[A-Z]{2,6}[0-9]{4,10}\b",  # Format : 2-6 lettres + 4-10 chiffres
        r"\b[A-Z0-9]{4,25}\b",  # Format ultra-générique : 4-25 caractères alphanumériques
        r"\b[A-Z]{1,8}[0-9]{1,15}\b",  # Format : 1-8 lettres + 1-15 chiffres
        r"\b[0-9]{4,20}\b"  # Format numérique étendu : 4-20 chiffres
    ]
    
    # Log pour debug
    logging.info(f"Texte complet extrait du PDF: {full_text[:500]}...")
    
    for pattern in patterns:
        match = re.search(pattern, full_text)
        if match:
            found_id = match.group(0)
            logging.info(f"ID trouvé avec pattern {pattern}: {found_id}")
            return found_id  # Retourne le premier ID trouvé
    
    logging.warning("Aucun ID de commande trouvé dans le PDF")
    return None  # Aucun ID trouvé

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.function_name(name="analyze_email_and_pdf")
@app.route(route="analyze_email_and_pdf", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        content_type = req.headers.get("Content-Type", "")
        user_content = ""

        # Récupération de l'email de l'expéditeur
        sender_email = req.get_json().get("sender_email", "")

        # Si le contenu est un PDF
        if "application/pdf" in content_type:
            pdf_bytes = req.get_body()
            if not pdf_bytes or len(pdf_bytes) < 1000:
                return func.HttpResponse("Le fichier PDF est vide ou incomplet", status_code=400)
            # Extraire l'ID de commande du PDF
            order_id = extract_order_id_from_pdf(pdf_bytes)

            if order_id:
                return func.HttpResponse(json.dumps({"ID_commande": order_id}), status_code=200, mimetype="application/json")
            else:
                return func.HttpResponse("Aucun ID de commande trouvé dans le PDF.", status_code=404)

        # Si le contenu est un email (ce cas est déclenché par Power Automate)
        else:
            req_body = req.get_json()
            email_text = req_body.get("email")

            # Vérifier si le fournisseur est présent dans l'email
            if "Fournisseur : " not in email_text or not email_text.split("Fournisseur : ")[1].strip():
                # Si le fournisseur est absent, utiliser l'email de l'expéditeur comme fournisseur
                email_text = email_text.replace("Fournisseur : ", f"Fournisseur : {sender_email}")

            pdf_text = None
            if "pdf_base64" in req_body:
                try:
                    pdf_bytes = base64.b64decode(req_body["pdf_base64"])
                    pdf_text = extract_text_from_pdf(pdf_bytes)
                    # Log pour debug
                    logging.info(f"Texte extrait du PDF: {pdf_text[:200]}...")
                except Exception as e:
                    logging.error(f"Erreur lors du décodage ou de l'extraction du PDF: {str(e)}")

            # Si un email et un PDF sont fournis, combinez-les
            if email_text and pdf_text:
                user_content = f"EMAIL:\n{email_text}\n\nPIECE_JOINTE_PDF:\n{pdf_text}"
            elif email_text:
                user_content = email_text
            elif pdf_text:
                user_content = pdf_text
            else:
                return func.HttpResponse("Aucun contenu à analyser (ni email ni PDF)", status_code=400)

        # Envoi de la requête à OpenAI
        result = query_azure_openai(user_content)

        # Vérification si la réponse est valide et structurer correctement
        if 'choices' in result and 'content' in result['choices'][0]['message']:
            result_json = result['choices'][0]['message']['content']
            logging.info(f"Réponse OpenAI : {result_json}")
            return func.HttpResponse(result_json, status_code=200, mimetype="application/json")
        else:
            logging.error("Réponse non valide ou mal structurée.")
            return func.HttpResponse("Erreur lors de l'analyse des données.", status_code=500)

    except Exception as e:
        logging.error(f"Erreur interne : {str(e)}")
        return func.HttpResponse(f"Erreur interne : {str(e)}", status_code=500)
