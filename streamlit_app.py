# Import python packages
import streamlit as st
# from snowflake.snowpark.functions import col

cnx = st.connection("snowflake")
session = cnx.session()

# Write directly to the app
st.title("Come Play the Chain Game!")
st.header("Welcome to my project! If it's your first time playing, please click the button below.")

with st.expander("It's my first time"):
    st.write("My name is Brandon. I designed this game primarily as a portfolio piece to showcase my skills in data engineering and data science.")
    st.write("I currently work as a solutions engineer at Motive. I am proud to sell life-saving IOT devices and cutting-edge software, but since we've started offering some data analytics products and services, I've decided that my true passion is building solutions around these sorts of products.")
    st.write("The Chain Game is a simple simulation of a supply chain network. It is a game where you are a supply chain manager and you need to decide which routes to take to transport goods from your company's factory in China, to stores in a nine cities across the US.")
    st.write("As a supply chain manager, you have two tools at your disposal:")
    st.write("    1. You can make contracts with freight brokers to transport goods. You should make contracts to save money over paying 'spot rates,' which are often higher. But beware! You risk contracts being bloated, and forcing you to pay for freight services you won't need if demand goes down.")
    st.write("    2. Once your contracts are locked in, you'll be able to navigate REAL TIME spot rates for ocean, rail, and truck cargo to get products where they belong")
    st.write("Your goal is to get products to where they belong for as little cost as possible. Good luck!")

st.header("Demand Projections")
st.caption(
    "Each table shows projected unit demand by destination and product "
    "for one quarter."
)

@st.cache_data(ttl=600)
def load_demand_projections():
    return cnx.query("""
        SELECT
            demand.id,
            demand.period,
            city.city_name AS location,
            product.product_name AS product,
            demand.quantity
        FROM CHAIN_GAME_DEV.MARTS.FCT_DEMAND_PROJ AS demand
        LEFT JOIN CHAIN_GAME_DEV.MARTS.DIM_CITIES AS city
            ON demand.location = city.city_id
        LEFT JOIN CHAIN_GAME_DEV.MARTS.DIM_PRODUCTS AS product
            ON demand.product = product.sku
        ORDER BY
            demand.period,
            city.city_name,
            product.product_name
    """)

demand_projections = load_demand_projections()
demand_periods = sorted(demand_projections["PERIOD"].dropna().unique())
demand_columns = st.columns(2)

for period_index, period in enumerate(demand_periods):
    period_demand = demand_projections[
        demand_projections["PERIOD"] == period
    ]
    demand_matrix = period_demand.pivot_table(
        index="LOCATION",
        columns="PRODUCT",
        values="QUANTITY",
        aggfunc="sum",
        fill_value=0,
    )
    demand_matrix.index.name = "Location"
    demand_matrix.columns.name = "Product"

    with demand_columns[period_index % len(demand_columns)]:
        st.subheader(f"Quarter {int(period)}")
        st.dataframe(demand_matrix, use_container_width=True)

st.header("Contract Selection")

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

@st.cache_data(ttl=600)
def load_rail_contract_options():
    return cnx.query("""
        SELECT
            rail.rail_contract_id,
            rail.origin,
            origin_city.city_name AS origin_city,
            rail.destination,
            destination_city.city_name AS destination_city,
            rail.quantity,
            rail.price_per_container
        FROM CHAIN_GAME_DEV.MARTS.FCT_CONTRACT_OPTIONS_RAIL AS rail
        LEFT JOIN CHAIN_GAME_DEV.MARTS.DIM_CITIES AS origin_city
            ON rail.origin = origin_city.city_id
        LEFT JOIN CHAIN_GAME_DEV.MARTS.DIM_CITIES AS destination_city
            ON rail.destination = destination_city.city_id
        ORDER BY
            origin_city.city_name,
            destination_city.city_name,
            rail.quantity,
            rail.price_per_container
    """)

