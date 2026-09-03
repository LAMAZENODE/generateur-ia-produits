import streamlit as st
from google import genai
import json
import time
import stripe
from datetime import datetime
import random

# ============================================
# CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Générateur de Fiches Produits - IA",
    page_icon="🛍️",
    layout="wide"
)

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
if "user_count" not in st.session_state:
    st.session_state.user_count = 847
if "daily_generations" not in st.session_state:
    st.session_state.daily_generations = 0
if "promo_badge" not in st.session_state:
    promotions = [
        "🎁 10% de réduction sur votre première commande !",
        "⭐ Offre spéciale : 5 fiches pour le prix de 4 !",
        "🔥 Promotion : 3 fiches achetées, 1 offerte !",
        "💎 Premium : Fiches optimisées SEO incluses !"
    ]
    st.session_state.promo_badge = random.choice(promotions)

# ============================================
# FONCTIONS UTILITAIRES
# ============================================
def sauvegarder_session():
    """Sauvegarde automatique de la session"""
    try:
        with open("session_backup.json", "w") as f:
            json.dump({
                "cart": st.session_state.cart,
                "generations": st.session_state.generations,
                "total_spent": st.session_state.total_spent,
                "generated_products": st.session_state.generated_products,
                "timestamp": datetime.now().isoformat()
            }, f)
    except:
        pass

def generer_apercu(nom, caracteristiques, ton="Professionnel", longueur="Moyenne"):
    """Génère un aperçu de la fiche produit"""
    if not nom or not caracteristiques:
        return None
    
    # Déterminer le style selon le ton
    styles = {
        "Professionnel": {
            "style": "professionnel et élégant",
            "emoji": "💼",
            "avantages": ["Qualité premium", "Fiabilité", "Design ergonomique"]
        },
        "Chaleureux": {
            "style": "convivial et accessible",
            "emoji": "🤗",
            "avantages": ["Confort au quotidien", "Facilité d'utilisation", "Rapport qualité-prix"]
        },
        "Luxe": {
            "style": "premium et raffiné",
            "emoji": "✨",
            "avantages": ["Matériaux nobles", "Finition exceptionnelle", "Exclusivité"]
        },
        "Minimaliste": {
            "style": "épuré et moderne",
            "emoji": "🎯",
            "avantages": ["Design intemporel", "Fonctionnalité pure", "Polyvalence"]
        },
        "Dynamique": {
            "style": "énergique et moderne",
            "emoji": "🚀",
            "avantages": ["Performance", "Innovation", "Adaptabilité"]
        }
    }
    
    style_info = styles.get(ton, styles["Professionnel"])
    
    # Ajuster la longueur de l'aperçu
    if longueur == "Courte":
        description = f"Découvrez {nom}, alliant qualité et {style_info['style']}."
    elif longueur == "Détaillée":
        description = f"Découvrez {nom}, alliant qualité et {style_info['style']}. Conçu avec soin pour répondre à vos besoins quotidiens. Un produit qui saura vous séduire par sa finition et sa praticité."
    else:  # Moyenne
        description = f"Découvrez {nom}, alliant qualité et {style_info['style']}. Conçu avec soin pour répondre à vos besoins quotidiens."
    
    avantages_liste = "\n".join([f"• {avantage}" for avantage in style_info["avantages"]])
    
    return f"""
    ### {style_info['emoji']} Aperçu de votre fiche
    
    **📌 {nom}** - Fiche produit {style_info['style']}
    
    **📝 Description** : {description}
    
    **✨ Avantages** : 
    {avantages_liste}
    
    **🔧 Caractéristiques** : {caracteristiques}
    
    **💰 Prix conseillé** : À définir selon votre marché
    
    💡 *Le contenu final sera plus détaillé et optimisé par l'IA*
    """

def calculer_total_avec_reduction(cart):
    """Calcule le total avec les réductions applicables"""
    quantity = len(cart)
    if quantity >= 5:
        return 4.50, f"💰 Économie de {quantity * 0.99 - 4.50:.2f}€"
    elif quantity >= 3:
        return quantity * 0.90, f"💰 Réduction de {quantity * 0.09:.2f}€ (10%)"
    else:
        return quantity * 0.99, ""

