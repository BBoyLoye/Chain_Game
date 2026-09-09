# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col

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

# Replace each list with a Snowflake query, e.g.
# session.table("CONTRACTS").filter(col("MODE") == "SEA").select("LANE").to_pandas()["LANE"].tolist()
sea_options = []
rail_options = []
truck_options = []

sea_col, rail_col, truck_col = st.columns(3)

with sea_col:
    st.subheader("Sea")
    df_sea = cnx.query("""SELECT DISTINCT quantity 
      FROM CHAIN_GAME_DEV.MARTS.FCT_CONTRACT_OPTIONS_SEA 
      ORDER BY quantity ASC;""")
    sea_contract = st.selectbox("Sea contract", df_sea["QUANTITY"].tolist(), index=None, placeholder="Select a sea contract")


with rail_col:
    st.subheader("Rail")
    rail_contract = st.selectbox("Rail contract", rail_options, index=None, placeholder="Select a rail contract")

with truck_col:
    st.subheader("Truck")
    truck_contract = st.selectbox("Truck contract", truck_options, index=None, placeholder="Select a truck contract")

st.header("Build Routes")
st.write(f"Streamlit Version: {st.__version__}")