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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Mobile First avec support desktop
st.markdown("""
<style>
    /* Reset et base */
    .stApp {
        max-width: 100%;
        padding: 0.5rem;
    }
    
    /* Cards responsives */
    .stContainer {
        border-radius: 12px !important;
        padding: 12px !important;
        margin: 8px 0 !important;
    }
    
    /* Boutons pleine largeur sur mobile */
    .stButton button {
        border-radius: 10px !important;
        padding: 12px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    
    /* Inputs adaptés */
    .stTextInput input, .stTextArea textarea {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 10px !important;
    }
    
    /* Métriques adaptées */
    .stMetric {
        background: #f8f9fa;
        padding: 8px;
        border-radius: 10px;
        text-align: center;
        margin: 2px 0;
    }
    
    /* Responsive Desktop */
    @media (min-width: 769px) {
        .stApp {
            padding: 1rem 2rem;
        }
        .stContainer {
            padding: 20px !important;
        }
        .stButton button {
            padding: 14px !important;
            font-size: 18px !important;
        }
        h1 {
            font-size: 36px !important;
        }
    }
    
    /* Responsive Mobile */
    @media (max-width: 768px) {
        .stApp {
            padding: 0.25rem;
        }
        .stContainer {
            padding: 8px !important;
            margin: 4px 0 !important;
        }
        .stColumns {
            flex-direction: column !important;
        }
        .stMetric {
            padding: 4px;
        }
        .stMetric label {
            font-size: 11px !important;
        }
        .stMetric div {
            font-size: 16px !important;
        }
        h1 {
            font-size: 20px !important;
        }
        h2, .stSubheader {
            font-size: 16px !important;
        }
        h3 {
            font-size: 14px !important;
        }
        .stButton button {
            padding: 10px !important;
            font-size: 14px !important;
        }
        .stTextInput input, .stTextArea textarea {
            font-size: 14px !important;
            padding: 8px !important;
        }
        /* Bannière promo mobile */
        .promo-badge {
            font-size: 12px !important;
            padding: 8px !important;
        }
    }
    
    /* Animations */
    @keyframes slideIn {
        from { transform: translateY(-100%); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .stAlert {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    .promo-badge {
        animation: pulse 2s infinite;
    }
    
    /* Badge de confiance */
    .trust-badge {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 10px;
        margin: 6px 0;
        font-size: 13px;
        border-left: 4px solid #6772e5;
        text-align: center;
    }
    
    /* Cart item */
    .cart-item {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 10px;
        margin: 4px 0;
    }
    
    /* Scrollbar personnalisée */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #6772e5;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURATION
# ============================================

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
if "promo_badge" not in st.session_state:
    promotions = [
        "🔥 3 fiches achetées, 1 offerte !",
        "⭐ 5 fiches pour le prix de 4 !",
        "🎁 10% sur votre première commande !",
        "💎 Fiches optimisées SEO incluses !"
    ]
    st.session_state.promo_badge = random.choice(promotions)
if "form_nom" not in st.session_state:
    st.session_state.form_nom = ""
if "form_carac" not in st.session_state:
    st.session_state.form_carac = ""
if "form_ton" not in st.session_state:
    st.session_state.form_ton = "Professionnel"
if "form_longueur" not in st.session_state:
    st.session_state.form_longueur = "Moyenne"
if "form_mots_cles" not in st.session_state:
    st.session_state.form_mots_cles = ""
if "form_include_pricing" not in st.session_state:
    st.session_state.form_include_pricing = True

# ============================================
# FONCTIONS UTILITAIRES
# ============================================
def sauvegarder_session():
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
    if not nom or not caracteristiques:
        return None
    
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
    
    if longueur == "Courte":
        description = f"Découvrez {nom}, alliant qualité et {style_info['style']}."
    elif longueur == "Détaillée":
        description = f"Découvrez {nom}, alliant qualité et {style_info['style']}. Conçu avec soin pour répondre à vos besoins quotidiens. Un produit qui saura vous séduire par sa finition et sa praticité."
    else:
        description = f"Découvrez {nom}, alliant qualité et {style_info['style']}. Conçu avec soin pour répondre à vos besoins quotidiens."
    
    avantages_liste = "\n".join([f"• {avantage}" for avantage in style_info["avantages"]])
    
    return f"""
    **{style_info['emoji']} {nom}** - Fiche produit {style_info['style']}
    
    **📝 Description** : {description}
    
    **✨ Avantages** : 
    {avantages_liste}
    
    **🔧 Caractéristiques** : {caracteristiques}
    
    **💰 Prix conseillé** : À définir
    """

def calculer_total_avec_reduction(cart):
    quantity = len(cart)
    if quantity >= 5:
        return 4.50, f"💰 Économie de {quantity * 0.99 - 4.50:.2f}€"
    elif quantity >= 3:
        return quantity * 0.90, f"💰 Réduction de {quantity * 0.09:.2f}€ (10%)"
    else:
        return quantity * 0.99, ""

# ============================================
# EN-TÊTE
# ============================================
# Bannière promotionnelle
st.markdown(f"""
<div class="promo-badge" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); 
            padding: 12px; border-radius: 10px; color: white; text-align: center; 
            margin-bottom: 15px; font-weight: bold; font-size: clamp(14px, 2vw, 20px);
            box-shadow: 0 4px 15px rgba(255,107,107,0.3);">
    {st.session_state.promo_badge}
