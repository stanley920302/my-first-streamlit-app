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
st.subheader('1. Taiwan Export Amount Overall Trend')

fig=px.line(new_sale.groupby('datetime',as_index=False)['sales_amount'].sum(),
            x='datetime',
            y='sales_amount',
            labels={'datetime':'Date','sales_amount':'Export Amount (million dollars)'},
            width=800, height=500
)
st.plotly_chart(fig)

#用來設定將圖二及圖三並排顯示
col1, col2 = st.columns([1.5,2])
#不同國家的貢獻度 (Sales by Country)
with col1:
    st.subheader('2. Taiwan Export Amount by Country/Region(bar chart)')

    contribute=new_sale.groupby(['country'],as_index=False)['sales_amount'].sum().copy()
    contribute=contribute.sort_values(by='sales_amount',ascending=False)

    fig=px.bar(data_frame=contribute,
            x='country',
            y='sales_amount',
            labels={'country':'Country/Region','sales_amount':'Export Amount (million dollars)'},
                text_auto='.2s',
            )
    st.plotly_chart(fig, use_container_width=True)

#各國出口總額隨時間的趨勢 (Trend by Country)
with col2:
    st.subheader('3. Taiwan Export Amount by Country/Region(line chart)')

    fig=px.line(new_sale.groupby(['datetime','country'],as_index=False)['sales_amount'].sum(),
                x='datetime',
                y='sales_amount',
                color='country',
                labels={'datetime':'Date','sales_amount':'Export Amount (million dollars)','country':'Country/Region'},
                width=1000, height=500
    )
    st.plotly_chart(fig, use_container_width=True)

#各大產品類別的銷售表現 (Product Breakdown)
st.subheader('4. Taiwan Export Amount by Product Category')

# 建立單選選單
all_countries = ['Total'] + sorted(new_sale['country'].unique())
selected_country_breakdown = st.selectbox(
    "Select a Country to View Product Mix:",
    options=all_countries,
    index=0 # 預設選第一個
)

# 資料篩選
if selected_country_breakdown == 'Total':
    # 如果選 Total，使用原始完整資料，不進行篩選
    plot_data = new_sale
else:
    # 如果選特定國家，篩選該國家的資料
    plot_data = new_sale[new_sale['country'] == selected_country_breakdown]

product_breakdown=plot_data.groupby(['product'],as_index=False)['sales_amount'].sum().copy()
product_breakdown=product_breakdown.sort_values(by='sales_amount',ascending=False)

fig=px.bar(data_frame=product_breakdown,
           x='product',
           y='sales_amount',
           labels={'product':'Product Category','sales_amount':'Export Amount (million dollars)'},
           text_auto='.2s',
           width=600, height=500
           )
st.plotly_chart(fig)

#各大產品類別的銷售表現 (Product Breakdown)
st.subheader('5. Taiwan Export Amount by Product Category')

product_breakdown=new_sale.groupby(['product'],as_index=False)['sales_amount'].sum().copy()
product_breakdown=product_breakdown.sort_values(by='sales_amount',ascending=False)

fig=px.pie(data_frame=product_breakdown,
           values='sales_amount',
           names='product',
           labels={'product':'Product Category','sales_amount':'Export Amount (million dollars)'},
           width=600, height=500
           )

st.plotly_chart(fig)

#產品類別的銷售穩定度 (Sales Volatility)
st.subheader('6. Sales Volatility by Product Category')

volatility=new_sale.groupby(['product','datetime'],as_index=False)['sales_amount'].sum().copy()
fig=px.box(data_frame=volatility,
           x='product',
           y='sales_amount',
           width=800, height=600,
)
fig.update_yaxes(type="log")
st.plotly_chart(fig)

#出口市場的季節性波動 (Seasonality)
st.subheader('7. Taiwan Export Seasonality by Country/Region')

new_sale['Quarter']=new_sale['datetime'].dt.quarter.astype(str)
new_sale['Year']=new_sale['datetime'].dt.year.astype(str)

