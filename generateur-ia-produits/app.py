import streamlit as st
from google import genai

# Configuration de la page
st.set_page_config(page_title="Générateur IA Pro", page_icon="🛍️")

# 1. Gestion de la limitation gratuite
if "compteur_essais" not in st.session_state:
    st.session_state.compteur_essais = 0

# Configuration automatique du client GenAI via GEMINI_API_KEY
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Configuration API manquante. Veuillez vérifier votre GEMINI_API_KEY dans les Secrets Streamlit.")
    st.stop()

st.title("🛍️ Générateur de Fiches Produits E-Commerce")
st.write(f"Essais gratuits utilisés : **{st.session_state.compteur_essais} / 3**")

# 2. Vérification de la limite de gratuité
if st.session_state.compteur_essais >= 3:
    st.error("❌ Vous avez atteint la limite de 3 essais gratuits.")
    st.markdown("""
    ### 🔥 Libérez la puissance de l'IA pour votre boutique !
    Rédiger des fiches produits à la main vous prend trop de temps ? Un freelance vous coûte trop cher ? 
    
    Pour seulement **9,99€**, la version Pro vous offre :
    * 🚀 **Générations 100% illimitées** (zéro restriction)
    * 🎯 **Copywriting à haute conversion** (plus de ventes)
    * 📈 **Optimisation SEO** pour apparaître en premier sur Google
    * ⏰ **Un gain de temps massif** (15 minutes économisées par produit)
    """)
    
    # Bouton de paiement visuel (Remplacez par votre vrai lien Stripe ou PayPal entre les guillemets)
    lien_paiement = "https://buy.stripe.com/fZucN4dmn7TQ73eg3K8g002"
    
    st.markdown(f'<a href="{lien_paiement}" target="_blank" style="display: inline-block; padding: 14px 28px; background-color: #00D4B2; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; text-align: center; width: 100%;">🚀 Débloquer la Version Pro (9,99€)</a>', unsafe_allow_html=True)
    st.stop()

# 3. Interface de saisie
nom_produit = st.text_input("Nom du produit :", placeholder="Ex: Gourde isotherme")
caracteristiques = st.text_area("Caractéristiques :", placeholder="Ex: En inox, 750ml")



if st.button("🚀 Générer la fiche produit"):
    if nom_produit and caracteristiques:
        with st.spinner("L'IA rédige votre texte..."):
            try:
                prompt = f"Rédige une fiche produit e-commerce captivante pour : {nom_produit}. Caractéristiques : {caracteristiques}."
                
                # Utilisation du modèle officiel et universel du SDK google-genai
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                # Affichage immédiat du texte sur l'écran
                st.success("Généré avec succès !")
                st.markdown(response.text)
                
                # Incrémentation du compteur
                st.session_state.compteur_essais += 1
                
            except Exception as e:
                # Si une vraie erreur arrive, on l'affiche pour comprendre
                st.error(f"Une erreur technique est survenue : {e}")
    else:
        st.warning("Veuillez remplir tous les champs.")
