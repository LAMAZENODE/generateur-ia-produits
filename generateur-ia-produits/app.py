import streamlit as st
from google import genai
import json
import time
import stripe

# ============================================
# CONFIGURATION
# ============================================
st.set_page_config(page_title="Générateur IA Pro", page_icon="🛍️")

# Récupération des secrets
try:
    STRIPE_SECRET_KEY = st.secrets["STRIPE_SECRET_KEY"]
    STRIPE_PRICE_ID = st.secrets["STRIPE_PRICE_ID"]
    MON_URL_STREAMLIT = st.secrets["MON_URL_STREAMLIT"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # Configuration Stripe
    stripe.api_key = STRIPE_SECRET_KEY
    
    st.sidebar.success("✅ Stripe connecté")
    st.sidebar.info(f"💰 Prix: {STRIPE_PRICE_ID}")
    
except KeyError as e:
    st.error(f"❌ Secret manquant : {e}")
    st.stop()

# Configuration du client API Google GenAI
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    st.sidebar.success("✅ API Gemini connectée")
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
# INTERFACE PRINCIPALE
# ============================================
st.title("🛍️ Générateur de Fiches Produits")
st.write("💰 **Paiement réel avec Stripe** - 0,99€ par fiche")

# Statistiques
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📝 Générations", st.session_state.generations)
with col2:
    st.metric("💳 Dépensé", f"{st.session_state.total_spent:.2f} €")
with col3:
    st.metric("📦 Produits", len(st.session_state.generated_products))

# ============================================
# AJOUT AU PANIER
# ============================================
st.subheader("📝 Nouvelle fiche produit")

nom_produit = st.text_input("Nom du produit :", placeholder="Ex: Robe en cuir")
caracteristiques = st.text_area("Caractéristiques :", placeholder="Ex: Matière: Cuir véritable, Couleur: Noir")

if st.button("➕ Ajouter au panier", type="secondary"):
    if nom_produit and caracteristiques:
        st.session_state.cart.append({
            "nom": nom_produit,
            "caracteristiques": caracteristiques,
            "prix": 0.99
        })
        st.success(f"✅ {nom_produit} ajouté au panier (0.99€)")
        st.balloons()
    else:
        st.warning("⚠️ Remplissez tous les champs")

# ============================================
# PANIER ET PAIEMENT
# ============================================
if st.session_state.cart:
    st.subheader("🛒 Votre panier")
    total = sum(item["prix"] for item in st.session_state.cart)
    quantity = len(st.session_state.cart)
    
    # Liste des articles
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3 = st.columns([3, 1, 0.5])
        with col1:
            st.write(f"**{item['nom']}**")
        with col2:
            st.write(f"{item['prix']:.2f} €")
        with col3:
            if st.button("🗑️", key=f"remove_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
    
    st.divider()
    st.write(f"**Total : {total:.2f} €**")
    st.write(f"**Quantité : {quantity} fiche(s)**")
    
    # ============================================
    # PAIEMENT STRIPE AVEC PRICE_ID
    # ============================================
    st.info("💳 Paiement sécurisé par Stripe")
    
    if st.button("💳 Payer avec Stripe", type="primary", use_container_width=True):
        try:
            # Créer la session de paiement Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': STRIPE_PRICE_ID,  # Votre Price ID
                    'quantity': quantity,      # Nombre de fiches
                }],
                mode='payment',
                success_url=f"{MON_URL_STREAMLIT}?payment=success",
                cancel_url=f"{MON_URL_STREAMLIT}?payment=cancel",
                metadata={
                    'quantity': quantity,
                    'products': json.dumps([
                        {'nom': item['nom']} 
                        for item in st.session_state.cart
                    ])
                }
            )
            
            # Stocker l'ID de session
            st.session_state.checkout_session_id = checkout_session.id
            
            # Redirection vers Stripe avec JavaScript
            st.markdown(f'''
            <div style="text-align: center; padding: 30px; background-color: #f0f0f0; border-radius: 10px;">
                <h3>🔒 Redirection vers Stripe...</h3>
                <p>Veuillez patienter, vous allez être redirigé vers la page de paiement sécurisée.</p>
                <br>
                <a href="{checkout_session.url}" target="_blank" style="display: inline-block; padding: 12px 24px; background-color: #635bff; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    💳 Cliquez ici si la redirection ne fonctionne pas
                </a>
                <br><br>
                <small>⚠️ Ne fermez pas cette page pendant le paiement.</small>
            </div>
            <script>
                setTimeout(function() {{
                    window.location.href = "{checkout_session.url}";
                }}, 1000);
            </script>
            ''', unsafe_allow_html=True)
            
            st.session_state.payment_processing = True
            
        except stripe.error.AuthenticationError:
            st.error("❌ Erreur d'authentification Stripe. Vérifiez votre clé secrète.")
        except stripe.error.InvalidRequestError as e:
            st.error(f"❌ Erreur de requête Stripe : {e}")
        except Exception as e:
            st.error(f"❌ Erreur de paiement : {e}")