seasonal_data=new_sale.groupby(['Year','Quarter','country'],as_index=False)['sales_amount'].sum().copy()

fig=px.line(data_frame=seasonal_data,
           x='Quarter',
           y='sales_amount', 
           color='Year',
           labels={'Quarter':'Quarter','sales_amount':'Export Amount (million dollars)','country':'Country/Region'},
           facet_col='country',
           facet_col_wrap=3,
           markers=True,
           width=1000, height=800
            )
st.plotly_chart(fig)

#國家與產品的關聯熱力圖 (Country-Product Correlation)
st.subheader('8. Country-Product Export Amount Correlation Heatmap')

product_correlation=new_sale.groupby(['country','product'],as_index=False)['sales_amount'].sum().copy()
fig=px.density_heatmap(data_frame=product_correlation,
                       x='product',
                       y='country',
                       z='sales_amount',
                       text_auto=True,
                       color_continuous_scale='RdBu_r',
                       labels={'product':'Product','country':'Country/Region','sales_amount':'Export Amount '},
                       width=900, height=700
                       )
st.plotly_chart(fig)



#各產品類別的年成長率比較 (Year-over-Year Growth Comparison for Products)
# 1. 建立選項清單：手動加入 'Total' 到最前面
st.subheader('9. Year-over-Year Growth Comparison (Including Total)')
unique_products = new_sale['product'].unique().tolist()
options = ['Total'] + unique_products  # 將 Total 放在第一個選項

# 2. 建立多選選單
selected_options = st.multiselect(
    'Please select items to compare (including Total):',
    options=options,
    default=['Total', 'ICT products'] # 預設可以選 Total 和某個產品來對比
)

if selected_options:
    # 準備一個 list 來存放要合併的 dataframe
    data_frames_to_plot = []
    
    # --- 處理個別產品 (非 Total 的部分) ---
    # 找出使用者選了哪些「真實產品」
    real_products = [p for p in selected_options if p != 'Total']
    
    if real_products:
        # 篩選這些產品
        df_products = new_sale[new_sale['product'].isin(real_products)].copy()
        # 依照 年份+產品 加總
        grouped_products = df_products.groupby(['Year', 'product'], as_index=False)['sales_amount'].sum()
        data_frames_to_plot.append(grouped_products)
    
    # --- 處理 Total (如果使用者有選 Total) ---
    if 'Total' in selected_options:
        # 針對「全部資料」依照年份加總 (不分產品)
        df_total = new_sale.groupby(['Year'], as_index=False)['sales_amount'].sum()
        # 手動給予 product 欄位名稱為 'Total'，這樣等等才能跟其他產品一起畫圖
        df_total['product'] = 'Total' 
        data_frames_to_plot.append(df_total)
    
    # --- 合併資料並計算 YoY ---
    if data_frames_to_plot:
        # 將「個別產品資料」與「Total資料」上下合併
        final_comp = pd.concat(data_frames_to_plot, ignore_index=True)
        
        # 關鍵：一定要先排序 (產品 -> 年份)，這樣 pct_change 才會算對
        final_comp = final_comp.sort_values(by=['product', 'Year'])
        
        # 計算 YoY
        final_comp['YoY_Growth'] = final_comp.groupby('product')['sales_amount'].pct_change() * 100
        
        # 過濾掉不完整的年份 (2017, 2025)
        plot_data = final_comp[~final_comp['Year'].isin(['2017', '2025'])]
        
        # 繪圖
        fig = px.bar(
            data_frame=plot_data,
            x='Year',
            y='YoY_Growth',
            color='product',
            barmode='group',
            labels={'Year': 'Year', 'YoY_Growth': 'Growth Rate(%)'},
            text_auto='.2f',
            width=800, 
            height=500,
            title='YoY Growth Comparison (Including Total)'
        )
        
        st.plotly_chart(fig)
else:
    st.warning("Please select at least one item to compare.")