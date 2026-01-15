import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

#第一部分：資料載入與處理
#先匯入原本的excel後，把原本的ipynb的code搬過來
#下面這個是代表把資料載入並處理的function（把資料處理程式碼放在這裡面，使用者每次點你的網站時就會自動更新）
st.set_page_config(page_title='Taiwan Export Amount',layout='wide')

@st.cache_data
def load_and_process_data():
    sale=pd.read_excel('../data/TWsalesamount.xls',header=[0,1])
    sale.reset_index(inplace=True)

# 把多層的columns變成單層
    sale.columns = [
    '_'.join([str(i) for i in col if i != ''])
    for col in sale.columns]
    sale = sale.drop(columns=['index'])

#先把datetime清乾淨，接著保留符合的季度格式的資料，最後轉換成datetime的格式
    sale[' _datetime'] = sale[' _datetime'].astype(str).str.strip()
    sale = sale[sale[' _datetime'].str.match(r'^\d{4}Q[1-4]$')]
    sale[' _datetime'] = (
        pd.PeriodIndex(sale[' _datetime'], freq='Q')
        .to_timestamp()
    )

#把datetime清理乾淨，並且去除空白頁面
    sale.rename(columns={' _datetime':'datetime'},inplace=True)
    sale.columns=sale.columns.str.strip()

#把資料轉成電腦看得懂的格式
    new_sale=pd.melt(frame=sale,
                   id_vars=['datetime'],
                   var_name='city_product',
                   value_name='sales_amount'
                   )    
#利用_作為分割欄位，期中n=1代表只分割一次（分割最先看到的_)
#expand=True代表將分割後的結果展開成多個欄位(DataFrame)
    new_sale[['country','product']] = new_sale['city_product'].str.split('_',n=1,expand=True)
    new_sale.drop(columns=['city_product'],inplace=True)

# 1) 把純空白/空字串變成 NaN（這步最關鍵）
    new_sale = new_sale.replace(r'^\s*$', np.nan, regex=True)
# 2) 確保 sales_amount 是數字（不能轉的會變 NaN）
    new_sale['sales_amount'] = pd.to_numeric(new_sale['sales_amount'], errors='coerce')
# 3) 刪掉關鍵欄位缺值的列
    new_sale = new_sale.dropna(subset=['datetime', 'country', 'product', 'sales_amount'])
# 4) 整理 index
    new_sale = new_sale.reset_index(drop=True)

#重新設定產品的名稱
    translation_dict={
        '化學品':'Chemicals',
        '塑膠、橡膠及其製品':'Plastics',
        '紡織品':'Textiles',
        '基本金屬及其製品':'Base metals/products',
        '電子產品':'Electronic products',
        '機械':'Machinery ',
        '電機產品':'Electrical machinery / product',
        '資訊與通信產品':'ICT products',
        '運輸工具及其設備':'Transport equipment',
        '光學器材':'Optical instruments',
        }
    new_sale['product']=new_sale['product'].replace(translation_dict)

    return new_sale.reset_index(drop=True)



#第二部分：繪圖
#取得整理後的資料
new_sale=load_and_process_data()
#dashboard的頁面標題
st.title('Taiwan Export Amount Analysis Dashboard') 

#出口總額隨時間的趨勢 (Overall Trend)
fig=px.line(new_sale.groupby('datetime',as_index=False)['sales_amount'].sum(),
            x='datetime',
            y='sales_amount',
            title='Taiwan Export Amount Overall Trend',
            labels={'datetime':'Date','sales_amount':'Export Amount (million dollars)'},
            width=800, height=500
)
st.plotly_chart(fig)

#不同國家的貢獻度 (Sales by Country)
contribute=new_sale.groupby(['country'],as_index=False)['sales_amount'].sum().copy()
contribute=contribute.sort_values(by='sales_amount',ascending=False)

fig=px.bar(data_frame=contribute,
           x='country',
           y='sales_amount',
           title='Taiwan Export Amount by Country/Region',
           labels={'country':'Country/Region','sales_amount':'Export Amount (million dollars)'},
            text_auto='.2s',
           )
st.plotly_chart(fig)

