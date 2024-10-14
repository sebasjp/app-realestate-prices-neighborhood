import os
import requests
import matplotlib.pyplot as plt
import streamlit as st

ENDPOINT = os.getenv("ENDPOINT_PRICES_NEIGHBORHOOD")

def plot_bars_from_dict(count_dict: dict, feature: str):
    plt.figure()
    lists = sorted(count_dict.items()) # sorted by key, return a list of tuples
    x, y = zip(*lists) # unpack a list of pairs into two tuples
    plt.bar(x, y)
    plt.title(f'Cantidad de {feature} en la Zona')
    plt.xlabel(f'Cantidad de {feature}')
    plt.ylabel('Cantidad')
    st.pyplot(plt)


def plot_dist_from_list(dist_list: list, feature: str):
    plt.figure()
    plt.hist(dist_list)
    plt.title(f'{feature} en la Zona')
    plt.xlabel(feature)
    plt.ylabel('Cantidad')
    st.pyplot(plt)


def make_request(inputs: dict):
    
    print(inputs)
    response = requests.post(ENDPOINT, json=inputs)
    print(response)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None


def format_cop(x: float):
    return '${:,.0f}'.format(x)+" COP"