# ============================================
# TRAITEMENT APRÈS PAIEMENT RÉUSSI
# ============================================
if st.query_params.get("payment") == "success":
    st.success("✅ Paiement accepté ! Génération des fiches produits...")
    st.query_params.clear()
    
    # Vider le panier après paiement réussi
    if st.session_state.cart:
        with st.spinner("Génération des fiches produits..."):
            progress_bar = st.progress(0)
            
            for idx, item in enumerate(st.session_state.cart):
                progress_bar.progress((idx + 1) / len(st.session_state.cart))
                
                try:
                    prompt = f"""Rédige une fiche produit e-commerce captivante pour : {item['nom']}.
                    Caractéristiques : {item['caracteristiques']}.
                    
                    Structure la réponse avec :
                    - Titre accrocheur
                    - Description détaillée (100-150 mots)
                    - Caractéristiques techniques (tableau)
                    - Avantages (3 points)
                    - Appel à l'action
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.0-flash-exp',
                        contents=prompt,
                    )
                    
                    st.session_state.generated_products.append({
                        "nom": item['nom'],
                        "contenu": response.text,
                        "prix": 0.99,
                        "date": time.strftime("%d/%m/%Y %H:%M")
                    })
                    st.session_state.generations += 1
                    st.session_state.total_spent += 0.99
                    
                except Exception as e:
                    st.error(f"❌ Erreur pour {item['nom']} : {e}")
            
            st.session_state.cart = []
            st.session_state.payment_processing = False
            st.success("🎉 Toutes les fiches ont été générées !")
            st.balloons()
            time.sleep(2)
            st.rerun()
    else:
        st.warning("⚠️ Panier vide. Rien à générer.")

if st.query_params.get("payment") == "cancel":
    st.warning("⚠️ Paiement annulé")
    st.query_params.clear()
    st.session_state.payment_processing = False

# ============================================
# PRODUITS GÉNÉRÉS
# ============================================
if st.session_state.generated_products:
    st.subheader("📦 Mes fiches produits")
    
    for i, product in enumerate(st.session_state.generated_products):
        with st.expander(f"📄 {product['nom']} - {product['date']}"):
            st.markdown(product['contenu'])
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                if st.button("📋 Copier", key=f"copy_{i}"):
                    st.info("💡 Sélectionnez le texte et faites Ctrl+C")
            with col2:
                if st.button("📥 Télécharger TXT", key=f"download_{i}"):
                    st.download_button(
                        label="📥 Télécharger",
                        data=product['contenu'],
                        file_name=f"{product['nom']}_fiche.txt",
                        mime="text/plain"
                    )
            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.generated_products.pop(i)
                    st.rerun()
    
    # Export JSON de toutes les fiches
    if st.button("📥 Exporter tout en JSON"):
        export_data = {
            "total_generations": st.session_state.generations,
            "total_spent": st.session_state.total_spent,
            "products": st.session_state.generated_products
        }
        st.download_button(
            label="📥 Télécharger JSON",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name="mes_fiches_produits.json",
            mime="application/json"
        )

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.write("### 💳 Stripe")
    st.success("✅ Mode Production")
    st.caption(f"Price ID: {STRIPE_PRICE_ID}")
    
    st.write("### 🏷️ Produit Stripe")
    st.write("**Fiche produit e-commerce**")
    st.write("Prix: **0.99€**")
    
    st.write("### 🤖 IA")
    st.write("**Gemini 2.0 Flash**")
    
    st.write("### 📦 Panier")
    if st.session_state.cart:
        st.write(f"**{len(st.session_state.cart)}** article(s)")
        st.write(f"Total : **{sum(item['prix'] for item in st.session_state.cart):.2f} €**")
    else:
        st.write("Vide")
    
    st.divider()
    st.write("### 📊 Statistiques")
    st.write(f"Générations: {st.session_state.generations}")
    st.write(f"Dépensé: {st.session_state.total_spent:.2f} €")
    st.write(f"Produits: {len(st.session_state.generated_products)}")

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🔒 Paiement sécurisé par Stripe • 0.99€ par fiche produit")

    
    


