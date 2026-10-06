import streamlit as st
from google import genai
import json
import os
import re
import time
import base64
import stripe
from datetime import datetime
from weasyprint import HTML

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================
st.set_page_config(
    page_title="Product Sheet Generator - AI",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# 🔓 TRAITEMENT DU RETOUR PAIEMENT STRIPE
# ============================================
query_params = st.query_params

if "emails_payes" not in st.session_state:
    st.session_state.emails_payes = []

if query_params.get("payment") == "success":
    email_paye = query_params.get("email", "")
    if email_paye and email_paye not in st.session_state.emails_payes:
        st.session_state.emails_payes.append(email_paye)

# ============================================
# 🎨 CSS MODERNE — THÈME VIOLET CLAIR
# ============================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #c7d2fe 0%, #d8b4fe 50%, #e9d5ff 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }
    .main .block-container {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(6px);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 1rem;
        margin-bottom: 2rem;
        max-width: 1100px;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.6);
    }
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
    }
    h2, h3 {
        color: #4c1d95 !important;
        font-weight: 700 !important;
    }
    .stApp p, .stApp label, .stApp span, .stApp div {
        color: #3b0764;
    }
    .stApp .stCaption, .stApp small {
        color: #6b21a8 !important;
    }
    .stButton button {
        border-radius: 12px !important;
        padding: 14px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        width: 100%;
        background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.45);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.65);
    }
    .stLinkButton a {
        display: block !important;
        text-align: center !important;
        padding: 16px !important;
        background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        text-decoration: none !important;
        font-weight: 700 !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.45);
    }
    .stTextInput input, .stTextArea textarea {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 10px !important;
        border: 2px solid #c4b5fd !important;
        background: #ffffff !important;
        color: #3b0764 !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2) !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background: #ffffff !important;
        border-radius: 10px !important;
        border: 2px solid #c4b5fd !important;
        color: #3b0764 !important;
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px 15px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #c4b5fd;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.15);
    }
    .stMetric label {
        color: #6b21a8 !important;
        font-weight: 600 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #3b0764 !important;
        font-weight: 800 !important;
    }
    .promo-badge {
        background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        text-align: center;
        font-weight: 700;
        margin-bottom: 25px;
        font-size: 16px;
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.4);
    }
    .result-box {
        background: rgba(255, 255, 255, 0.95);
        padding: 25px;
        border-radius: 15px;
        border-left: 5px solid #7c3aed;
        margin-top: 20px;
        white-space: pre-line;
        color: #3b0764;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.15);
    }
    .payment-box {
        background: rgba(255, 255, 255, 0.95);
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #7c3aed;
        margin-top: 20px;
        text-align: center;
    }
    .pay-btn {
        display: block;
        text-align: center;
        padding: 16px;
        background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%);
        color: white !important;
        border-radius: 12px;
        text-decoration: none;
        font-weight: 700;
        margin: 15px 0;
    }
    div[data-testid="stAlert"] {
        border-radius: 12px;
    }
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
            border-radius: 15px;
            margin: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 🌍 TRADUCTIONS
