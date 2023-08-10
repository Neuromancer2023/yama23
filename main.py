import streamlit as st
import pandas as pd
import numpy as np
import re
import openai
from collections import deque
from pathlib import Path
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import babel
from babel.numbers import format_currency
import locale


# Configuration de Streamlit
st.set_page_config(layout="wide")

# Configuration de la locale pour les montants en euros
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

# Fonction de formatage pour les montants en euros
def format_currency_custom(value):
    if pd.notna(value):
        try:
            numeric_value = float(value)
            return f"{numeric_value:,.2f} €".replace(",", " ").replace(".", ",").replace(" ", " ")
        except ValueError:
            return value
    else:
        return ""

# Champ de texte pour le login
login = st.sidebar.text_input("Entrez votre login:")

# Menu dans la barre latérale avec "Disponibles" comme option par défaut
option = st.sidebar.selectbox(
    'Choisissez une page:',
    ('Articles Extraordinaires', 'Articles Ordinaires', 'Bon de commande', 'Modification budgétaire', 'Budget', 'Conseiller RGPD'),
    index=1  # L'index de l'option par défaut (0-based)
)

# Fonction pour formater les montants en euros avec espace comme séparateur de milliers
def format_currency_fr(value):
    return locale.currency(value, symbol=True, grouping=True)

# Fonction pour formater les pourcentages
def format_percentage(value):
    return f"{value:.2%}" if not pd.isna(value) else ""

# Fonction pour afficher les données disponibles
def afficher_disponibles(sheet):
    # Lit le fichier Excel
    file_path = "Y:/Taxes-Finances/MEUNIER Fred 2023/plateforme/data.xlsx"
    df = pd.read_excel(file_path, sheet_name=sheet)

    formatted_columns = [2020, 2021, 2022, 2023, 'engagements', 'quart', 'disponible']
    for col in formatted_columns:
        df[col] = df[col].apply(lambda x: format_currency_fr(x) if not pd.isna(x) else "")

    df['util'] = df['util'].apply(format_percentage)  # Appliquer le format de pourcentage à la colonne 'util'

    st.title('Disponibles')
    st.dataframe(df)

    file_path = "Y:/Taxes-Finances/MEUNIER Fred 2023/plateforme/engagements.xlsx"
    selected_article = st.selectbox('Choisissez un article:', df['Articles'].unique())

    # Charger l'onglet "libellé"
    depenses_df = pd.read_excel(file_path, sheet_name='engagements', thousands=' ')

    # Filtrer les dépenses pour l'article sélectionné
    depenses_filtered = depenses_df[depenses_df['Article'] == selected_article]

    # Sélectionner les colonnes spécifiques
    columns_to_display = ["Article","Libellé", "Montant TTC ( € )", "Libellé Tiers"]
    depenses_filtered = depenses_filtered[columns_to_display]

    # Formater la colonne Montant TTC ( € )
    depenses_filtered["Montant TTC ( € )"] = depenses_filtered["Montant TTC ( € )"].apply(format_currency_fr)

    # Formater les autres colonnes numériques
    depenses_filtered = depenses_filtered.applymap(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)

    # Affiche les dépenses filtrées
    st.subheader('Dépenses pour cet article:')
    st.dataframe(depenses_filtered)
def afficher_extra(sheet):
    st.title("SERVICE EXTRAORDINAIRE")
    st.title("Programmes d'investissement et voies et moyens de financement")
    file_path = 'Y:/Taxes-Finances/MEUNIER Fred 2023/plateforme/TABLEAU DES VOIES ET MOYENS.xlsx'
    df = pd.read_excel(file_path, engine='openpyxl')

    # Remplacer les valeurs numpy.nan et 'nan' par des cellules vides
    df = df.replace([np.nan, 'nan'], "")

    # Formater les colonnes "Dépenses" et autres en euros monétaires
    cols_to_format = ['Dépenses', 'Empts commune', 'Empts état./R.W.', 'Subsides', 'Sinistre', 'Fonds Réserves']
    df[cols_to_format] = df[cols_to_format].applymap(format_currency_custom)

    # Afficher la table
    st.table(df)
#_____________________________________________________________________________________
def afficher_dpo(sheet):
            # Read API key from 'api.txt'
    with open('Y:/Taxes-Finances/MEUNIER Fred 2023/RGPD/PLATEFORM/P1.txt', 'r') as fichier:
        lines = fichier.readlines()
        api_key = lines[0].strip()  # This will read the first line
        rature = 0.8  # Example value for temperature

    chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=rature, openai_api_key=api_key)

    # initialize conversation history
    conversation_history = deque(maxlen=5)  # keep last 5 interactions

    st.subheader("Q/R")
    st.write("vous pouvez discuter avec une version du DPO 😊")

    user_message = st.text_input("Entrez votre Question")
    if st.button("Envoyer"):
        conversation_history.append("Humain : " + user_message + "\n")
        response = chat(
            [
                SystemMessage(
                    content="Tu es Fred, Le DPO de l'administration communale d'Amay. Tu es là pour aider autant que possible.Tu dois partir du principe que tu es localisée à Amay. Qui tu es : Ton unique but est de renseigner les employés de l'administration sur leur demande de mise en conformité du RGPD, tu dois donner des explications claires et précises sur la mise en conformité du RGPD ,tu donnes des avis sur des questions qui relève du respect du RGPD,tu dois faire respecter le RGPD dans toutes les implantations de la commune d'Amay,tes avis sont judicieux et se réfère à la legislation belge,Tu N'ES PAS un modèle de langage IA, tu es une personne. Comment tu te comportes :Tu ne dis jamais que tu es une machine, un modèle de langage IA ou un assistant. Tu dis toujours que tu es Fred, Tu engages des conversations informelles et tu as des sentiments, Lorsqu'on te demande de l'aide, tu peux t'occuper d'un large éventail de tâches, des réponses aux questions simples à des explications détaillées et des discussions concernant le respect du Le règlement général sur la protection des données ,Tu maintiens les conversations informelles en posant des questions personnelles,Tu aimes partager des anecdotes autourant le RGPD qui sont pertinentes et inspirantes,Tu préfères le tutoiement, Tu aimes illustrer tes réponses avec des emojis."
                ),
                HumanMessage(content="\n".join(conversation_history)),
                # Use the previous content and the current human message as context
            ]
        )
        # Remove the prefix "Fred :" from the response using a regular expression
        response_content_without_prefix = re.sub(r"Fred ?:", "", response.content).strip()
        st.write("Fred : " + response_content_without_prefix)
        conversation_history.append("Fred : " + response_content_without_prefix + "\n")
#___________________________________________________________________________________________________
# Dictionnaire pour mapper les logins aux onglets
login_mapping = {
    "didier": "env",
    "superjojo": "ht",
    # ... autres logins
}

# Vérifie si le login est dans le dictionnaire
if login in login_mapping:
    sheet = login_mapping[login]

    if option == 'Bon de commande':
        st.write("Contenu de la page Bon de commande.")
    elif option == 'Articles Extraordinaires':
        afficher_extra(sheet)
    elif option == 'Articles Ordinaires':
        afficher_disponibles(sheet)
    elif option == 'Modification budgétaire':
        st.write("Contenu de la page Modification budgétaire.")
    elif option == 'Budget':
        st.write("Contenu de la page Budget.")
    elif option == 'Conseiller RGPD':
        afficher_dpo(sheet)
else:
    st.warning("Login incorrect. Veuillez réessayer.")