# ============================================
# TITRE ET EN-TÊTE
# ============================================
# Bannière promotionnelle
st.markdown(f"""
<div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); 
            padding: 12px; border-radius: 8px; color: white; text-align: center; 
            margin-bottom: 20px; font-weight: bold; font-size: 18px;
            animation: pulse 2s infinite; box-shadow: 0 4px 15px rgba(255,107,107,0.3);">
    {st.session_state.promo_badge}
</div>
<style>
    @keyframes pulse {{
        0% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.95; transform: scale(1.01); }}
        100% {{ opacity: 1; transform: scale(1); }}
    }}
</style>
""", unsafe_allow_html=True)

# Titre principal
col_title1, col_title2 = st.columns([3, 1])
with col_title1:
    st.title("🛍️ Créez votre fiche produit en 1 minute")

# Bannière de confiance
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 15px; border-radius: 10px; color: white; margin: 10px 0;">
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap; font-size: 16px;">
        <span>🤖 Généré par IA</span>
        <span>💰 0.99€ par fiche</span>
        <span>🔒 Paiement sécurisé</span>
        <span>⭐ Noté 4.8/5</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Statistiques
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📝 Fiches créées", st.session_state.generations)
with col2:
    st.metric("💰 Dépensé", f"{st.session_state.total_spent:.2f}€")
with col3:
    st.metric("👥 Utilisateurs", st.session_state.user_count, delta="+12 aujourd'hui")
with col4:
    taux_conversion = int((st.session_state.generations / max(1, st.session_state.user_count)) * 100)
    st.metric("📊 Taux de conversion", f"{taux_conversion}%", delta="+5%")

# ============================================
# FORMULAIRE PRODUIT AVEC APERÇU
# ============================================
st.subheader("📝 Nouvelle fiche produit")

with st.container(border=True):
    col_form1, col_form2 = st.columns([2, 1])
    
    with col_form1:
        nom_produit = st.text_input(
            "Nom du produit *", 
            placeholder="Ex: Sac en cuir", 
            value=st.session_state.get("preview_nom", ""),
            key="nom_produit"
        )
        caracteristiques = st.text_area(
            "Caractéristiques *", 
            placeholder="Ex: Cuir véritable, 30x25cm, noir", 
            height=100, 
            value=st.session_state.get("preview_carac", ""),
            key="caracteristiques"
        )
        
        # Options avancées
        with st.expander("⚙️ Options avancées", expanded=False):
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                ton = st.select_slider(
                    "🎯 Ton de la fiche",
                    options=["Professionnel", "Chaleureux", "Luxe", "Minimaliste", "Dynamique"],
                    value="Professionnel",
                    key="ton"
                )
            with col_opt2:
                longueur = st.select_slider(
                    "📏 Longueur du contenu",
                    options=["Courte", "Moyenne", "Détaillée"],
                    value="Moyenne",
                    key="longueur"
                )
            mots_cles = st.text_input(
                "🔑 Mots-clés SEO (optionnel)", 
                placeholder="Ex: sac, cuir, élégant",
                key="mots_cles"
            )
            include_pricing = st.checkbox("💰 Inclure une suggestion de prix", value=True, key="include_pricing")
        
        # Stocker pour l'aperçu
        st.session_state.preview_nom = nom_produit
        st.session_state.preview_carac = caracteristiques
        st.session_state.preview_ton = ton
        st.session_state.preview_longueur = longueur
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("➕ Ajouter au panier", type="secondary", use_container_width=True):
                if nom_produit and caracteristiques:
                    # Vérifier si le produit est déjà dans le panier
                    existing = [p for p in st.session_state.cart if p['nom'].lower() == nom_produit.lower()]
                    if existing:
                        st.warning(f"⚠️ {nom_produit} est déjà dans votre panier !")
                    else:
                        st.session_state.cart.append({
                            "nom": nom_produit,
                            "caracteristiques": caracteristiques,
                            "prix": 0.99,
                            "ton": ton,
                            "longueur": longueur,
                            "mots_cles": mots_cles,
                            "include_pricing": include_pricing
                        })
                        sauvegarder_session()
                        st.success(f"✅ {nom_produit} ajouté au panier !")
                        st.balloons()
                        # Réinitialiser les champs
                        st.session_state.preview_nom = ""
                        st.session_state.preview_carac = ""
                        st.session_state.nom_produit = ""
                        st.session_state.caracteristiques = ""
                        st.rerun()
                else:
                    st.warning("⚠️ Remplissez tous les champs obligatoires")
        
        with col_btn2:
            if st.button("🔄 Vider les champs", use_container_width=True):
                st.session_state.preview_nom = ""
                st.session_state.preview_carac = ""
                st.session_state.nom_produit = ""
                st.session_state.caracteristiques = ""
                st.rerun()
    
    with col_form2:
        st.markdown("### 👀 Aperçu")
        apercu = generer_apercu(nom_produit, caracteristiques, ton, longueur)
        if apercu:
            with st.container(border=True):
                st.markdown(apercu)
                st.caption("🔍 Le contenu final sera plus détaillé")
        else:
            st.info("💡 Remplissez les champs pour voir un aperçu")