def render_contract_selector(mode, offers, contract_id_column):
    selected_contracts = []
    origins = sorted(
        {offer["ORIGIN_CITY"] for offer in offers if offer["ORIGIN_CITY"]}
    )
    origin_column, destination_column, contract_column = st.columns(3)

    with origin_column:
        st.markdown("**Origin**")
        selected_origins = []
        for origin in origins:
            origin_key = f"{mode}_origin_{origin}"
            if st.checkbox(origin, key=origin_key):
                selected_origins.append(origin)
            else:
                route_destinations = {
                    offer["DESTINATION_CITY"]
                    for offer in offers
                    if offer["ORIGIN_CITY"] == origin
                }
                for destination in route_destinations:
                    st.session_state.pop(
                        f"{mode}_destination_{origin}_{destination}", None
                    )
                    st.session_state.pop(
                        f"{mode}_contract_{origin}_{destination}", None
                    )

    selected_routes = []
    with destination_column:
        st.markdown("**Destination**")
        if not selected_origins:
            st.caption("Select an origin to see destinations.")

        for origin in selected_origins:
            destinations = sorted(
                {
                    offer["DESTINATION_CITY"]
                    for offer in offers
                    if offer["ORIGIN_CITY"] == origin
                    and offer["DESTINATION_CITY"]
                }
            )
            for destination in destinations:
                destination_key = f"{mode}_destination_{origin}_{destination}"
                route_label = f"{origin} → {destination}"
                if st.checkbox(route_label, key=destination_key):
                    selected_routes.append((origin, destination))
                else:
                    st.session_state.pop(
                        f"{mode}_contract_{origin}_{destination}", None
                    )

    with contract_column:
        st.markdown("**Contract Options**")
        if not selected_routes:
            st.caption("Select a destination to see contract options.")

        for origin, destination in selected_routes:
            matching_offers = [
                offer
                for offer in offers
                if offer["ORIGIN_CITY"] == origin
                and offer["DESTINATION_CITY"] == destination
            ]
            offer_by_id = {
                offer[contract_id_column]: offer for offer in matching_offers
            }
            contract_key = f"{mode}_contract_{origin}_{destination}"
            selected_contract_id = st.radio(
                f"{origin} → {destination}",
                list(offer_by_id),
                index=None,
                format_func=lambda contract_id, offers_by_id=offer_by_id: (
                    f"{int(offers_by_id[contract_id]['QUANTITY'])} containers at "
                    f"${offers_by_id[contract_id]['PRICE_PER_CONTAINER']:,.2f} each"
                ),
                key=contract_key,
            )
            if selected_contract_id is not None:
                selected_contracts.append(offer_by_id[selected_contract_id])

    return selected_contracts


sea_offers = load_sea_contract_options().to_dict("records")
rail_offers = load_rail_contract_options().to_dict("records")

st.subheader("Sea")
sea_contracts = render_contract_selector(
    "sea", sea_offers, "SEA_CONTRACT_ID"
)

st.divider()
st.subheader("Rail")
rail_contracts = render_contract_selector(
    "rail", rail_offers, "RAIL_CONTRACT_ID"
)

st.subheader("Selected Contracts")
all_selected_contracts = [
    ("Sea", contract) for contract in sea_contracts
] + [
    ("Rail", contract) for contract in rail_contracts
]

if all_selected_contracts:
    total_committed = 0
    for mode_name, contract in all_selected_contracts:
        quantity = int(contract["QUANTITY"])
        contract_cost = quantity * contract["PRICE_PER_CONTAINER"]
        total_committed += contract_cost
        st.write(
            f"**{mode_name}:** {quantity} containers from "
            f"{contract['ORIGIN_CITY']} to {contract['DESTINATION_CITY']} "
            f"(${contract_cost:,.2f})"
        )
    st.metric("Total committed spend", f"${total_committed:,.2f}")
else:
    st.info("No contracts selected.")


st.header("Delivery to last mile destinations")
st.write("With contracts in place, the remaining costs are calculated automatically.")
st.write("Goods that were delivered by sea or rail will be delivered to their local store first by default to save costs. Goods in excess of what a local store will need will be taken to the nearest store by truck.")



st.write(f"Streamlit Version: {st.__version__}")