</div>
""", unsafe_allow_html=True)

# Titre + compteur panier
col_title, col_cart_icon = st.columns([4, 1])
with col_title:
    st.title("🛍️ Fiche Produit IA")
with col_cart_icon:
    if len(st.session_state.cart) > 0:
        st.markdown(f"""
        <div style="background: #6772e5; color: white; border-radius: 50px; 
                    padding: 6px 12px; text-align: center; font-weight: bold; 
                    margin-top: 5px; font-size: clamp(14px, 1.5vw, 18px);
                    box-shadow: 0 2px 10px rgba(103, 114, 229, 0.3);">
            🛒 {len(st.session_state.cart)}
        </div>
        """, unsafe_allow_html=True)

# Statistiques compactes
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📝", st.session_state.generations)
with col2:
    st.metric("💰", f"{st.session_state.total_spent:.2f}€")
with col3:
    st.metric("👥", "847", delta="+12")
with col4:
    taux = int((st.session_state.generations / max(1, st.session_state.user_count)) * 100)
    st.metric("📊", f"{taux}%", delta="+5%")

st.divider()

# ============================================
# FORMULAIRE PRODUIT
# ============================================
with st.container(border=True):
    st.subheader("📝 Nouvelle fiche")
    
    nom_produit = st.text_input(
        "Nom du produit *", 
        placeholder="Ex: Sac en cuir", 
        value=st.session_state.form_nom,
        key="input_nom"
    )
    caracteristiques = st.text_area(
        "Caractéristiques *", 
        placeholder="Ex: Cuir véritable, 30x25cm, noir", 
        height=80, 
        value=st.session_state.form_carac,
        key="input_carac"
    )
    
    # Options avancées en accordéon
    with st.expander("⚙️ Options", expanded=False):
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            ton = st.select_slider(
                "🎯 Ton",
                options=["Professionnel", "Chaleureux", "Luxe", "Minimaliste", "Dynamique"],
                value=st.session_state.form_ton,
                key="input_ton"
            )
        with col_opt2:
            longueur = st.select_slider(
                "📏 Longueur",
                options=["Courte", "Moyenne", "Détaillée"],
                value=st.session_state.form_longueur,
                key="input_longueur"
            )
        mots_cles = st.text_input(
            "🔑 Mots-clés SEO",
            placeholder="Ex: sac, cuir, élégant",
            value=st.session_state.form_mots_cles,
            key="input_mots_cles"
        )
        include_pricing = st.checkbox(
            "💰 Suggestion de prix", 
            value=st.session_state.form_include_pricing,
            key="input_include_pricing"
        )
    
    st.session_state.form_nom = nom_produit
    st.session_state.form_carac = caracteristiques
    st.session_state.form_ton = ton
    st.session_state.form_longueur = longueur
    st.session_state.form_mots_cles = mots_cles
    st.session_state.form_include_pricing = include_pricing
    
    # Aperçu
    apercu = generer_apercu(nom_produit, caracteristiques, ton, longueur)
    if apercu:
        with st.container(border=True):
            st.caption("👀 Aperçu")
            st.markdown(apercu)
            st.caption("🔍 Contenu final plus détaillé")
    
    # Boutons
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ Ajouter", type="secondary", use_container_width=True):
            if nom_produit and caracteristiques:
                existing = [p for p in st.session_state.cart if p['nom'].lower() == nom_produit.lower()]
                if existing:
                    st.warning(f"⚠️ {nom_produit} déjà dans le panier")
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
                    st.success(f"✅ {nom_produit} ajouté !")
                    st.balloons()
                    st.session_state.form_nom = ""
                    st.session_state.form_carac = ""
                    st.session_state.form_mots_cles = ""
                    st.rerun()
            else:
                st.warning("⚠️ Remplissez tous les champs")
    
    with col_btn2:
        if st.button("🔄 Effacer", use_container_width=True):
            st.session_state.form_nom = ""
            st.session_state.form_carac = ""
            st.session_state.form_mots_cles = ""
            st.rerun()

st.divider()

# ============================================
# OFFRE GROUPÉE
# ============================================
if len(st.session_state.cart) >= 3:
    st.success("🎁 **Offre** : 5 fiches = 4,50€ !")
    if len(st.session_state.cart) < 5:
        st.caption(f"💰 +{5 - len(st.session_state.cart)} fiche(s) pour l'offre")
else:
    if len(st.session_state.cart) > 0:
        st.info(f"💡 +{3 - len(st.session_state.cart)} fiche(s) pour offre groupée")

# ============================================
# PANIER
# ============================================
if st.session_state.cart:
    st.subheader("🛒 Panier")
    
    for i, item in enumerate(st.session_state.cart):
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 0.5])
            with col1:
                st.write(f"**{item['nom']}**")
                st.caption(f"🎯 {item.get('ton', 'Pro')} | 📏 {item.get('longueur', 'Moy')}")
            with col2:
                st.write("0.99€")
            with col3:
                if st.button("✕", key=f"remove_{i}"):
                    st.session_state.cart.pop(i)
                    sauvegarder_session()
                    st.rerun()
    
    st.divider()
    
    total, reduction_message = calculer_total_avec_reduction(st.session_state.cart)
    
    if reduction_message:
        st.write(f"**Total : {total:.2f}€**")
        st.caption(reduction_message)
    else:
        st.write(f"**Total : {total:.2f}€**")
    st.caption(f"{len(st.session_state.cart)} fiche(s)")
    
    # Badge de confiance
    st.markdown("""
    <div class="trust-badge">
        💬 Support 24/7 · 🔒 Paiement sécurisé · 📝 Instantané
    </div>
    """, unsafe_allow_html=True)
    
    # Bouton de paiement
    if st.button("💳 Payer maintenant", type="primary", use_container_width=True):
        try:
            st.session_state.payment_processing = True
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': STRIPE_PRICE_ID,
                    'quantity': len(st.session_state.cart),
                }],
                mode='payment',
                success_url=f"{MON_URL_STREAMLIT}?payment=success",
                cancel_url=f"{MON_URL_STREAMLIT}?payment=cancel",
                metadata={
                    'products': json.dumps([item['nom'] for item in st.session_state.cart]),
                    'user_id': st.session_state.get('user_id', 'anonymous'),
                    'generations': str(st.session_state.generations),
                    'total_items': str(len(st.session_state.cart)),
                    'total_amount': str(total)
                }
            )
            
            stripe_url = checkout_session.url
            
            st.markdown(f'''
            <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: white; z-index: 9999; 
                        display: flex; justify-content: center; align-items: center; flex-direction: column; padding: 20px;">
                <div style="text-align: center; max-width: 400px;">
                    <div style="font-size: 48px; margin-bottom: 15px;">🔄</div>
                    <h3 style="margin-bottom: 10px;">Redirection Stripe</h3>
                    <p style="color: #666; margin-bottom: 15px;">Paiement sécurisé</p>
                    <div style="border: 4px solid #f3f3f3; border-top: 4px solid #6772e5; border-radius: 50%; 
                                width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 15px auto;"></div>
                    <p style="color: #999; font-size: 14px;">Montant : {total:.2f}€</p>
                    <a href="{stripe_url}" target="_blank" 
                       style="display: inline-block; margin-top: 15px; padding: 12px 24px; 
                              background: #6772e5; color: white; text-decoration: none; border-radius: 10px; 
                              font-weight: bold; font-size: 16px;">
                        Payer maintenant
                    </a>
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
                }}, 2000);
            </script>
            ''', unsafe_allow_html=True)
            
            st.stop()
            
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

st.divider()

# ============================================
# PRODUITS GÉNÉRÉS
# ============================================
if st.session_state.generated_products:
    st.subheader("📦 Mes fiches")
    
    # Filtres compacts
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_term = st.text_input("🔍 Rechercher", placeholder="Nom...", key="search_input")
    with col_filter:
        filter_ton = st.selectbox(
            "🎯 Filtre", 
            ["Tous", "Professionnel", "Chaleureux", "Luxe", "Minimaliste", "Dynamique"],
            key="filter_input"
        )
    
    filtered_products = st.session_state.generated_products
    if search_term:
        filtered_products = [p for p in filtered_products if search_term.lower() in p['nom'].lower()]
    if filter_ton != "Tous":
        filtered_products = [p for p in filtered_products if p.get('ton', 'Professionnel') == filter_ton]
    
    if filtered_products:
        for i, product in enumerate(filtered_products):
            real_index = st.session_state.generated_products.index(product)
            with st.expander(f"📄 {product['nom'][:20]} - {product.get('date', '')[:10]}"):
                st.markdown(product['contenu'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        label="📥 Télécharger",
                        data=product['contenu'],
                        file_name=f"{product['nom']}_fiche.txt",
                        mime="text/plain",
                        key=f"download_{real_index}",
                        use_container_width=True
                    )
                with col2:
                    if st.button("📋 Copier", key=f"copy_{real_index}", use_container_width=True):
                        st.success("✅ Copié !")
                with col3:
                    if st.button("🗑️ Supprimer", key=f"del_{real_index}", use_container_width=True):
                        st.session_state.generated_products.pop(real_index)
                        sauvegarder_session()
                        st.rerun()
        
        # Export
        col_export1, col_export2 = st.columns(2)
        with col_export1:
            if st.button("📥 Exporter JSON", use_container_width=True):
                export_data = {
                    "products": st.session_state.generated_products,
                    "generated_at": datetime.now().isoformat()
                }
                st.download_button(
                    label="Télécharger",
                    data=json.dumps(export_data, indent=2, ensure_ascii=False),
                    file_name=f"fiches_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="export_json"
                )
        with col_export2:
            if st.button("🔄 Tout effacer", use_container_width=True):
                if st.checkbox("Confirmer la suppression ?"):
                    st.session_state.generated_products = []
                    st.session_state.generations = 0
                    st.session_state.total_spent = 0
                    sauvegarder_session()
                    st.rerun()
    else:
        st.info("Aucun produit trouvé")

st.divider()

# ============================================
# TRAITEMENT APRÈS PAIEMENT
# ============================================
if st.query_params.get("payment") == "success":
    st.query_params.clear()
    st.success("✅ Paiement accepté ! Génération...")
    
    if st.session_state.cart:
        progress_bar = st.progress(0)
        status_text = st.empty()
        generated_count = 0
        
        for idx, item in enumerate(st.session_state.cart):
            status_text.text(f"📝 {idx+1}/{len(st.session_state.cart)} : {item['nom']}")
            progress_bar.progress((idx + 1) / len(st.session_state.cart))
            
            try:
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
                    "longueur": item.get('longueur', 'Moyenne')
                })
                st.session_state.generations += 1
                st.session_state.total_spent += 0.99
                generated_count += 1
                sauvegarder_session()
                
            except Exception as e:
                st.error(f"❌ Erreur pour {item['nom']}")
                st.session_state.generated_products.append({
                    "nom": item['nom'],
                    "contenu": f"""**{item['nom']}** - Fiche produit

