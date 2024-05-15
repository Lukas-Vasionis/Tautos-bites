import os
import pickle
import pandas as pd
import plotly.express as px
import streamlit as st
import polars as pl

pl.Config(fmt_str_lengths=1000)
pl.Config(tbl_width_chars=2000)

df_mp = pd.read_csv("data/metadata_mp.csv")
df_mp.loc[:, 'mp_url'] = df_mp['mp_url'].str.split('=').str[-1].astype(int)
mp_party_map = df_mp.loc[:, ['fraction', 'name']].values.tolist()
mp_party_map = {x[1]: x[0] for x in mp_party_map}

# with open("/home/vejas/PycharmProjects/parlamentinis_greitukas/process_data/objects/df_voting_data_cln.pickle",
with open("data/df_voting_data_cln.pickle",
          'rb') as p:
    df_voting = pickle.load(p)  #pd.DataFrame
    df_voting = pl.from_pandas(df_voting)

    map_mp_name_id = df_mp.loc[:, ["mp_url", "name"]].to_records(index=False)
    map_mp_name_id = dict(map_mp_name_id)
    df_voting = df_voting.with_columns(pl.col("name_url").replace(map_mp_name_id).alias("name"))

    map_vote = {0: "Už", 1: "Prieš", 2: "Susilaikė", 3: "Registravosi", 4: "Nedalyvavo"}
    df_voting = df_voting.with_columns(pl.col("vote").replace(map_vote).alias("vote"))
    df_voting = df_voting.select('name', "vote")

    df_voting_grouped = df_voting.group_by('name', "vote").len(name="count")

with open("data/count_vote_combos.pickle", 'rb') as file:
    dict_vote_combos = pickle.load(file)

st.set_page_config(layout="wide")

# Kas daugiausiai lojo kai pranešantis mp pristatė savo projektą
# Lankomūmo dažnias pagal valandas (headtmap)
# Kurie nariai ateina tik dėl vieno klausimo
# Seimo nario lankomumas
# Nutrūkusios seimo narių kadencijos/vėliau prasidėjusios seimo narių kadencijos (Matas Skamarakas)
# Kiek įvyko balsvimų kur target_mp buvo už prieš susilaikė nedalyvavo....
color_schema_legend = {"Už": "green",
                       "Prieš": "red",
                       "Susilaikė": "lightblue",
                       "Registravosi": "#FF9800",
                       "Nedalyvavo": "#9E9E9E"}
category_orders = {"vote": list(color_schema_legend.keys()),
                   "vote1": list(color_schema_legend.keys()),
                   "vote2": list(color_schema_legend.keys())}

target_mp = st.selectbox(
    "Which MP interests you?",
    options=list(dict_vote_combos.keys()),
    index=None,
    placeholder="Parlamentaras(-ė)",
)

if target_mp:
    df_voting_grouped_filt = df_voting_grouped.filter(pl.col("name") == target_mp)
    fig_target_mp_vote_summary = px.bar(
        df_voting_grouped_filt,
        x="count", y="name", color='vote', barmode="stack",
        color_discrete_map=color_schema_legend,
        category_orders=category_orders,
        orientation='h', title=f"Vote summary of {target_mp}"
    )

    st.plotly_chart(fig_target_mp_vote_summary, use_container_width=True)

    df_vote_combos = dict_vote_combos[target_mp]

    all_affiliations = df_vote_combos['mp2_affiliation'].unique().tolist()

    container = st.container()
    select_all = st.checkbox("Select all")
    if select_all:
        selected_affiliations = container.multiselect(f"Select affiliation (fraction) of parliamentarians you want"
                                                      f" {target_mp} to compare with",
                                                      all_affiliations, all_affiliations)
    else:
        selected_affiliations = container.multiselect(f"Select affiliation (fraction) of parliamentarians you want"
                                                      f" {target_mp} to compare with",
                                                      all_affiliations)

    for affiliation in selected_affiliations:
        df_affiliation = df_vote_combos.loc[df_vote_combos['mp2_affiliation'] == affiliation, :]

        mp_count = len(df_affiliation['mp2'].unique().tolist())
        size_per_category = 40
        fig_height = mp_count * size_per_category
        fig_height = fig_height if fig_height > 300 else 300

        fig = px.bar(df_affiliation,
                     facet_col_spacing=0.04,
                     x="count", y="mp2", color='vote2', barmode="stack",
                     orientation='h', title=affiliation, facet_col="vote1",
                     color_discrete_map=color_schema_legend,
                     category_orders=category_orders)
        fig.update_xaxes(matches=None, showticklabels=True)
        fig.for_each_annotation(lambda a: a.update(text=f"{target_mp}\n{a.text.split('=')[-1]}"))
        fig.update_layout(height=fig_height)

        st.plotly_chart(fig, use_container_width=True)

        # c1, c2, c3, c4, c5 = st.columns(5)
        # with c1:
        #     fig = px.bar(df_affiliation.loc[df_affiliation['vote1'] == 'Už', :],
        #                  x="count", y="mp2", color='vote2', barmode="stack",
        #                   orientation='h', title="Už")
        #
        #     st.plotly_chart(fig)
        #
        # with c2:
        #     fig = px.bar(df_affiliation.loc[df_affiliation['vote1'] == 'Prieš', :],
        #                  x="count", y="mp2", color='vote2', barmode="stack",
        #                   orientation='h', title="Prieš")
        #
        #     st.plotly_chart(fig)
        #
        # with c3:
        #     fig = px.bar(df_affiliation.loc[df_affiliation['vote1'] == 'Susilaikė', :],
        #                  x="count", y="mp2", color='vote2', barmode="stack",
        #                   orientation='h', title="Susilaikė")
        #     st.plotly_chart(fig)
        #
        # with c4:
        #     fig = px.bar(df_affiliation.loc[df_affiliation['vote1'] == 'Registravosi', :],
        #                  x="count", y="mp2", color='vote2', barmode="stack",
        #                   orientation='h', title="Registravosi")
        #     st.plotly_chart(fig)
        #
        # with c5:
        #     fig = px.bar(df_affiliation.loc[df_affiliation['vote1'] == 'Nedalyvavo', :],
        #                  x="count", y="mp2", color='vote2', barmode="stack",
        #                   orientation='h', title="Nedalyvavo")
        #
        #     st.plotly_chart(fig)
