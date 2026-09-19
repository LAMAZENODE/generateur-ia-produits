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
    page_title="Générateur de Fiches Produits - IA",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Mobile First avec support desktop
st.markdown("""
<style>
    .stApp { max-width: 100%; padding: 0.5rem; }
    .stButton button {
        border-radius: 10px !important; padding: 12px !important;
        font-size: 16px !important; font-weight: 600 !important;
        transition: all 0.3s ease; width: 100%;
        background-color: #6772e5 !important; color: white !important;
    }
    .stTextInput input, .stTextArea textarea {
        font-size: 16px !important; padding: 12px !important; border-radius: 10px !important;
    }
    .stMetric { background: #f8f9fa; padding: 8px; border-radius: 10px; text-align: center; }
    @media (min-width: 769px) {
        .stApp { padding: 1rem 2rem; }
        .stButton button { padding: 14px !important; font-size: 18px !important; }
        h1 { font-size: 36px !important; }
    }
    .promo-badge {
        background-color: #ff4b4b; color: white; padding: 12px; border-radius: 10px;
        text-align: center; font-weight: bold; margin-bottom: 20px; font-size: 16px;
    }
    .result-box {
        background-color: #f1f3f9; padding: 20px; border-radius: 10px;
        border-left: 5px solid #6772e5; margin-top: 20px;
        white-space: pre-line;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALISATION DES SECRETS & API
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
# GESTION LOCALE DES UTILISATEURS (ESSAI GRATUIT)
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
# STATE DE SESSION
# ============================================
if "generations" not in st.session_state:
    st.session_state.generations = 0
if "generated_products" not in st.session_state:
    st.session_state.generated_products = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "user_count" not in st.session_state:
    st.session_state.user_count = 847

st.session_state.promo_badge = "🎁 Votre 1ère fiche 100% Gratuite · Puis Offre flash : 5 fiches pour le prix de 4 !"

# ============================================
# FONCTION GÉNÉRATION IA
# ============================================
def generer_fiche_ia(nom, caracteristiques, ton, longueur, mots_cles, langue):
    prompt = f"""
    Tu es un expert en copywriting e-commerce et en SEO.
    Rédige une fiche produit captivante, vendeuse et optimisée pour les moteurs de recherche.
    LA FICHE PRODUIT DOIT IMPÉRATIVEMENT ÊTRE RÉDIGÉE EN : {langue}.
    Si la langue est l'Arabe, adapte la structure globale de droite à gauche.
    Produit: {nom}, Caractéristiques: {caracteristiques}, Ton: {ton}, Longueur: {longueur}, Mots-clés: {mots_cles}.
    Structure attendue: Titre accrocheur, introduction bénéfices, liste à puces avantages, appel à l'action.
    """
    modeles = ['gemini-3.6-flash', 'gemini-2.5-flash']
    for mod in modeles:
        try:
            response = client.models.generate_content(model=mod, contents=prompt)
            return response.text
        except Exception:
            continue
    return "❌ Serveurs saturés, veuillez réessayer dans un instant."

# ============================================
# INTERFACE UTILISATEUR
# ============================================
st.markdown(f'<div class="promo-badge">{st.session_state.promo_badge}</div>', unsafe_allow_html=True)

st.title("🛍️ Fiche Produit")
st.subheader("Générez des fiches produits professionnelles en 30 secondes")

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric(label="📝 Vos Fiches Générées", value=st.session_state.generations)
with col_m2:
    st.metric(label="👥 Utilisateurs Actifs", value=f"{st.session_state.user_count} (+12)")
with col_m3:
    st.metric(label="💰 Prix par fiche", value="0,99€")

st.write("---")

# ÉTAPE 1 : IDENTIFICATION PAR E-MAIL
st.markdown("### 🔑 Étape 1 : Entrez votre adresse e-mail")
user_email = st.text_input("Votre e-mail pour activer ou suivre vos fiches *", placeholder="exemple@domaine.com").strip().lower()

if user_email:
    if not valider_email(user_email):
        st.error("❌ Veuillez entrer une adresse e-mail valide.")
    else:
        db_utilisateurs = charger_utilisateurs()
        deja_utilise = user_email in db_utilisateurs and db_utilisateurs[user_email].get("a_utilise_essai", False)
        
        if not deja_utilise:
            st.success("🎉 Bonne nouvelle ! Vous bénéficiez d'un **essai gratuit (1 fiche offerte)** avec cet e-mail.")
            bouton_texte = "🚀 Générer ma fiche gratuite (Essai offert)"
            est_payant = False
        else:
            st.warning("ℹ️ Vous avez déjà consommé votre essai gratuit. Les prochaines fiches sont à **0,99€** via paiement sécurisé.")
            bouton_texte = "💳 Payer et générer ma fiche (0,99€)"
            est_payant = True

        st.write("---")
        
        # ÉTAPE 2 : LE FORMULAIRE DE CRÉATION
        st.markdown("### 📝 Étape 2 : Détails du produit")
        col_form1, col_form2 = st.columns(2)

        with col_form1:
            nom_produit = st.text_input("Nom du produit *", placeholder="Ex: Sac en cuir")
            caracs = st.text_area("Caractéristiques *", placeholder="Ex: Cuir véritable, noir")

        with col_form2:
            langues = ["Français 🇫🇷", "Anglais 🇬🇧", "Espagnol 🇪🇸", "Allemand 🇩🇪", "Italien 🇮🇹", "Arabe 🇸🇦"]
            langue_choisie = st.selectbox("Langue de rédaction *", langues)
            ton_choisi = st.selectbox("Ton éditorial", ["Professionnel", "Luxe", "Chaleureux", "Minimaliste"])
            longueur_choisie = st.selectbox("Longueur de la fiche", ["Courte", "Moyenne", "Détaillée"])

        with st.expander("⚙️ Options avancées"):
            mots_cles = st.text_input("Mots-clés SEO", placeholder="Ex: sac durable")

        st.write("")

        # BOUTON D'ACTION DYNAMIQUE
        if st.button(bouton_texte):
            if not nom_produit or not caracs:
                st.warning("⚠️ Veuillez remplir le nom et les caractéristiques.")
            else:
                if est_payant:
                    try:
                        session_stripe = stripe.checkout.Session.create(
                            payment_method_types=['card'],
                            line_items=[{
                                'price': STRIPE_PRICE_ID,
                                'quantity': 1,
                            }],
                            mode='payment',
                            success_url=f"{MON_URL_STREAMLIT}?payment=success&email={user_email}",
                            cancel_url=MON_URL_STREAMLIT,
                            customer_email=user_email
                        )
                        st.markdown(f"📲 [Cliquez ici pour procéder au paiement sécurisé Stripe]({session_stripe.url})")
                        st.info("Une fois le paiement effectué, vous serez redirigé pour voir votre fiche.")
                    except Exception as e:
                        st.error(f"❌ Erreur avec le système Stripe : {str(e)}")
                else:
                    # CORRECTION : Génération et affichage immédiat sans st.rerun() brusque
                    with st.spinner("🤖 Génération de votre fiche gratuite en cours..."):
                        fiche_finale = generer_fiche_ia(nom_produit, caracs, ton_choisi, longueur_choisie, mots_cles, langue_choisie)
                        
                        if "❌" not in fiche_finale:
                            # Sauvegarde du blocage de l'essai
                            enregistrer_utilisateur(user_email, a_utilise_essai=True)
                            
                            st.session_state.current_result = fiche_finale
                            st.session_state.generations += 1
                            st.session_state.generated_products.append({
                                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "nom": nom_produit,
                                "langue": langue_choisie,
                                "contenu": fiche_finale
                            })
                            st.success("✨ Votre fiche gratuite a été générée avec succès !")
                        else:
                            st.error(fiche_finale)


                # ZONE D'AFFICHAGE DU RÉSULTAT DIRECT
        if st.session_state.current_result:
            st.write("---")
            st.markdown("### ✨ Votre fiche produit générée :")
            
            if "Arabe" in langue_choisie or "🇸🇦" in langue_choisie:
                st.markdown(f'<div class="result-box" style="direction: rtl; text-align: right;">{st.session_state.current_result}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="result-box">{st.session_state.current_result}</div>', unsafe_allow_html=True)

        # HISTORIQUE DES SESSIONS
        if st.session_state.generated_products:
            st.write("---")
            st.markdown("### 📋 Vos fiches générées")
            for prod in reversed(st.session_state.generated_products):
                with st.expander(f"📦 {prod['nom']} ({prod['langue']}) - {prod['date']}"):
                    if "Arabe" in prod['langue'] or "🇸🇦" in prod['langue']:
                        st.markdown(f'<div style="direction: rtl; text-align: right;">{prod["contenu"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(prod['contenu']
