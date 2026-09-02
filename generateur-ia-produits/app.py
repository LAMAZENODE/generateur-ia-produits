import streamlit as st
from google import genai
import json
import time
import stripe

# ============================================
# CONFIGURATION
# ============================================
st.set_page_config(page_title="Générateur de Fiches Produits", page_icon="🛍️")

# Récupération des secrets
STRIPE_SECRET_KEY = st.secrets["STRIPE_SECRET_KEY"]
STRIPE_PRICE_ID = st.secrets["STRIPE_PRICE_ID"]
MON_URL_STREAMLIT = st.secrets["MON_URL_STREAMLIT"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

stripe.api_key = STRIPE_SECRET_KEY
client = genai.Client(api_key=GEMINI_API_KEY)

# ============================================
# SESSION STATE
# ============================================
if "cart" not in st.session_state:
    st.session_state.cart = []
if "generations" not in st.session_state:
    st.session_state.generations = 0
if "total_spent" not in st.session_state:
    st.session_state.total_spent = 0
if "generated_products" not in st.session_state:
    st.session_state.generated_products = []

# ============================================
# TITRE ET STATISTIQUES SIMPLIFIÉES
# ============================================
st.title("🛍️ Créez votre fiche produit en 1 minute")
st.caption("🤖 Généré par IA · 0.99€ par fiche · 🔒 Paiement sécurisé")

col1, col2 = st.columns(2)
with col1:
    st.metric("📝 Fiches créées", st.session_state.generations)
with col2:
    st.metric("💰 Dépensé", f"{st.session_state.total_spent:.2f}€")

# ============================================
# FORMULAIRE PRODUIT
# ============================================
st.subheader("📝 Nouvelle fiche produit")

with st.container(border=True):
    nom_produit = st.text_input("Nom du produit *", placeholder="Ex: Sac en cuir")
    caracteristiques = st.text_area("Caractéristiques *", placeholder="Ex: Cuir véritable, 30x25cm, noir")

    if st.button("➕ Ajouter au panier", type="secondary", use_container_width=True):
        if nom_produit and caracteristiques:
            st.session_state.cart.append({
                "nom": nom_produit,
                "caracteristiques": caracteristiques,
                "prix": 0.99
            })
            st.success(f"✅ {nom_produit} ajouté !")
            st.balloons()
            st.rerun()
        else:
            st.warning("⚠️ Remplissez tous les champs")

# ============================================
# PANIER - SIMPLIFIÉ
# ============================================
if st.session_state.cart:
    st.divider()
    st.subheader("🛒 Votre panier")
    
    total = sum(item["prix"] for item in st.session_state.cart)
    quantity = len(st.session_state.cart)
    
    # Liste des articles
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3 = st.columns([3, 1, 0.3])
        with col1:
            st.write(f"**{item['nom']}**")
        with col2:
            st.write(f"{item['prix']:.2f}€")
        with col3:
            if st.button("✕", key=f"remove_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
    
    st.divider()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**Total : {total:.2f}€**")
        st.caption(f"{quantity} fiche(s)")
    
    with col2:
        # BOUTON DE PAIEMENT CLAIR
        if st.button("💳 Payer maintenant", type="primary", use_container_width=True):
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price': STRIPE_PRICE_ID,
                        'quantity': quantity,
                    }],
                    mode='payment',
                    success_url=f"{MON_URL_STREAMLIT}?payment=success",
                    cancel_url=f"{MON_URL_STREAMLIT}?payment=cancel",
                )
                
                st.markdown(f'''
                <meta http-equiv="refresh" content="0;url={checkout_session.url}">
                <div style="text-align:center; padding:20px;">
                    <p>🔒 Redirection vers Stripe...</p>
                    <a href="{checkout_session.url}" target="_blank">Cliquez ici</a>
                </div>
                ''', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Erreur : {e}")
    
    st.caption("🔒 Paiement sécurisé par Stripe")

# ============================================
# TRAITEMENT APRÈS PAIEMENT
# ============================================
if st.query_params.get("payment") == "success":
    st.query_params.clear()
    st.success("✅ Paiement accepté ! Génération...")
    
    if st.session_state.cart:
        for item in st.session_state.cart:
            try:
                prompt = f"""Rédige une fiche produit pour : {item['nom']}.
                Caractéristiques : {item['caracteristiques']}.
                Structure : Titre, Description, Caractéristiques techniques, Avantages.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt,
                )
                
                st.session_state.generated_products.append({
                    "nom": item['nom'],
                    "contenu": response.text,
                    "prix": 0.99
                })
                st.session_state.generations += 1
                st.session_state.total_spent += 0.99
                
            except Exception as e:
                st.error(f"Erreur pour {item['nom']}")
        
        st.session_state.cart = []
        st.success("🎉 Fiche(s) générée(s) !")
        st.balloons()
        st.rerun()

# ============================================
# PRODUITS GÉNÉRÉS
# ============================================
if st.session_state.generated_products:
    st.divider()
    st.subheader("📦 Mes fiches produits")
    
    for i, product in enumerate(st.session_state.generated_products):
        with st.expander(f"📄 {product['nom']}"):
            st.markdown(product['contenu'])
            if st.button("🗑️ Supprimer", key=f"del_{i}"):
                st.session_state.generated_products.pop(i)
                st.rerun()
    
    if st.button("📥 Exporter tout"):
        export_data = {"products": st.session_state.generated_products}
        st.download_button(
            label="Télécharger JSON",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name="fiches.json",
            mime="application/json"
        )
