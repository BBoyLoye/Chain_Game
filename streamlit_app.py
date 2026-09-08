# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col

# Write directly to the app
st.title("Come Play the Chain Game!")
st.write(
  """Welcome to my project! If it's your first time playing, please click the button below.
  """
)

with st.expander("It's my first time"):
    st.write("My name is Brandon. I designed this game primarily as a portfolio piece to showcase my skills in data engineering and data science.")
    st.write("I currently work as a solutions engineer at Motive. I am proud to sell life-saving IOT devices and cutting-edge software, but since we've started offering some data analytics products and services, I've decided that my true passion is building solutions around these sorts of products.")
    st.write("The Chain Game is a simple simulation of a supply chain network. It is a game where you are a supply chain manager and you need to decide which routes to take to transport goods from your company's factory in Shenzhen, to your dozen stores in the US.")
    st.write("As a supply chain manager, you have two tools at your disposal:")
    st.write("    1. You can make contracts with freight brokers to transport goods. You should make contracts to save money over paying 'spot rates,' which are often higher. But beware! You risk contracts being bloated, and forcing you to pay for freight services you won't need if demand goes down.")
    st.write("    2. Once your contracts are locked in, you'll be able to navigate REAL TIME spot rates for ocean, rail, and truck cargo to get products where they belong")
    st.write("")
    st.write("Your goal is to get products to where they belong for as little cost as possible. Good luck!")
    
# You can also add formatting, bold text, or markdown links inside
st.markdown("**Tip:** Check the sidebar for current freight market rates!")

cnx = st.connection("snowflake")
session = cnx.session()

# Use an interactive slider to get user input
hifives_val = st.slider(
  "Number of high-fives in Q3",
  min_value=0,
  max_value=90,
  value=60,
  help="Use this to enter the number of high-fives you gave in Q3",
)

#  Create an example dataframe
#  Note: this is just some dummy data, but you can easily connect to your Snowflake data
#  It is also possible to query data using raw SQL using session.sql() e.g. session.sql("select * from table")
created_dataframe = session.create_dataframe(
  [[50, 25, "Q1"], [20, 35, "Q2"], [hifives_val, 30, "Q3"]],
  schema=["HIGH_FIVES", "FIST_BUMPS", "QUARTER"],
)

# Execute the query and convert it into a Pandas dataframe
queried_data = created_dataframe.to_pandas()

# Create a simple bar chart
# See docs.streamlit.io for more types of charts
st.subheader("Number of high-fives")
st.bar_chart(data=queried_data, x="QUARTER", y="HIGH_FIVES")

st.subheader("Underlying data")
st.dataframe(queried_data, use_container_width=True)

st.write(f"Streamlit Version: {st.__version__}")