# ============================================
TEXTES = {
    "Français 🇫🇷": {
        "promo": "🎁 Votre 1ère fiche 100% Gratuite · Puis Offre flash : 5 fiches pour le prix de 4 !",
        "titre": "🛍️ Fiche Produit",
        "sous_titre": "Générez des fiches produits professionnelles en 30 secondes",
        "metric_fiches": "📝 Vos Fiches Générées",
        "metric_users": "👥 Utilisateurs Actifs",
        "metric_prix": "💰 Prix par fiche",
        "etape1": "🔑 Étape 1 : Entrez votre adresse e-mail",
        "label_email": "Votre e-mail pour activer ou suivre vos fiches *",
        "email_placeholder": "exemple@domaine.com",
        "etape2": "📝 Étape 2 : Détails du produit",
        "nom_produit": "Nom du produit *",
        "nom_produit_ph": "Ex: Sac en cuir",
        "caracs": "Caractéristiques *",
        "caracs_ph": "Ex: Cuir véritable, noir",
        "langue_fiche": "📝 Langue de la fiche produit",
        "ton": "Ton éditorial",
        "longueur": "Longueur de la fiche",
        "options_ton": ["Professionnel", "Luxe", "Chaleureux", "Minimaliste"],
        "options_longueur": ["Courte", "Moyenne", "Détaillée"],
        "options_langue_fiche": ["Français 🇫🇷", "Anglais 🇬🇧", "Espagnol 🇪🇸", "Allemand 🇩🇪", "Italien 🇮🇹", "Arabe 🇸🇦"],
        "options": "⚙️ Options avancées",
        "mots_cles": "Mots-clés SEO",
        "mots_cles_ph": "Ex: sac durable",
        "btn_gratuit": "🚀 Générer ma fiche gratuite (Essai offert)",
        "btn_payant": "💳 Payer et générer ma fiche (0,99 €)",
        "essai_ok": "🎉 Bonne nouvelle ! Vous bénéficiez d'un **essai gratuit (1 fiche offerte)**.",
        "essai_utilise": "ℹ️ Essai déjà consommé. Prochaines fiches : **0,99 €**.",
        "email_invalide": "❌ Veuillez entrer une adresse e-mail valide.",
        "genere_ok": "✨ Votre fiche a été générée avec succès !",
        "genere_spinner": "🤖 Génération en cours...",
        "resultat": "✨ Votre fiche produit générée :",
        "historique": "📋 Vos fiches générées",
        "remplir_champs": "⚠️ Veuillez remplir le nom et les caractéristiques.",
        "paiement_titre": "💳 Paiement sécurisé prêt !",
        "paiement_bouton": "🔒 Payer maintenant 0,99 € sur Stripe",
        "paiement_info": "Paiement 100% sécurisé par Stripe.",
        "paiement_erreur": "❌ Erreur Stripe :",
        "paiement_ok": "🎉 Paiement confirmé ! Complétez le formulaire pour générer votre fiche.",
        "pdf_bouton": "📄 Télécharger en PDF",
        "surcharge": "⏳ Le service est momentanément surchargé. Merci de réessayer dans 1 à 2 minutes. Votre essai gratuit n'a **pas** été consommé.",
        "aucun_modele": "❌ Aucun modèle Gemini disponible pour votre clé API. Vérifiez vos secrets.",
    },
    "Anglais 🇬🇧": {
        "promo": "🎁 Your 1st sheet 100% Free · Then Flash offer: 5 sheets for the price of 4!",
        "titre": "🛍️ Product Sheet",
        "sous_titre": "Generate professional product sheets in 30 seconds",
        "metric_fiches": "📝 Your Generated Sheets",
        "metric_users": "👥 Active Users",
        "metric_prix": "💰 Price per sheet",
        "etape1": "🔑 Step 1: Enter your email address",
        "label_email": "Your email to activate or track your sheets *",
        "email_placeholder": "example@domain.com",
        "etape2": "📝 Step 2: Product details",
        "nom_produit": "Product name *",
        "nom_produit_ph": "Ex: Leather bag",
        "caracs": "Features *",
        "caracs_ph": "Ex: Genuine leather, black",
        "langue_fiche": "📝 Product sheet language",
        "ton": "Editorial tone",
        "longueur": "Sheet length",
        "options_ton": ["Professional", "Luxury", "Warm", "Minimalist"],
        "options_longueur": ["Short", "Medium", "Detailed"],
        "options_langue_fiche": ["French 🇫🇷", "English 🇬🇧", "Spanish 🇪🇸", "German 🇩🇪", "Italian 🇮🇹", "Arabic 🇸🇦"],
        "options": "⚙️ Advanced options",
        "mots_cles": "SEO keywords",
        "mots_cles_ph": "Ex: durable bag",
        "btn_gratuit": "🚀 Generate my free sheet (Free trial)",
        "btn_payant": "💳 Pay and generate my sheet (€0.99)",
        "essai_ok": "🎉 Good news! You get a **free trial (1 sheet offered)**.",
        "essai_utilise": "ℹ️ Trial already used. Next sheets: **€0.99**.",
        "email_invalide": "❌ Please enter a valid email address.",
        "genere_ok": "✨ Your sheet has been generated successfully!",
        "genere_spinner": "🤖 Generating...",
        "resultat": "✨ Your generated product sheet:",
        "historique": "📋 Your generated sheets",
        "remplir_champs": "⚠️ Please fill in the name and features.",
        "paiement_titre": "💳 Secure payment ready!",
        "paiement_bouton": "🔒 Pay now €0.99 on Stripe",
        "paiement_info": "100% secure payment by Stripe.",
        "paiement_erreur": "❌ Stripe error:",
        "paiement_ok": "🎉 Payment confirmed! Complete the form to generate your sheet.",
        "pdf_bouton": "📄 Download PDF",
        "surcharge": "⏳ The service is temporarily overloaded. Please try again in 1-2 minutes. Your free trial was **not** consumed.",
        "aucun_modele": "❌ No Gemini model available for your API key. Check your secrets.",
    },
    "Espagnol 🇪🇸": {
        "promo": "🎁 ¡Tu 1ª ficha 100% Gratis · Oferta flash: 5 fichas por el precio de 4!",
        "titre": "🛍️ Ficha de Producto",
        "sous_titre": "Genera fichas de productos profesionales en 30 segundos",
        "metric_fiches": "📝 Tus Fichas Generadas",
        "metric_users": "👥 Usuarios Activos",
        "metric_prix": "💰 Precio por ficha",
        "etape1": "🔑 Paso 1: Introduce tu correo electrónico",
        "label_email": "Tu correo para activar o seguir tus fichas *",
        "email_placeholder": "ejemplo@dominio.com",
        "etape2": "📝 Paso 2: Detalles del producto",
        "nom_produit": "Nombre del producto *",
        "nom_produit_ph": "Ej: Bolso de cuero",
        "caracs": "Características *",
        "caracs_ph": "Ej: Cuero genuino, negro",
        "langue_fiche": "📝 Idioma de la ficha",
        "ton": "Tono editorial",
        "longueur": "Longitud de la ficha",
        "options_ton": ["Profesional", "Lujo", "Cálido", "Minimalista"],
        "options_longueur": ["Corta", "Media", "Detallada"],
        "options_langue_fiche": ["Francés 🇫🇷", "Inglés 🇬🇧", "Español 🇪🇸", "Alemán 🇩🇪", "Italiano 🇮🇹", "Árabe 🇸🇦"],
        "options": "⚙️ Opciones avanzadas",
        "mots_cles": "Palabras clave SEO",
        "mots_cles_ph": "Ej: bolso duradero",
        "btn_gratuit": "🚀 Generar mi ficha gratis (Prueba gratis)",
        "btn_payant": "💳 Pagar y generar mi ficha (0,99 €)",
        "essai_ok": "🎉 ¡Buenas noticias! Tienes una **prueba gratuita (1 ficha)**.",
        "essai_utilise": "ℹ️ Prueba ya usada. Próximas fichas: **0,99 €**.",
        "email_invalide": "❌ Por favor introduce un correo válido.",
        "genere_ok": "✨ ¡Tu ficha se ha generado con éxito!",
        "genere_spinner": "🤖 Generando...",
        "resultat": "✨ Tu ficha de producto generada:",
        "historique": "📋 Tus fichas generadas",
        "remplir_champs": "⚠️ Por favor rellena el nombre y las características.",
        "paiement_titre": "💳 ¡Pago seguro listo!",
        "paiement_bouton": "🔒 Pagar ahora 0,99 € en Stripe",
        "paiement_info": "Pago 100% seguro por Stripe.",
        "paiement_erreur": "❌ Error de Stripe:",
        "paiement_ok": "🎉 ¡Pago confirmado! Completa el formulario para generar tu ficha.",
        "pdf_bouton": "📄 Descargar PDF",
        "surcharge": "⏳ El servicio está temporalmente sobrecargado. Inténtalo de nuevo en 1-2 minutos. Tu prueba gratuita **no** se ha consumido.",
        "aucun_modele": "❌ Ningún modelo Gemini disponible para tu clave API. Verifica tus secretos.",
    },
}