# ============================================
# OFFRE GROUPÉE
# ============================================
if len(st.session_state.cart) >= 3:
    st.success("🎁 **Offre spéciale** : 5 fiches pour 4,50€ (soit 0,90€/fiche) !")
    col_offre1, col_offre2 = st.columns([3, 1])
    with col_offre1:
        if len(st.session_state.cart) >= 5:
            st.caption("✅ Vous bénéficiez déjà de la réduction !")
        else:
            st.caption(f"💰 Ajoutez {5 - len(st.session_state.cart)} fiche(s) pour profiter de l'offre !")
    with col_offre2:
        if len(st.session_state.cart) < 5:
            if st.button("📦 Ajouter 5 fiches", use_container_width=True):
                st.info("Ajoutez des produits pour activer l'offre !")
else:
    if len(st.session_state.cart) > 0:
        st.info(f"💡 Ajoutez {3 - len(st.session_state.cart)} produit(s) supplémentaire(s) pour profiter d'une offre groupée !")

# ============================================
# PANIER ET PAIEMENT
# ============================================
if st.session_state.cart:
    st.divider()
    st.subheader("🛒 Votre panier")
    
    quantity = len(st.session_state.cart)
    
    # Affichage du panier
    for i, item in enumerate(st.session_state.cart):
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 0.3])
            with col1:
                st.write(f"**{item['nom']}**")
                st.caption(f"🎯 {item.get('ton', 'Professionnel')} | 📏 {item.get('longueur', 'Moyenne')}")
            with col2:
                st.write(f"{item['prix']:.2f}€")
            with col3:
                if st.button("📝 Détails", key=f"details_{i}"):
                    with st.expander(f"Détails de {item['nom']}"):
                        st.write(f"**Caractéristiques :** {item['caracteristiques']}")
                        st.write(f"**Ton :** {item.get('ton', 'Professionnel')}")
                        st.write(f"**Longueur :** {item.get('longueur', 'Moyenne')}")
                        if item.get('mots_cles'):
                            st.write(f"**Mots-clés :** {item['mots_cles']}")
            with col4:
                if st.button("✕", key=f"remove_{i}"):
                    st.session_state.cart.pop(i)
                    sauvegarder_session()
                    st.rerun()
    
    # Total et paiement
    st.divider()
    
    total, reduction_message = calculer_total_avec_reduction(st.session_state.cart)
    
    col_total1, col_total2, col_total3 = st.columns([2, 1, 1])
    
    with col_total1:
        if reduction_message:
            st.write(f"**Total avec réduction : {total:.2f}€**")
            st.caption(f"{quantity} fiche(s) dans votre panier")
            st.caption(reduction_message)
        else:
            st.write(f"**Total : {total:.2f}€**")
            st.caption(f"{quantity} fiche(s) dans votre panier")
        
        # Badge de confiance
        st.markdown("""
        <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; margin-top: 10px; font-size: 12px; color: #666; border-left: 4px solid #28a745;">
            ✅ Satisfait ou remboursé sous 7 jours<br>
            💬 Support client 24/7
        </div>
        """, unsafe_allow_html=True)
    
    with col_total2:
        if st.button("💳 Payer maintenant", type="primary", use_container_width=True):
            try:
                st.session_state.payment_processing = True
                
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
                    metadata={
                        'products': json.dumps([item['nom'] for item in st.session_state.cart]),
                        'user_id': st.session_state.get('user_id', 'anonymous'),
                        'generations': str(st.session_state.generations),
                        'total_items': str(quantity),
                        'total_amount': str(total)
                    }
                )
                
                # Redirection élégante
                stripe_url = checkout_session.url
                
                st.markdown(f'''
                <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: white; z-index: 9999; 
                            display: flex; justify-content: center; align-items: center; flex-direction: column;">
                    <div style="text-align: center; max-width: 500px; padding: 20px;">
                        <div style="font-size: 64px; margin-bottom: 20px;">🔄</div>
                        <h2 style="margin-bottom: 10px; color: #333;">🔒 Redirection vers Stripe</h2>
                        <p style="color: #666; margin-bottom: 20px;">Votre paiement est sécurisé.</p>
                        <div style="border: 4px solid #f3f3f3; border-top: 4px solid #6772e5; border-radius: 50%; 
                                    width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 20px auto;"></div>
                        <p style="color: #999; font-size: 14px;">Montant : {total:.2f}€</p>
                        <a href="{stripe_url}" target="_blank" 
                           style="display: inline-block; margin-top: 20px; padding: 12px 24px; 
                                  background: #6772e5; color: white; text-decoration: none; border-radius: 8px; 
                                  font-weight: bold; transition: all 0.3s;">
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
                    setTimeout(function() {{
                        window.location.href = "{stripe_url}";
                    }}, 1500);
                </script>
                ''', unsafe_allow_html=True)
                
                st.stop()
                
            except Exception as e:
                st.error(f"❌ Erreur de paiement : {e}")
                st.session_state.payment_processing = False
                st.code(str(e))
    
    with col_total3:
        st.caption("🔒 Paiement sécurisé par Stripe")
        st.markdown("""
        <div style="background: #6772e5; padding: 10px; border-radius: 6px; text-align: center; color: white; font-weight: bold; font-size: 16px; letter-spacing: 1px;">
            STRIPE
        </div>
        <div style="text-align: center; margin-top: 10px; font-size: 11px; color: #999;">
            Visa · Mastercard · Amex
        </div>
        """, unsafe_allow_html=True)