#各國出口總額隨時間的趨勢 (Trend by Country)
fig=px.line(new_sale.groupby(['datetime','country'],as_index=False)['sales_amount'].sum(),
            x='datetime',
            y='sales_amount',
            color='country',
            title='Taiwan Export Amount by Country/Region',
            labels={'datetime':'Date','sales_amount':'Export Amount (million dollars)','country':'Country/Region'},
            width=1000, height=500
)
st.plotly_chart(fig)

#各大產品類別的銷售表現 (Product Breakdown)
product_breakdown=new_sale.groupby(['product'],as_index=False)['sales_amount'].sum().copy()
product_breakdown=product_breakdown.sort_values(by='sales_amount',ascending=False)

fig=px.bar(data_frame=product_breakdown,
           x='product',
           y='sales_amount',
           title='Taiwan Export Amount by Product Category',
           labels={'product':'Product Category','sales_amount':'Export Amount (million dollars)'},
           text_auto='.2s',
           width=600, height=500
           )
st.plotly_chart(fig)

#各大產品類別的銷售表現 (Product Breakdown)
product_breakdown=new_sale.groupby(['product'],as_index=False)['sales_amount'].sum().copy()
product_breakdown=product_breakdown.sort_values(by='sales_amount',ascending=False)

fig=px.pie(data_frame=product_breakdown,
           values='sales_amount',
           names='product',
           title='Taiwan Export Amount by Product Category',
           labels={'product':'Product Category','sales_amount':'Export Amount (million dollars)'},
           width=600, height=500
           )

st.plotly_chart(fig)

#產品類別的銷售穩定度 (Sales Volatility)
volatility=new_sale.groupby(['product','datetime'],as_index=False)['sales_amount'].sum().copy()
fig=px.box(data_frame=volatility,
           x='product',
           y='sales_amount',
           title='Sales Volatility by Product Category',
           width=800, height=600,
)
fig.update_yaxes(type="log")
st.plotly_chart(fig)

#出口市場的季節性波動 (Seasonality)
new_sale['Quarter']=new_sale['datetime'].dt.quarter.astype(str)
new_sale['Year']=new_sale['datetime'].dt.year.astype(str)

seasonal_data=new_sale.groupby(['Year','Quarter','country'],as_index=False)['sales_amount'].sum().copy()

fig=px.line(data_frame=seasonal_data,
           x='Quarter',
           y='sales_amount', 
           title='Taiwan Export Seasonality by Country/Region',
           color='Year',
           labels={'Quarter':'Quarter','sales_amount':'Export Amount (million dollars)','country':'Country/Region'},
           facet_col='country',
           facet_col_wrap=3,
           markers=True,
           width=1000, height=800
            )
st.plotly_chart(fig)

#國家與產品的關聯熱力圖 (Country-Product Correlation)
product_correlation=new_sale.groupby(['country','product'],as_index=False)['sales_amount'].sum().copy()
fig=px.density_heatmap(data_frame=product_correlation,
                       x='product',
                       y='country',
                       z='sales_amount',
                       text_auto=True,
                       color_continuous_scale='RdBu_r',
                       labels={'product':'Product','country':'Country/Region','sales_amount':'Export Amount '},
                       title='Country-Product Export Amount Correlation Heatmap',
                       width=900, height=700
                       )
st.plotly_chart(fig)

#ICT與電子產品的年成長率比較 (Year-over-Year Growth for ICT and Electronic Products)
target=['ICT products', 'Electronic products']
new_sale_target=new_sale[new_sale['product'].isin(target)].copy()

new_sale['Year']=new_sale['datetime'].dt.year.astype(str)

yearly_comp=new_sale_target.groupby(['Year','product'],as_index=False)['sales_amount'].sum()
yearly_comp['YoY_Growth'] = yearly_comp.groupby('product')['sales_amount'].pct_change() * 100

#計算完畢後，再過濾掉 2017 與 2025
plot_data = yearly_comp[~yearly_comp['Year'].isin(['2017', '2025'])]

fig=px.bar(data_frame=plot_data,
           x='Year',
           y='YoY_Growth',
           color='product',
           barmode='group',
           title='Year-over-Year Growth for ICT and Electronic Products',
           labels={'Year':'Year','YoY_Growth':'Growth Rate(%)'},
           text_auto='.2f',
              width=800, height=500)
st.plotly_chart(fig)


