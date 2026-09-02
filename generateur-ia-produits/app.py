import streamlit as st
from google import genai
import stripe
import json
import time

# Configuration de la page
st.set_page_config(page_title="Générateur IA Pro - Pay per Use", page_icon="🛍️")

# Configuration Stripe
try:
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
    stripe_public_key = st.secrets["STRIPE_PUBLIC_KEY"]
except Exception:
    st.warning("Configuration Stripe manquante. Mode démo activé.")

# Configuration du client API
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Configuration API manquante.")
    st.stop()

# Gestion du panier / session
if "cart" not in st.session_state:
    st.session_state.cart = []
if "generations" not in st.session_state:
    st.session_state.generations = 0
if "total_spent" not in st.session_state:
    st.session_state.total_spent = 0
if "generated_products" not in st.session_state:
    st.session_state.generated_products = []

st.title("🛍️ Générateur de Fiches Produits")
st.write("💰 **Paiement à l'utilisation** - Payez uniquement pour ce que vous générez !")

# Statistiques de la session
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📝 Générations", st.session_state.generations)
with col2:
    st.metric("💳 Dépensé", f"{st.session_state.total_spent:.2f} €")
with col3:
    st.metric("📦 Total produits", len(st.session_state.generated_products))

# Prix par génération
PRICE_PER_GENERATION = 0.99  # 0,99€ par fiche produit

# Interface de saisie
st.subheader("📝 Nouvelle fiche produit")

nom_produit = st.text_input("Nom du produit :", placeholder="Ex: Gourde isotherme en acier inoxydable")
caracteristiques = st.text_area("Caractéristiques :", placeholder="Ex: Matière: Inox 304, Capacité: 750ml, Isolation: Double paroi")

# Ajouter au panier
if st.button("➕ Ajouter au panier", type="secondary"):
    if nom_produit and caracteristiques:
        st.session_state.cart.append({
            "nom": nom_produit,
            "caracteristiques": caracteristiques,
            "prix": PRICE_PER_GENERATION
        })
        st.success(f"✅ {nom_produit} ajouté au panier ({PRICE_PER_GENERATION}€)")
        st.balloons()
    else:
        st.warning("⚠️ Remplissez tous les champs")

# Affichage du panier
if st.session_state.cart:
    st.subheader("🛒 Votre panier")
    
    total = sum(item["prix"] for item in st.session_state.cart)
    
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
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Total : {total:.2f} €**")
    with col2:
        # Bouton de paiement
        st.markdown(f'''
        <div style="text-align: right;">
            <button onclick="window.location.href='#checkout'" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
                💳 Payer {total:.2f} €
            </button>
        </div>
        ''', unsafe_allow_html=True)
    
    # Intégration Stripe (pour paiement réel)
    st.subheader("💳 Paiement sécurisé")
    
    # Option 1: Stripe Checkout (recommandé)
    if st.button("💳 Payer avec Stripe", type="primary"):
        try:
            # Créer une session de paiement Stripe
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f"Fiches produits ({len(st.session_state.cart)} générations)",
                            'description': f"Génération de {len(st.session_state.cart)} fiches produits",
                        },
                        'unit_amount': int(total * 100),  # En centimes
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://votre-app.streamlit.app/success',
                cancel_url='https://votre-app.streamlit.app/cancel',
            )
            
            # Rediriger vers Stripe
            st.markdown(f'<meta http-equiv="refresh" content="0;url={session.url}">', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erreur de paiement : {e}")
    
    # Option 2: Paiement simulé (pour démonstration)
    if st.button("🎮 Paiement de démonstration (simulé)", type="secondary"):
        with st.spinner("Traitement du paiement..."):
            time.sleep(2)
            st.success("✅ Paiement accepté ! Génération des fiches produits...")
            
            # Générer toutes les fiches produits
            for item in st.session_state.cart:
                with st.spinner(f"Génération de {item['nom']}..."):
                    try:
                        prompt = f"""Rédige une fiche produit e-commerce captivante et professionnelle pour : {item['nom']}. 
                        Caractéristiques : {item['caracteristiques']}.
                        
                        Structure la réponse avec :
                        - Un titre accrocheur
                        - Une description détaillée
                        - Les caractéristiques techniques en tableau
                        - Les avantages produits
                        - Un appel à l'action
                        """
                        
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=prompt,
                        )
                        
                        st.session_state.generated_products.append({
                            "nom": item['nom'],
                            "contenu": response.text,
                            "prix": item['prix']
                        })
                        st.session_state.generations += 1
                        st.session_state.total_spent += item['prix']
                        
                    except Exception as e:
                        st.error(f"Erreur pour {item['nom']} : {e}")
            
            # Vider le panier
            st.session_state.cart = []
            st.success("🎉 Toutes les fiches produits ont été générées !")
            st.balloons()
            st.rerun()