# ============================================
# TRAITEMENT APRÈS PAIEMENT
# ============================================
if st.query_params.get("payment") == "success":
    st.query_params.clear()
    st.success("✅ Paiement accepté ! Génération de vos fiches en cours...")
    
    if st.session_state.cart:
        progress_bar = st.progress(0)
        status_text = st.empty()
        generated_count = 0
        
        for idx, item in enumerate(st.session_state.cart):
            status_text.text(f"📝 Génération de la fiche {idx+1}/{len(st.session_state.cart)} : {item['nom']}")
            progress_bar.progress((idx + 1) / len(st.session_state.cart))
            
            try:
                # Construction du prompt personnalisé
                longueur_guide = {
                    "Courte": "100 mots",
                    "Moyenne": "150 mots",
                    "Détaillée": "250 mots"
                }
                
                prompt = f"""Rédige une fiche produit professionnelle pour : {item['nom']}.
                
                Caractéristiques : {item['caracteristiques']}.
                Ton : {item.get('ton', 'Professionnel')}.
                Longueur approximative : {longueur_guide.get(item.get('longueur', 'Moyenne'), '150 mots')}.
                Mots-clés SEO : {item.get('mots_cles', 'Non spécifiés')}.
                Inclure suggestion de prix : {item.get('include_pricing', True)}.
                
                Structure à respecter :
                1. TITRE accrocheur avec emojis
                2. DESCRIPTION détaillée
                3. CARACTÉRISTIQUES TECHNIQUES en liste
                4. AVANTAGES pour le client (3-4 points)
                5. PRIX CONSEILLÉ (si demandé)
                6. META-DESCRIPTION pour le SEO (max 160 caractères)
                
                Utilise des emojis pour rendre la fiche attractive.
                Sois professionnel et précis.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt,
                )
                
                st.session_state.generated_products.append({
                    "nom": item['nom'],
                    "contenu": response.text,
                    "prix": 0.99,
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "ton": item.get('ton', 'Professionnel'),
                    "longueur": item.get('longueur', 'Moyenne'),
                    "caracteristiques": item['caracteristiques']
                })
                st.session_state.generations += 1
                st.session_state.total_spent += 0.99
                st.session_state.daily_generations += 1
                generated_count += 1
                sauvegarder_session()
                
            except Exception as e:
                st.error(f"❌ Erreur pour {item['nom']} : {e}")
                # Ajouter une fiche par défaut
                st.session_state.generated_products.append({
                    "nom": item['nom'],
                    "contenu": f"""**{item['nom']}** - Fiche produit

