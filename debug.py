import pandas as pd
import streamlit as st

sale=pd.read_excel('TWsalesamount.xls',header=[0,1])

st.set_page_config(page_title='Taiwan Export Amount',layout='wide')
