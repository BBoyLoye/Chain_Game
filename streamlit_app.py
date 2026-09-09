# Import python packages
import streamlit as st
# from snowflake.snowpark.functions import col

# Write directly to the app
st.title("Come Play the Chain Game!")
st.header("Welcome to my project! If it's your first time playing, please click the button below.")

with st.expander("It's my first time"):
    st.write("My name is Brandon. I designed this game primarily as a portfolio piece to showcase my skills in data engineering and data science.")
    st.write("I currently work as a solutions engineer at Motive. I am proud to sell life-saving IOT devices and cutting-edge software, but since we've started offering some data analytics products and services, I've decided that my true passion is building solutions around these sorts of products.")
    st.write("The Chain Game is a simple simulation of a supply chain network. It is a game where you are a supply chain manager and you need to decide which routes to take to transport goods from your company's factory in Shenzhen, to your dozen stores in the US.")
    st.write("As a supply chain manager, you have two tools at your disposal:")
    st.write("    1. You can make contracts with freight brokers to transport goods. You should make contracts to save money over paying 'spot rates,' which are often higher. But beware! You risk contracts being bloated, and forcing you to pay for freight services you won't need if demand goes down.")
    st.write("    2. Once your contracts are locked in, you'll be able to navigate REAL TIME spot rates for ocean, rail, and truck cargo to get products where they belong")
    st.write("Your goal is to get products to where they belong for as little cost as possible. Good luck!")
    
# You can also add formatting, bold text, or markdown links inside
st.markdown("**Tip:** Check the sidebar for current freight market rates!")

cnx = st.connection("snowflake")
session = cnx.session()

st.header("Contract Selection")

rail_options = []
truck_options = []

sea_col, rail_col, truck_col = st.columns(3)

with sea_col:
    st.subheader("Sea")

    @st.cache_data(ttl=600)
    def load_sea_contract_options():
        return cnx.query("""
            SELECT
                sea.sea_contract_id,
                sea.origin,
                origin_city.city_name AS origin_city,
                sea.destination,
                destination_city.city_name AS destination_city,
                sea.quantity,
                sea.price_per_container
            FROM CHAIN_GAME_DEV.MARTS.FCT_CONTRACT_OPTIONS_SEA AS sea
            LEFT JOIN CHAIN_GAME_DEV.MARTS.DIM_CITIES AS origin_city
                ON sea.origin = origin_city.city_id
            LEFT JOIN CHAIN_GAME_DEV.MARTS.DIM_CITIES AS destination_city
                ON sea.destination = destination_city.city_id
            ORDER BY
                origin_city.city_name,
                destination_city.city_name,
                sea.quantity,
                sea.price_per_container
        """)

    sea_contract_data = load_sea_contract_options()
    sea_offers = sea_contract_data.to_dict("records")
    sea_origins = sorted(
        {offer["ORIGIN_CITY"] for offer in sea_offers if offer["ORIGIN_CITY"]}
    )
    sea_destinations = sorted(
        {offer["DESTINATION_CITY"] for offer in sea_offers if offer["DESTINATION_CITY"]}
    )

    if "sea_contract_rows" not in st.session_state:
        st.session_state.sea_contract_rows = [0]
        st.session_state.next_sea_contract_row = 1

    def selected_routes(excluded_row_id):
        routes = set()
        for contract_row_id in st.session_state.sea_contract_rows:
            if contract_row_id == excluded_row_id:
                continue
            origin = st.session_state.get(f"sea_from_{contract_row_id}")
            destination = st.session_state.get(f"sea_to_{contract_row_id}")
            if origin and destination:
                routes.add((origin, destination))
        return routes

    sea_contracts = []

    for row_index, row_id in enumerate(list(st.session_state.sea_contract_rows)):
        from_key = f"sea_from_{row_id}"
        to_key = f"sea_to_{row_id}"
        offer_key = f"sea_for_{row_id}"
        routes_in_other_rows = selected_routes(row_id)

        selected_destination = st.session_state.get(to_key)
        available_origins = [
            origin
            for origin in sea_origins
            if origin != selected_destination
            and (origin, selected_destination) not in routes_in_other_rows
        ]
        if st.session_state.get(from_key) not in available_origins:
            st.session_state.pop(from_key, None)

        row_columns = st.columns([3, 3, 4, 1, 1])

        with row_columns[0]:
            selected_origin = st.selectbox(
                "From",
                available_origins,
                index=None,
                placeholder="Select origin",
                key=from_key,
            )

        available_destinations = [
            destination
            for destination in sea_destinations
            if destination != selected_origin
            and (selected_origin, destination) not in routes_in_other_rows
        ]
        if st.session_state.get(to_key) not in available_destinations:
            st.session_state.pop(to_key, None)

        with row_columns[1]:
            selected_destination = st.selectbox(
                "To",
                available_destinations,
                index=None,
                placeholder="Select destination",
                key=to_key,
            )

        matching_offers = [
            offer
            for offer in sea_offers
            if offer["ORIGIN_CITY"] == selected_origin
            and offer["DESTINATION_CITY"] == selected_destination
        ]
        offer_by_id = {
            offer["SEA_CONTRACT_ID"]: offer for offer in matching_offers
        }
        if st.session_state.get(offer_key) not in offer_by_id:
            st.session_state.pop(offer_key, None)

        with row_columns[2]:
            selected_offer_id = st.selectbox(
                "For",
                list(offer_by_id),
                index=None,
                placeholder="Select terms",
                format_func=lambda contract_id: (
                    f"{offer_by_id[contract_id]['QUANTITY']} containers for "
                    f"${offer_by_id[contract_id]['PRICE_PER_CONTAINER']:.2f} "
                    "per container"
                ),
                key=offer_key,
            )

        with row_columns[3]:
            if st.button("＋", key=f"add_sea_contract_{row_id}", help="Add contract"):
                new_row_id = st.session_state.next_sea_contract_row
                st.session_state.next_sea_contract_row += 1
                st.session_state.sea_contract_rows.insert(row_index + 1, new_row_id)
                st.rerun()

        with row_columns[4]:
            if st.button(
                "−",
                key=f"remove_sea_contract_{row_id}",
                help="Delete contract",
                disabled=len(st.session_state.sea_contract_rows) == 1,
            ):
                st.session_state.sea_contract_rows.remove(row_id)
                for key in (from_key, to_key, offer_key):
                    st.session_state.pop(key, None)
                st.rerun()

        if selected_offer_id is not None:
            sea_contracts.append(offer_by_id[selected_offer_id])

with rail_col:
    st.subheader("Rail")
    rail_contract = st.selectbox("Rail contract", rail_options, index=None, placeholder="Select a rail contract")

with truck_col:
    st.subheader("Truck")
    truck_contract = st.selectbox("Truck contract", truck_options, index=None, placeholder="Select a truck contract")

st.header("Build Routes")
st.write(f"Streamlit Version: {st.__version__}")