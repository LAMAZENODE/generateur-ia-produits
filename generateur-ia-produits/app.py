import streamlit as st
from google import genai
import json
import time
import stripe
import webbrowser

# ============================================
# CONFIGURATION
# ============================================
st.set_page_config(page_title="Générateur de Fiches Produits", page_icon="🛍️")

# Récupération des secrets
try:
    STRIPE_SECRET_KEY = st.secrets["STRIPE_SECRET_KEY"]
    STRIPE_PRICE_ID = st.secrets["STRIPE_PRICE_ID"]
    MON_URL_STREAMLIT = st.secrets["MON_URL_STREAMLIT"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    stripe.api_key = STRIPE_SECRET_KEY
except KeyError as e:
    st.error(f"❌ Secret manquant : {e}")
    st.stop()

# Configuration API Gemini
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"❌ Erreur API Gemini : {e}")
    st.stop()

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
if "payment_processing" not in st.session_state:
    st.session_state.payment_processing = False

# ============================================
# TITRE
# ============================================
st.title("🛍️ Créez votre fiche produit en 1 minute")
st.caption("🤖 Généré par IA · 0.99€ par fiche · 🔒 Paiement sécurisé")

# Statistiques
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
# PANIER ET PAIEMENT
# ============================================
if st.session_state.cart:
    st.divider()
    st.subheader("🛒 Votre panier")
    
    total = sum(item["prix"] for item in st.session_state.cart)
    quantity = len(st.session_state.cart)
    
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
        # ⭐ BOUTON DE PAIEMENT CORRIGÉ
        if st.button("💳 Payer maintenant", type="primary", use_container_width=True):
            try:
                # Créer la session Stripe
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
                
                # ⭐ Redirection avec météo HTML
                stripe_url = checkout_session.url
                
                # Afficher une page de redirection
                st.markdown(f'''
                <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: white; z-index: 9999; display: flex; justify-content: center; align-items: center;">
                    <div style="text-align: center; max-width: 500px; padding: 20px;">
                        <h2 style="margin-bottom: 10px;">🔒 Paiement sécurisé</h2>
                        <p style="color: #666; margin-bottom: 20px;">Redirection vers Stripe en cours...</p>
                        <div style="border: 4px solid #f3f3f3; border-top: 4px solid #635bff; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 20px auto;"></div>
                        <a href="{stripe_url}" target="_blank" style="display: inline-block; margin-top: 20px; padding: 12px 24px; background: #635bff; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
                            💳 Cliquez ici si la redirection ne fonctionne pas
                        </a>
                        <p style="margin-top: 15px; font-size: 12px; color: #999;">🔒 Paiement sécurisé par Stripe</p>
                    </div>
                </div>
                <style>
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                </style>
                <script>
                    // Redirection automatique après 1 seconde
                    setTimeout(function() {{
                        window.location.href = "{stripe_url}";
                    }}, 1000);
                </script>
                ''', unsafe_allow_html=True)
                
                # ⭐ Arrêter l'exécution pour éviter l'affichage du reste
                st.stop()
                
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
                st.code(str(e))

    st.caption("🔒 Paiement sécurisé par Stripe")

# ============================================
# TRAITEMENT APRÈS PAIEMENT
# ============================================
if st.query_params.get("payment") == "success":
    st.query_params.clear()
    st.success("✅ Paiement accepté ! Génération...")
    
    if st.session_state.cart:
        progress_bar = st.progress(0)
        for idx, item in enumerate(st.session_state.cart):
            progress_bar.progress((idx + 1) / len(st.session_state.cart))
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
        time.sleep(2)
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
