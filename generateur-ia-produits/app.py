import streamlit as st
from google import genai
import json
import os
import re
import stripe
import time
from datetime import datetime

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
# 🎨 CSS MODERNE — FOND DÉGRADÉ + CARTES
# ============================================
st.markdown("""
<style>
    /* FOND DÉGRADÉ MODERNE */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }
    
    /* CONTENEUR PRINCIPAL BLANC QUI FLOTTE */
    .main .block-container {
        background: rgba(255, 255, 255, 0.97);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    
    /* TITRES AVEC DÉGRADÉ */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
    }
    h2, h3 { color: #333 !important; font-weight: 700 !important; }
    
    /* BOUTONS MODERNES */
    .stButton button {
        border-radius: 12px !important;
        padding: 14px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    
    .stLinkButton a {
        display: block !important;
        text-align: center !important;
        padding: 16px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        text-decoration: none !important;
        font-weight: 700 !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* CHAMPS DE SAISIE */
    .stTextInput input, .stTextArea textarea {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 10px !important;
        border: 2px solid #e0e0e0 !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #667eea !important;
    }
    
    /* CARTES MÉTRIQUES */
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 20px 15px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }
    .stMetric label { color: #666 !important; font-weight: 600 !important; }
    
    /* BADGE PROMO ANIMÉ */
    .promo-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        text-align: center;
        font-weight: 700;
        margin-bottom: 25px;
        font-size: 16px;
        box-shadow: 0 6px 20px rgba(245, 87, 108, 0.4);
    }
    
    /* RÉSULTAT */
    .result-box {
        background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
        padding: 25px;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin-top: 20px;
        white-space: pre-line;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);
    }
    
    /* BOÎTE PAIEMENT */
    .payment-box {
        background: linear-gradient(135deg, #f0f4ff 0%, #e8efff 100%);
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #667eea;
        margin-top: 20px;
        text-align: center;
    }
    
    /* BOUTON PAIEMENT FALLBACK */
    .pay-btn {
        display: block;
        text-align: center;
        padding: 16px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 12px;
        text-decoration: none;
        font-weight: 700;
        margin: 15px 0;
    }
    
    @media (max-width: 768px) {
        .main .block-container { padding: 1rem; border-radius: 15px; }
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
        "btn_payant": "💳 Payer et générer ma fiche (0,99€)",
        "essai_ok": "🎉 Bonne nouvelle ! Vous bénéficiez d'un **essai gratuit (1 fiche offerte)**.",
        "essai_utilise": "ℹ️ Essai déjà consommé. Prochaines fiches : **0,99€**.",
        "email_invalide": "❌ Veuillez entrer une adresse e-mail valide.",
        "genere_ok": "✨ Votre fiche gratuite a été générée avec succès !",
        "genere_spinner": "🤖 Génération en cours...",
        "resultat": "✨ Votre fiche produit générée :",
        "historique": "📋 Vos fiches générées",
        "remplir_champs": "⚠️ Veuillez remplir le nom et les caractéristiques.",
        "paiement_titre": "💳 Paiement sécurisé prêt !",
        "paiement_bouton": "🔒 Payer maintenant 0,99€ sur Stripe",
        "paiement_info": "Paiement 100% sécurisé par Stripe.",
        "paiement_erreur": "❌ Erreur Stripe :",
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
        "genere_ok": "✨ Your free sheet has been generated successfully!",
        "genere_spinner": "🤖 Generating...",
        "resultat": "✨ Your generated product sheet:",
        "historique": "📋 Your generated sheets",
        "remplir_champs": "⚠️ Please fill in the name and features.",
        "paiement_titre": "💳 Secure payment ready!",
        "paiement_bouton": "🔒 Pay now €0.99 on Stripe",
        "paiement_info": "100% secure payment by Stripe.",
        "paiement_erreur": "❌ Stripe error:",
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
        "btn_payant": "💳 Pagar y generar mi ficha (0,99€)",
        "essai_ok": "🎉 ¡Buenas noticias! Tienes una **prueba gratuita (1 ficha)**.",
        "essai_utilise": "ℹ️ Prueba ya usada. Próximas fichas: **0,99€**.",
        "email_invalide": "❌ Por favor introduce un correo válido.",
        "genere_ok": "✨ ¡Tu ficha gratuita se ha generado con éxito!",
        "genere_spinner": "🤖 Generando...",
        "resultat": "✨ Tu ficha de producto generada:",
        "historique": "📋 Tus fichas generadas",
        "remplir_champs": "⚠️ Por favor rellena el nombre y las características.",
        "paiement_titre": "💳 ¡Pago seguro listo!",
        "paiement_bouton": "🔒 Pagar ahora 0,99€ en Stripe",
        "paiement_info": "Pago 100% seguro por Stripe.",
        "paiement_erreur": "❌ Error de Stripe:",
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
# UTILISATEURS
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
if "user_count" not in st.session_state:
    st.session_state.user_count = 847
if "payment_url" not in st.session_state:
    st.session_state.payment_url = None

# ============================================
# 🤖 GÉNÉRATION IA (MODÈLES CORRIGÉS)
# ============================================
def generer_fiche_ia(nom, caracteristiques, ton, longueur, mots_cles, langue):
    prompt = f"""
    Tu es un expert en copywriting e-commerce et SEO.
    Rédige une fiche produit captivante et optimisée SEO.
    LA FICHE DOIT ÊTRE EN : {langue}.
    Produit: {nom}
    Caractéristiques: {caracteristiques}
    Ton: {ton}
    Longueur: {longueur}
    Mots-clés: {mots_cles}
    Structure: Titre accrocheur, intro bénéfices, liste avantages, appel à l'action.
    """
    # ✅ Modèles valides
    modeles = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    derniere_erreur = None
    
    for mod in modeles:
        try:
            response = client.models.generate_content(model=mod, contents=prompt)
            return response.text
        except Exception as e:
            derniere_erreur = str(e)
            continue
    
    return f"❌ Erreur : {derniere_erreur}"

# ============================================
# INTERFACE
# ============================================
st.markdown("## 🌍 Choose your language / Choisissez votre langue / Elige tu idioma")

langue_interface = st.selectbox(
    "Language / Langue / Idioma",
    list(TEXTES.keys()),
    key="langue_interface_select"
)

T = TEXTES[langue_interface]

st.write("---")

st.markdown(f'<div class="promo-badge">{T["promo"]}</div>', unsafe_allow_html=True)

st.title(T["titre"])
st.subheader(T["sous_titre"])

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric(label=T["metric_fiches"], value=st.session_state.generations)
with col_m2:
    st.metric(label=T["metric_users"], value=f"{st.session_state.user_count} (+12)")
with col_m3:
    st.metric(label=T["metric_prix"], value="0,99€")

st.write("---")

# ÉTAPE 1
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

        if not deja_utilise:
            st.success(T["essai_ok"])
            bouton_texte = T["btn_gratuit"]
            est_payant = False
        else:
            st.warning(T["essai_utilise"])
            bouton_texte = T["btn_payant"]
            est_payant = True

        st.write("---")

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

        if st.button(bouton_texte):
            if not nom_produit or not caracs:
                st.warning(T["remplir_champs"])
            else:
                if est_payant:
                    try:
                        locale_stripe = LOCALES_STRIPE.get(langue_interface, "auto")
                        session_stripe = stripe.checkout.Session.create(
                            payment_method_types=['card'],
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
                    with st.spinner(T["genere_spinner"]):
                        fiche_finale = generer_fiche_ia(
                            nom_produit, caracs, ton_choisi,
                            longueur_choisie, mots_cles, langue_choisie
                        )

                        if "❌" not in fiche_finale:
                            enregistrer_utilisateur(user_email, a_utilise_essai=True)
                            st.session_state.current_result = fiche_finale
                            st.session_state.generations += 1
                            st.session_state.generated_products.append({
                                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "nom": nom_produit,
                                "langue": langue_choisie,
                                "contenu": fiche_finale
                            })
                            st.success(T["genere_ok"])
                        else:
                            st.error(fiche_finale)

        # PAIEMENT
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

        # RÉSULTAT
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

        # HISTORIQUE
        if st.session_state.generated_products:
            st.write("---")
            st.markdown(f"### {T['historique']}")
            for prod in reversed(st.session_state.generated_products):
                with st.expander(f"📦 {prod['nom']} ({prod['langue']}) - {prod['date']}"):
                    st.markdown(prod['contenu'])