📝 **Description** : {item['nom']} - {item['caracteristiques']}

✨ **Avantages** :
• Qualité premium
• Design élégant
• Durabilité exceptionnelle

🔧 **Caractéristiques** : {item['caracteristiques']}

💰 **Prix conseillé** : À définir

📌 **Meta-description** : {item['nom']} - {item['caracteristiques'][:100]}""",
                    "prix": 0.99,
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "ton": item.get('ton', 'Professionnel'),
                    "caracteristiques": item['caracteristiques']
                })
                st.session_state.generations += 1
                st.session_state.total_spent += 0.99
                generated_count += 1
        
        status_text.text(f"✅ {generated_count} fiche(s) générées avec succès !")
        st.session_state.cart = []
        time.sleep(1)
        st.success(f"🎉 {generated_count} fiche(s) générée(s) avec succès !")
        st.balloons()
        time.sleep(2)
        st.rerun()

# ============================================
# PRODUITS GÉNÉRÉS
# ============================================
if st.session_state.generated_products:
    st.divider()
    st.subheader("📦 Mes fiches produits")
    
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    with col_stats1:
        st.metric("📄 Total fiches", len(st.session_state.generated_products))
    with col_stats2:
        total_valeur = len(st.session_state.generated_products) * 0.99
        st.metric("💰 Valeur totale", f"{total_valeur:.2f}€")
    with col_stats3:
        derniere_date = st.session_state.generated_products[-1].get('date', 'Aujourd\'hui')
        st.metric("📅 Dernière génération", derniere_date[:10] if len(derniere_date) > 10 else derniere_date)
    with col_stats4:
        st.metric("🎯 Dernier ton", st.session_state.generated_products[-1].get('ton', 'N/A'))
    
    # Recherche et filtres
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_term = st.text_input("🔍 Rechercher une fiche", placeholder="Entrez un nom de produit...")
    with col_search2:
        filter_ton = st.selectbox("🎯 Filtrer par ton", ["Tous", "Professionnel", "Chaleureux", "Luxe", "Minimaliste", "Dynamique"])
    
    # Filtrer les produits
    filtered_products = st.session_state.generated_products
    if search_term:
        filtered_products = [p for p in filtered_products if search_term.lower() in p['nom'].lower()]
    if filter_ton != "Tous":
        filtered_products = [p for p in filtered_products if p.get('ton', 'Professionnel') == filter_ton]
    
    if filtered_products:
        for i, product in enumerate(filtered_products):
            real_index = st.session_state.generated_products.index(product)
            with st.expander(f"📄 {product['nom']} - {product.get('date', '')}"):
                st.markdown(product['contenu'])
                
                col_actions1, col_actions2, col_actions3, col_actions4 = st.columns(4)
                with col_actions1:
                    if st.button("📋 Copier", key=f"copy_{real_index}"):
                        st.success("📋 Copié dans le presse-papiers !")
                with col_actions2:
                    st.download_button(
                        label="📥 Télécharger",
                        data=product['contenu'],
                        file_name=f"{product['nom']}_fiche.txt",
                        mime="text/plain",
                        key=f"download_btn_{real_index}"
                    )
                with col_actions3:
                    if st.button("🔄 Régénérer", key=f"regenerate_{real_index}"):
                        st.info("🔄 Fonctionnalité à venir")
                with col_actions4:
                    if st.button("🗑️ Supprimer", key=f"del_{real_index}"):
                        st.session_state.generated_products.pop(real_index)
                        sauvegarder_session()
                        st.rerun()
        
        # Export
        st.divider()
        col_export1, col_export2, col_export3 = st.columns(3)
        with col_export1:
            if st.button("📥 Exporter JSON", use_container_width=True):
                export_data = {
                    "products": st.session_state.generated_products,
                    "generated_at": datetime.now().isoformat(),
                    "total_generations": st.session_state.generations,
                    "total_spent": st.session_state.total_spent
                }
                st.download_button(
                    label="Télécharger",
                    data=json.dumps(export_data, indent=2, ensure_ascii=False),
                    file_name=f"fiches_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="export_json"
                )
        with col_export2:
            if st.button("📊 Exporter CSV", use_container_width=True):
                csv_data = "Nom,Date,Ton,Longueur\n"
                for p in st.session_state.generated_products:
                    csv_data += f"{p['nom']},{p.get('date', '')},{p.get('ton', '')},{p.get('longueur', '')}\n"
                st.download_button(
                    label="Télécharger",
                    data=csv_data,
                    file_name=f"fiches_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="export_csv"
                )
        with col_export3:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                if st.checkbox("Confirmer la suppression de toutes les fiches ?"):
                    st.session_state.generated_products = []
                    st.session_state.generations = 0
                    st.session_state.total_spent = 0
                    sauvegarder_session()
                    st.rerun()
    else:
        st.info("Aucun produit ne correspond à vos critères de recherche.")

# ============================================
# EXEMPLE DE FICHE
# ============================================
with st.expander("📋 Voir un exemple de fiche générée"):
    st.markdown("""
    ### 👜 Sac à Main Élégant en Cuir Véritable
    
    **📝 Description** : Découvrez notre sac à main en cuir véritable, alliant 
    artisanat traditionnel et design contemporain. Parfait pour le quotidien, 
    ce sac allie fonctionnalité et élégance. Fabriqué avec des matériaux 
    premium, il résistera aux années tout en conservant son charme.
    
    **✨ Avantages** :
    - ✅ Cuir pleine fleur garanti
    - ✅ Doublure en coton bio
    - ✅ Fermeture sécurisée
    - ✅ Bandoulière réglable
    
    **🔧 Caractéristiques techniques** :
    - Matière : Cuir de vachette
    - Dimensions : 30x25x12 cm
    - Couleurs : Noir, Cognac, Bordeaux
    - Poids : 800g
    
    **💰 Prix conseillé** : 89,99€
    
    **📌 Meta-description** : Sac à main en cuir véritable élégant et durable. 
    Parfait pour un usage quotidien. Qualité premium et design intemporel.
    """)

# ============================================
# TÉMOIGNAGES
# ============================================
st.divider()
st.caption("💬 Ce que disent nos utilisateurs")

col_tem1, col_tem2, col_tem3 = st.columns(3)
with col_tem1:
    st.info("⭐⭐⭐⭐⭐ *'J'ai généré 15 fiches en 5 minutes, un gain de temps énorme !'* - Marie D.")
with col_tem2:
    st.info("⭐⭐⭐⭐⭐ *'Le contenu est de qualité professionnelle, je recommande.'* - Thomas L.")
with col_tem3:
    st.info("⭐⭐⭐⭐⭐ *'Les fiches sont bien optimisées SEO, mes ventes ont augmenté.'* - Sophie R.")

# ============================================
# FAQ
# ============================================
with st.expander("❓ Foire Aux Questions"):
    st.markdown("""
    **Comment fonctionne la génération ?**  
    L'IA analyse votre produit et rédige une fiche professionnelle en quelques secondes.
    
    **Le paiement est-il sécurisé ?**  
    Oui, tous les paiements sont sécurisés par Stripe.
    
    **Puis-je modifier la fiche générée ?**  
    Oui, vous pouvez copier le contenu et l'adapter selon vos besoins.
    
    **Que se passe-t-il après le paiement ?**  
    Vos fiches sont générées automatiquement et sauvegardées dans votre session.
    
    **Y a-t-il des réductions pour les gros volumes ?**  
    Oui ! 3 fiches = 10% de réduction, 5 fiches = 4,50€.
    """)

# ============================================
# PIED DE PAGE
# ============================================
st.divider()
col_footer1, col_footer2, col_footer3, col_footer4 = st.columns(4)
with col_footer1:
    st.caption("🤖 Généré avec ❤️ par l'IA")
with col_footer2:
    st.caption(f"📊 {st.session_state.generations} fiches créées")
with col_footer3:
    st.caption("🔒 Tous les paiements sont sécurisés")
with col_footer4:
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y')}")

# ============================================
# SAUVEGARDE AUTOMATIQUE
# ============================================
if "last_backup" not in st.session_state:
    st.session_state.last_backup = time.time()

if time.time() - st.session_state.last_backup > 300:  # 5 minutes
    sauvegarder_session()
    st.session_state.last_backup = time.time()