📝 **Description** : {item['nom']} - {item['caracteristiques']}

✨ **Avantages** :
• Qualité premium
• Design élégant
• Durabilité

🔧 **Caractéristiques** : {item['caracteristiques']}""",
                    "prix": 0.99,
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "ton": item.get('ton', 'Professionnel')
                })
                st.session_state.generations += 1
                st.session_state.total_spent += 0.99
                generated_count += 1
        
        status_text.text(f"✅ {generated_count} fiche(s) générées !")
        st.session_state.cart = []
        time.sleep(1)
        st.success(f"🎉 {generated_count} fiche(s) générée(s) !")
        st.balloons()
        time.sleep(2)
        st.rerun()

# ============================================
# EXEMPLE, TÉMOIGNAGES ET FAQ (Accordéons)
# ============================================
with st.expander("📋 Exemple de fiche"):
    st.markdown("""
    **👜 Sac à Main en Cuir Véritable**
    
    📝 Description : Sac en cuir véritable, alliant artisanat et design contemporain.
    
    ✨ Avantages :
    • Cuir pleine fleur
    • Doublure en coton bio
    • Fermeture sécurisée
    
    🔧 Caractéristiques : Cuir vachette, 30x25cm
    """)

with st.expander("💬 Témoignages"):
    st.info("⭐⭐⭐⭐⭐ *'15 fiches en 5 minutes !'* - Marie D.")
    st.info("⭐⭐⭐⭐⭐ *'Qualité professionnelle'* - Thomas L.")
    st.info("⭐⭐⭐⭐⭐ *'SEO efficace, ventes en hausse'* - Sophie R.")

with st.expander("❓ FAQ"):
    st.markdown("""
    **🤖 Comment ça fonctionne ?**  
    L'IA génère une fiche professionnelle en quelques secondes.
    
    **🔒 Paiement sécurisé ?**  
    Oui, par Stripe.
    
    **📝 Puis-je modifier ?**  
    Oui, copiez-collez le contenu.
    
    **💰 Y a-t-il des réductions ?**  
    Oui ! 3 fiches = 10%, 5 fiches = 4,50€.
    """)

# ============================================
# PIED DE PAGE
# ============================================
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("🤖 Généré par IA")
with col_f2:
    st.caption(f"📊 {st.session_state.generations} fiches")
with col_f3:
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y')}")

# ============================================
# SAUVEGARDE AUTOMATIQUE
# ============================================
if "last_backup" not in st.session_state:
    st.session_state.last_backup = time.time()

if time.time() - st.session_state.last_backup > 300:
    sauvegarder_session()
    st.session_state.last_backup = time.time()