LOCALES_STRIPE = {
    "Français 🇫🇷": "fr",
    "Anglais 🇬🇧": "en",
    "Espagnol 🇪🇸": "es",
}

# ============================================
# SECRETS & API
# ============================================
try:
    STRIPE_SECRET_KEY = st.secrets["STRIPE_SECRET_KEY"]
    STRIPE_PRICE_ID = st.secrets["STRIPE_PRICE_ID"]
    MON_URL_STREAMLIT = st.secrets["MON_URL_STREAMLIT"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    stripe.api_key = STRIPE_SECRET_KEY
except KeyError as e:
    st.error(f"❌ Secret manquant : {e}")
    st.stop()

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"❌ Erreur API Gemini : {e}")
    st.stop()

# ============================================
# 🤖 AUTO-DÉCOUVERTE DES MODÈLES DISPONIBLES
# ============================================
@st.cache_resource(show_spinner=False)
def obtenir_modeles_disponibles():
    try:
        noms = []
        for m in client.models.list():
            methods = (
                getattr(m, "supported_generation_methods", None)
                or getattr(m, "supported_actions", [])
                or []
            )
            methods_str = [str(x) for x in methods]
            if any("generateContent" in s for s in methods_str):
                nom_propre = m.name.replace("models/", "")
                noms.append(nom_propre)

        if not noms:
            return []

        def cle_tri(x):
            return (
                "flash" not in x,
                "latest" not in x,
                "2.5" not in x,
                "2.0" not in x,
                "1.5" not in x,
                x,
            )

        noms.sort(key=cle_tri)
        return noms

    except Exception as e:
        st.warning(f"⚠️ Impossible de lister les modèles : {e}")
        return []

