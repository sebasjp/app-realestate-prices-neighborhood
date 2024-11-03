import streamlit as st
import statistics
from utils import (
    make_request, 
    format_cop, 
    plot_bars_from_dict,
    plot_dist_from_list
)
from unidecode import unidecode
# Map to capture coordinates
import folium as fl
from streamlit_folium import st_folium


# state to give time to the api processing
if 'is_streaming' not in st.session_state:
    st.session_state.is_streaming = False

if 'api_response' not in st.session_state:
    st.session_state.api_response = None

if 'input_request' not in st.session_state:
    st.session_state.input_request = None

# Streamlit app
st.title("Analisis de datos: Real Estate :bar_chart: :nerd_face:")
msg = (
    "Esta herramienta está diseñada para ayudar en el **aprendizaje "
    "de la debida diligencia**, centrándose en el análisis cuantitativo de las rentas tradicionales. "
    "El objetivo es facilitar la revisión del mercado en una zona de interés, utilizando datos extraídos en Oct/2024 "
    "de alrededor de 30mil anuncios (entre casas y apartamentos en venta o arriendo) "
    "de la página https://www.fincaraiz.com.co/.\n\n"

    "**¿Cómo funciona?**\n\n"
    "1. Debes tener un inmueble (**casa** o **apartamento**) que quieras revisar, "
    "ya sea porque quieras invertir, "
    "o quieras conocer el valor actual del precio por m2 medio de **arriendo** o **venta**.\n\n"
    "2. Esta herramienta compara los inmuebles vecinos (cercanos) a la ubicación que le ingresas.\n\n"
    "3. Calcula el precio medio, características de los inmuebles de la zona y se muestran "
    "las publicaciones encontradas ordenadas por precio por m2.\n\n"

    "**La información aqui presentada es con fines académicos y no representa "
    "ninguna recomendación ni publicidad.**"
)
st.markdown(msg)

# Input fields
st.markdown("### Datos de entrada")
st.markdown("Aquí se ingresan los datos del inmueble o zona que deseas evaluar.")
city = st.selectbox("Ciudad :cityscape:", ["Bogotá", "Medellín", "Cali"], index=None)
business_type = st.selectbox("Tipo de negocio :nerd_face:", ["Arriendo", "Venta"], index=None)
property_type = st.selectbox("Tipo de propiedad :house_buildings:", ["Apartamento", "Casa"], index=None)
area = st.number_input("Area (m2) :black_square_button:", value=None, placeholder=70.20, format="%.2f")

if city:
    city = unidecode(city).lower()
if business_type:
    business_type = business_type.lower()
if property_type:
    property_type = property_type.lower()

# call to render Folium map in Streamlit
if city=="bogota":
    start_coords = [4.7109886, -74.072092]
elif city=="medellin":
    start_coords = [6.2476376, -75.5658153]
elif city=="cali":
    start_coords = [3.4516467, -76.5319854]
else:
    start_coords = [4.570868,-74.297333]

st.write("Escoja el lugar de interes :world_map:")
m = fl.Map(location=start_coords, zoom_start=11)
m.add_child(fl.LatLngPopup())
map_data = st_folium(m, height=300, width=700)

if map_data["last_clicked"]:
    lat_val = map_data["last_clicked"]["lat"]
    lon_val = map_data["last_clicked"]["lng"]
else:
    lat_val = None
    lon_val = None

lat = st.number_input("Latitude :world_map:", value=lat_val, placeholder=4.1157, format="%.4f")
lon = st.number_input("Longitude :world_map:", value=lon_val, placeholder=-72.9301, format="%.4f")

# validar que todos los datos existan
if (city and business_type and property_type and area and lat and lon):
    disable_process = False
else:
    disable_process = True

if st.button(
    "Procesar", 
    use_container_width=True, 
    disabled=disable_process
):
    # Call API with input data
    input_request = {
        "city": city, 
        "business_type": business_type, 
        "property_type": property_type,
        "area_m2": area,
        "lat": lat,
        "lon": lon
    }
    st.session_state.api_response = make_request(input_request)
    st.session_state.input_request = input_request

    # declare streaming states
    st.session_state.is_streaming = True
    st.session_state.is_streaming_refined = False

st.markdown("---")