# Afficher les produits générés
if st.session_state.generated_products:
    st.subheader("📦 Mes fiches produits")
    
    for i, product in enumerate(st.session_state.generated_products):
        with st.expander(f"📄 {product['nom']} ({product['prix']:.2f}€)"):
            st.markdown(product['contenu'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Copier", key=f"copy_{i}"):
                    st.info("Texte copié dans le presse-papier")
            with col2:
                if st.button("🗑️ Supprimer", key=f"delete_{i}"):
                    st.session_state.generated_products.pop(i)
                    st.rerun()
    
    # Export de toutes les fiches
    if st.button("📥 Exporter toutes les fiches en JSON"):
        export_data = {
            "total_generations": st.session_state.generations,
            "total_spent": st.session_state.total_spent,
            "products": st.session_state.generated_products
        }
        st.download_button(
            label="📥 Télécharger le fichier JSON",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name="mes_fiches_produits.json",
            mime="application/json"
        )

# Sections informatives
with st.expander("💳 Comment ça marche ?"):
    st.markdown(f"""
    ### 📝 Comment utiliser ce service ?
    
    1. **Saisissez** les informations de votre produit
    2. **Ajoutez** au panier (autant de fois que vous voulez !)
    3. **Payez** uniquement pour les fiches que vous voulez générer
    4. **Recevez** vos fiches produits immédiatement
    
    ### 💰 Tarifs
    - **{PRICE_PER_GENERATION}€** par fiche produit
    - Pas d'abonnement
    - Pas de limite de générations
    - Payez autant de fois que vous voulez
    
    ### ✅ Avantages
    - ✅ Pas de limite mensuelle
    - ✅ Paiement sécurisé
    - ✅ Génération instantanée
    - ✅ Fiches professionnelles
    """)

with st.expander("📊 Statistiques de l'utilisateur"):
    st.write("**Votre activité**")
    st.write(f"- Nombre de fiches générées : {st.session_state.generations}")
    st.write(f"- Montant total dépensé : {st.session_state.total_spent:.2f} €")
    st.write(f"- Nombre de produits dans votre bibliothèque : {len(st.session_state.generated_products)}")
    
    if st.button("🔄 Réinitialiser mes données"):
        st.session_state.cart = []
        st.session_state.generations = 0
        st.session_state.total_spent = 0
        st.session_state.generated_products = []
        st.rerun()

# Sidebar avec configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.write("### 💳 Informations de paiement")
    st.write("Prix par génération : **0,99€**")
    
    st.write("### 📦 Panier")
    if st.session_state.cart:
        st.write(f"**{len(st.session_state.cart)}** article(s)")
        st.write(f"Total : **{sum(item['prix'] for item in st.session_state.cart):.2f} €**")
    else:
        st.write("Votre panier est vide")
    
    st.divider()
    st.write("### 🔗 Liens utiles")
    st.markdown("- [Conditions d'utilisation](#)")
    st.markdown("- [FAQ](#)")
    st.markdown("- [Support](#)")