# ============================================
# UTILISATEURS (fichier JSON local)
# ============================================
DB_FILE = "utilisateurs.json"

def charger_utilisateurs():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def enregistrer_utilisateur(email, a_utilise_essai=True):
    utilisateurs = charger_utilisateurs()
    utilisateurs[email] = {
        "a_utilise_essai": a_utilise_essai,
        "date_inscription": datetime.now().isoformat()
    }
    with open(DB_FILE, "w") as f:
        json.dump(utilisateurs, f)

def valider_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

# ============================================
# STATE
# ============================================
if "generations" not in st.session_state:
    st.session_state.generations = 0
if "generated_products" not in st.session_state:
    st.session_state.generated_products = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "current_nom_produit" not in st.session_state:
    st.session_state.current_nom_produit = ""
if "user_count" not in st.session_state:
    st.session_state.user_count = 847
if "payment_url" not in st.session_state:
    st.session_state.payment_url = None
if "cache_fiche" not in st.session_state:
    st.session_state.cache_fiche = {}

# ============================================
# 🤖 GÉNÉRATION IA (PROMPT ARABE DÉDIÉ + RETRY)
# ============================================
def generer_fiche_ia(nom, caracteristiques, ton, longueur, mots_cles, langue):
    est_arabe = any(x in langue for x in ["Arabe", "Arabic", "Árabe", "🇸🇦"])

    if est_arabe:
        prompt = f"""
أنت خبير في كتابة المحتوى التسويقي للتجارة الإلكترونية وتحسين محركات البحث (SEO).

اكتب بطاقة منتج جذابة ومحسّنة للتحويل وSEO.
⚠️ يجب أن تكون البطاقة بالكامل باللغة العربية الفصحى. لا تستخدم أي لغة أخرى أبدًا.

=== معلومات المنتج ===
- الاسم: {nom}
- الخصائص: {caracteristiques}
- النبرة: {ton}
- الطول: {longueur}
- كلمات مفتاحية SEO: {mots_cles}

=== البنية المطلوبة ===
1. عنوان H1 جذاب (أقل من 70 حرفًا)
2. عنوان فرعي يبرز الفائدة (أقل من 120 حرفًا)
3. مقدمة من 2-3 جمل تركز على فوائد العميل
4. قسم "لماذا تختار هذا المنتج؟" مع 4 نقاط
5. قسم "المواصفات الرئيسية" مع 4 نقاط
6. دعوة نهائية قوية لاتخاذ إجراء

=== قواعد صارمة ===
- اكتب كل النص بالعربية فقط، بما في ذلك عناوين الأقسام.
- لا تستخدم أبدًا الفواصل مثل "--" أو "---" أو "___".
- افصل الأقسام بعناوين Markdown (##, ###).
- استخدم النقاط بشرطة "-" فقط للقوائم.
- تأكد من كتابة التنوين والحركات ملتصقة بالحرف السابق (مثال: مظهراً وليس مظهرا ً).
- راجع نفسك: لا أخطاء إملائية، لا جمل ناقصة.
- لا تضع رموز Markdown حول النص (بدون ```).
- أجب فقط بالبطاقة النهائية، بدون أي تعليق.
"""
    else:
        prompt = f"""
Tu es un expert en copywriting e-commerce et SEO.

Rédige une fiche produit captivante, optimisée pour la conversion et le référencement.
LA FICHE DOIT ÊTRE ENTIÈREMENT RÉDIGÉE EN : {langue}.

⚠️ RÈGLE ABSOLUE : Utilise UNIQUEMENT la langue demandée ({langue}) dans TOUT le texte.
Traduis TOUS les titres de sections dans cette langue.

=== INFORMATIONS PRODUIT ===
- Nom : {nom}
- Caractéristiques : {caracteristiques}
- Ton éditorial : {ton}
- Longueur : {longueur}
- Mots-clés SEO : {mots_cles}

=== STRUCTURE ATTENDUE ===
1. Un titre H1 accrocheur (≤ 70 caractères)
2. Un sous-titre bénéfice (≤ 120 caractères)
3. Une introduction de 2-3 phrases orientée bénéfices client
4. Une section "Pourquoi choisir ce produit ?" avec 4 puces
5. Une section "Caractéristiques clés" avec 4 puces
6. Un appel à l'action final percutant

=== RÈGLES STRICTES ===
- TOUT le texte doit être dans la langue demandée ({langue}), sans exception.
- N'utilise JAMAIS de séparateurs comme "--", "---" ou "___".
- Sépare les sections par des titres Markdown (##, ###).
- Utilise des puces avec "-" uniquement pour les listes.
- Relis-toi : aucune faute d'orthographe, aucune phrase inachevée.
- Ne mets pas de code Markdown autour du texte (pas de ```).
- Réponds UNIQUEMENT avec la fiche finale, sans commentaire.
"""

    modeles = obtenir_modeles_disponibles()

    if not modeles:
        return "❌ Erreur : aucun modèle Gemini disponible pour votre clé API."

    modeles_a_tester = modeles[:5]
    derniere_erreur = None

    for mod in modeles_a_tester:
        for tentative in range(2):
            try:
                response = client.models.generate_content(model=mod, contents=prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                derniere_erreur = str(e)
                if "404" in derniere_erreur or "NOT_FOUND" in derniere_erreur:
                    break
                if "503" in derniere_erreur or "UNAVAILABLE" in derniere_erreur:
                    time.sleep(2)
                continue

    return f"❌ Erreur : {derniere_erreur}"

# ============================================
# 📄 GÉNÉRATION PDF AVEC WEASYPRINT (RTL NATIF + POLICE EMBARQUÉE)
# ============================================
@st.cache_resource(show_spinner=False)
def _charger_police_base64():
    """Charge la police arabe en base64 pour l'intégrer dans le HTML."""
    try:
        with open("NotoNaskhArabic-Regular.ttf", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def _nettoyer_espaces_arabe(texte):
    """Corrige les espaces parasites avant les accents arabes."""
    remplacements = {
        " ً": "ً", " ٍ": "ٍ", " ٌ": "ٌ",
        " َ": "َ", " ِ": "ِ", " ُ": "ُ",
        " ْ": "ْ", " ّ": "ّ",
    }
    for k, v in remplacements.items():
        texte = texte.replace(k, v)
    return texte


def _markdown_vers_html(contenu, est_arabe=False):
    """Convertit une fiche Markdown simple en HTML structuré."""
    lignes_html = []
    for ligne in contenu.split("\n"):
        l = ligne.rstrip()

        if not l.strip():
            lignes_html.append("<br>")
            continue

        if est_arabe:
            l = _nettoyer_espaces_arabe(l)

        if l.startswith("### "):
            lignes_html.append(f"<h3>{l[4:]}</h3>")
        elif l.startswith("## "):
            lignes_html.append(f"<h2>{l[3:]}</h2>")
        elif l.startswith("# "):
            lignes_html.append(f"<h1>{l[2:]}</h1>")
        elif l.lstrip().startswith(("- ", "* ")):
            texte_puce = l.lstrip()[2:]
            if est_arabe:
                lignes_html.append(f'<p class="puce-ar">• {texte_puce}</p>')
            else:
                lignes_html.append(f'<p class="puce">• {texte_puce}</p>')
        else:
            lignes_html.append(f"<p>{l}</p>")

    return "\n".join(lignes_html)


def generer_pdf(contenu, nom_produit, langue="Français 🇫🇷"):
    est_arabe = any(x in langue for x in ["Arabe", "Arabic", "Árabe", "🇸🇦"])

    corps_html = _markdown_vers_html(contenu, est_arabe=est_arabe)

    direction = "rtl" if est_arabe else "ltr"
    align = "right" if est_arabe else "left"
    titre_section = "بطاقة المنتج" if est_arabe else "Fiche Produit"

    # Police embarquée en base64
    police_b64 = _charger_police_base64()
    font_face = ""
    if police_b64:
        font_face = f"""
        @font-face {{
            font-family: 'NotoArabicEmbedded';
            src: url(data:font/ttf;base64,{police_b64}) format('truetype');
        }}
        """
        police_css = "'NotoArabicEmbedded', 'DejaVu Sans', Arial, sans-serif"
    else:
        police_css = "'Noto Naskh Arabic', 'Amiri', 'DejaVu Sans', Arial, sans-serif"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            {font_face}
            @page {{
                margin: 2cm;
                size: A4;
            }}
            body {{
                font-family: {police_css};
                direction: {direction};
                text-align: {align};
                font-size: 12pt;
                line-height: 1.8;
                color: #333333;
            }}
            h1 {{
                font-size: 20pt;
                color: #4c1d95;
                margin-bottom: 8px;
                margin-top: 0;
            }}
            h2 {{
                font-size: 16pt;
                color: #6b21a8;
                margin-top: 22px;
                margin-bottom: 10px;
                border-bottom: 1px solid #e9d5ff;
                padding-bottom: 4px;
            }}
            h3 {{
                font-size: 14pt;
                color: #7c3aed;
                margin-top: 16px;
                margin-bottom: 8px;
            }}
            p {{
                margin: 8px 0;
            }}
            .puce-ar {{
                padding-right: 25px;
                text-indent: -15px;
                margin: 5px 0;
            }}
            .puce {{
                padding-left: 25px;
                text-indent: -15px;
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <h1>{titre_section} — {nom_produit}</h1>
        {corps_html}
    </body>
    </html>
    """

    return HTML(string=html).write_pdf()

# ============================================
# 🌍 INTERFACE
# ============================================
st.markdown("## 🌍 Choose your language / Choisissez votre langue / Elige tu idioma")

langue_interface = st.selectbox(
    "Language / Langue / Idioma",
    list(TEXTES.keys()),
    key="langue_interface_select"
)

T = TEXTES[langue_interface]

if query_params.get("payment") == "success":
    email_retour = query_params.get("email", "")
    st.success(T["paiement_ok"])
    st.info(f"📧 {email_retour}")
    st.write("---")

st.markdown(f'<div class="promo-badge">{T["promo"]}</div>', unsafe_allow_html=True)

st.title(T["titre"])
st.subheader(T["sous_titre"])


col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(label=T["metric_fiches"], value=st.session_state.generations)
with col_m2:
    st.metric(label=T["metric_prix"], value="0,99 €")

st.write("---")

# ============================================
# ÉTAPE 1 : EMAIL
# ============================================
st.markdown(f"### {T['etape1']}")
user_email = st.text_input(
    T["label_email"],
    placeholder=T["email_placeholder"]
).strip().lower()

if user_email:
    if not valider_email(user_email):
        st.error(T["email_invalide"])
    else:
        db_utilisateurs = charger_utilisateurs()
        deja_utilise = user_email in db_utilisateurs and db_utilisateurs[user_email].get("a_utilise_essai", False)
        email_deja_paye = user_email in st.session_state.emails_payes

        if not deja_utilise:
            st.success(T["essai_ok"])
            bouton_texte = T["btn_gratuit"]
            est_payant = False
        elif email_deja_paye:
            st.success(T["paiement_ok"])
            bouton_texte = "✨ Générer ma fiche payée"
            est_payant = False
        else:
            st.warning(T["essai_utilise"])
            bouton_texte = T["btn_payant"]
            est_payant = True

        st.write("---")

        # ============================================
        # ÉTAPE 2 : FORMULAIRE
        # ============================================
        st.markdown(f"### {T['etape2']}")
        col_form1, col_form2 = st.columns(2)

        with col_form1:
            nom_produit = st.text_input(T["nom_produit"], placeholder=T["nom_produit_ph"])
            caracs = st.text_area(T["caracs"], placeholder=T["caracs_ph"])

        with col_form2:
            langue_choisie = st.selectbox(T["langue_fiche"], T["options_langue_fiche"])
            ton_choisi = st.selectbox(T["ton"], T["options_ton"])
            longueur_choisie = st.selectbox(T["longueur"], T["options_longueur"])

        with st.expander(T["options"]):
            mots_cles = st.text_input(T["mots_cles"], placeholder=T["mots_cles_ph"])

        st.write("")

        # ============================================
        # BOUTON D'ACTION
        # ============================================
        if st.button(bouton_texte):
            if not nom_produit or not caracs:
                st.warning(T["remplir_champs"])
            else:
                if est_payant:
                    try:
                        locale_stripe = LOCALES_STRIPE.get(langue_interface, "auto")
                        session_stripe = stripe.checkout.Session.create(
                         
                            line_items=[{'price': STRIPE_PRICE_ID, 'quantity': 1}],
                            mode='payment',
                            success_url=f"{MON_URL_STREAMLIT}?payment=success&email={user_email}",
                            cancel_url=MON_URL_STREAMLIT,
                            customer_email=user_email,
                            locale=locale_stripe
                        )
                        st.session_state.payment_url = session_stripe.url
                    except Exception as e:
                        st.error(f"{T['paiement_erreur']} {str(e)}")
                else:
                    cle_cache = f"{nom_produit}|{caracs}|{ton_choisi}|{longueur_choisie}|{langue_choisie}|{mots_cles}"

                    if cle_cache in st.session_state.cache_fiche:
                        fiche_finale = st.session_state.cache_fiche[cle_cache]
                    else:
                        with st.spinner(T["genere_spinner"]):
                            fiche_finale = generer_fiche_ia(
                                nom_produit, caracs, ton_choisi,
                                longueur_choisie, mots_cles, langue_choisie
                            )
                            if "❌" not in fiche_finale:
                                st.session_state.cache_fiche[cle_cache] = fiche_finale

                    if "❌" not in fiche_finale:
                        if not deja_utilise:
                            enregistrer_utilisateur(user_email, a_utilise_essai=True)

                        st.session_state.current_result = fiche_finale
                        st.session_state.current_nom_produit = nom_produit
                        st.session_state.generations += 1
                        st.session_state.generated_products.append({
                            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "nom": nom_produit,
                            "langue": langue_choisie,
                            "contenu": fiche_finale
                        })
                        st.success(T["genere_ok"])
                    else:
                        if "503" in fiche_finale or "UNAVAILABLE" in fiche_finale:
                            st.warning(T["surcharge"])
                        elif "404" in fiche_finale or "NOT_FOUND" in fiche_finale or "aucun modèle" in fiche_finale.lower():
                            st.error(T["aucun_modele"])
                        else:
                            st.error(fiche_finale)

        # ============================================
        # 💳 ZONE DE PAIEMENT
        # ============================================
        if st.session_state.payment_url:
            st.write("---")
            st.markdown(f"### {T['paiement_titre']}")

            bouton_affiche = False
            try:
                st.link_button(
                    T["paiement_bouton"],
                    st.session_state.payment_url,
                    use_container_width=True
                )
                bouton_affiche = True
            except (AttributeError, TypeError):
                pass

            if not bouton_affiche:
                st.markdown(
                    f'<a href="{st.session_state.payment_url}" target="_blank" class="pay-btn">'
                    f'{T["paiement_bouton"]}</a>',
                    unsafe_allow_html=True
                )

            st.caption(T["paiement_info"])

        # ============================================
        # 📄 AFFICHAGE RÉSULTAT + PDF
        # ============================================
        if st.session_state.current_result:
            st.write("---")
            st.markdown(f"### {T['resultat']}")

            if any(x in langue_choisie for x in ["Arabe", "Arabic", "Árabe", "🇸🇦"]):
                st.markdown(
                    f'<div class="result-box" style="direction: rtl; text-align: right;">{st.session_state.current_result}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="result-box">{st.session_state.current_result}</div>',
                    unsafe_allow_html=True
                )

            try:
                pdf_bytes = generer_pdf(
                    st.session_state.current_result,
                    st.session_state.current_nom_produit or "produit",
                    langue=langue_choisie
                )

                nom_base = st.session_state.current_nom_produit or "produit"
                nom_fichier = "fiche_" + nom_base.replace(" ", "_") + ".pdf"

                st.download_button(
                    label=T["pdf_bouton"],
                    data=pdf_bytes,
                    file_name=nom_fichier,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"PDF indisponible : {e}")

        # ============================================
        # HISTORIQUE
        # ============================================
        if st.session_state.generated_products:
            st.write("---")
            st.markdown(f"### {T['historique']}")
            for prod in reversed(st.session_state.generated_products):
                with st.expander(f"📦 {prod['nom']} ({prod['langue']}) - {prod['date']}"):
                    st.markdown(prod['contenu'])