if st.session_state.is_streaming:

    if st.session_state.api_response:
        api_response = st.session_state.api_response.copy()
        input_request = st.session_state.input_request.copy()

        # Extracting data from the response
        ratio_used = api_response.get('ratio_used')
        offer_ratios = api_response.get('offer_ratios')
        price_m2 = api_response.get('med_price_m2_neigh')

        # first validate if we have a metric as response
        if price_m2:
            price_full = api_response.get('med_price_full_neigh')
            count_bathrooms_neigh = api_response.get("count_bathrooms_neigh")
            count_bedrooms_neigh = api_response.get("count_bedrooms_neigh")
            count_ant_neigh = api_response.get("count_ant_neigh")
            neigh_data = api_response.get('neigh')
            dist_area_neigh = [row["m2"] for row in neigh_data]
            

            # Displaying results
            st.markdown("## Resultados :chart_with_upwards_trend:")
            # ============= metrics ============= #
            st.markdown(
                "A continuación, se muestra valor medio del precio por m2, el area que ingresaste * precio por m2 medio y "
                "la cantidad de **publicaciones vecinas** utilizadas para estos calculos, "
                "es decir, aquellos que se encuentran "
                f"a menos de {ratio_used}mts de la coordenada ingresada."
            )
            col1, col2, col3 = st.columns(3)
            st.markdown(
                """
            <style>
            [data-testid="stMetricValue"] {
                font-size: 20px;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )
            col1.metric(label=f"Cant. a menos de {ratio_used}mts", value=offer_ratios[str(ratio_used)])
            col2.metric(label="Precio por m²", value=format_cop(price_m2))
            col3.metric(label="Total precio (precio m² x area)", value=format_cop(price_full))

            # ============= table ============= #
            st.markdown(
                f"En la siguiente tabla se muestran las {offer_ratios[str(ratio_used)]} publicaciones vecinas. "
                "La columna `posicion` indica el orden de acuerdo con el precio por m2, "
                f"donde 1 indica el más económico y el {offer_ratios[str(ratio_used)]} el más costoso."
            )
            neigh_data = sorted(neigh_data, key=lambda d: d['price_m2'])
            data_display = [
                {
                "posicion": ix+1,
                "link": "https://www.fincaraiz.com.co"+row["link"],
                "price_m2": round(row["price_m2"]),
                "m2": row["m2"],              
                "price_published": row["price_admin_included"],
                "bathrooms": row["bathrooms"],
                "bedrooms": row["bedrooms"]
                }
                for ix, row in enumerate(neigh_data)
            ]
            st.dataframe(
                data_display,
                column_config={"link": st.column_config.LinkColumn("URL")}
            )            
            # ============= graficos ============= #
            st.markdown("### Caracteristicas de los inmuebles vecinos :toilet: :sleeping_accommodation:")
            
            colbath, colbed = st.columns(2)
            colant, colarea = st.columns(2)

            with colbath:
                # Number of bathrooms in the zone
                plot_bars_from_dict(count_bathrooms_neigh, "Baños")
            with colbed:
                # Number of bedrooms in the zone
                plot_bars_from_dict(count_bedrooms_neigh, "Habitaciones")
            with colant:
                # Antiguedad en la zona
                plot_bars_from_dict(count_ant_neigh, "Antiguedad")
            with colarea:
                # Antiguedad en la zona
                plot_dist_from_list(dist_area_neigh, "Area")

            st.markdown(
                "---\n\n"
                "**A continuación, puedes refinar el cálculo del precio por m2, agregando información sobre la "
                "cantidad de baños y/o cantidad de habitaciones de interes.**"
            )
            # refinamiento por cantidad de baños y habitaciones
            num_bathrooms = st.selectbox(
                "Numero de baños :toilet:", 
                count_bathrooms_neigh.keys(), 
                index=None
            )
            num_bedrooms = st.selectbox(
                "Numero de habitaciones :sleeping_accommodation:", 
                count_bedrooms_neigh.keys(), 
                index=None
            )
            # validar datos
            if num_bathrooms or num_bedrooms:
                disable_process_refined = False
            else:
                disable_process_refined = True

            if st.button("Refinar indicadores", use_container_width=True, disabled=disable_process_refined):
                st.session_state.is_streaming_refined = True

            if st.session_state.is_streaming_refined:
                neigh_data_refined = neigh_data.copy()
                if num_bathrooms:
                    num_bathrooms = float(num_bathrooms)
                    neigh_data_refined = [
                        row for row in neigh_data_refined if row["bathrooms"]==num_bathrooms
                    ]
                if num_bedrooms:
                    num_bedrooms = float(num_bedrooms)
                    neigh_data_refined = [
                        row for row in neigh_data_refined if row["bedrooms"]==num_bedrooms
                    ]
                
                if len(neigh_data_refined)>0:
                    # precio medio por metro2
                    price_m2_refined = round(
                        statistics.median([
                            x["price_m2"] for x in neigh_data_refined
                        ])
                    )
                    # precio medio full
                    price_full_refined = round(
                        price_m2_refined * input_request["area_m2"]
                    )
                    col11, col21, col31 = st.columns(3)
                    col11.metric(label=f"Cant. a menos de {ratio_used}mts", value=len(neigh_data_refined))
                    col21.metric(label="Precio por m²", value=format_cop(price_m2_refined))
                    col31.metric(label="Total precio (precio m² x area)", value=format_cop(price_full_refined))
                else:
                    st.markdown(
                        f"**No se encontraron publicaciones con las características ingresadas, "
                        "por lo tanto no se pueden obtener resultados.**"
                    )
                    st.markdown("---")
        else:
            st.markdown(
                f"**No se encontraron publicaciones a menos de {ratio_used}mts de la coordenada ingresada, "
                "por lo tanto no se pueden obtener resultados.**"
            )
            st.markdown("---")

st.markdown(":link: Elaborado por: https://www.linkedin.com/in/sjimenezp/")