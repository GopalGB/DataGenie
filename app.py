import streamlit as st
import pandas as pd
from helpers.utils import clicked, describe_dataframe, to_show, checkbox_clicked, additional_clicked_fun
from helpers.llm import first_look_function, eda_selection_generator, individual_eda, aaa_sample_generator, aaa_answer_generator
from helpers.llm import filled_eda_prompt, filled_aaa_prompt
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.output_parsers import JsonOutputParser

from helpers.vis import chart_generator, vis_generator


from dotenv import load_dotenv
load_dotenv()

# Initialization
if 'clicked' not in st.session_state:
    st.session_state.clicked = {'begin_button': False}

if 'eda_selection' not in st.session_state:
    st.session_state.eda_selection = []

if 'data_exist' not in st.session_state:
    st.session_state.data_exist = False

if 'checkbox_menu' not in st.session_state:
    st.session_state.checkbox_menu = {
        'show_data_button': True,
        'eda_button': True,
        'va_button': True,
        'aaa_button': True
    }

if 'column_names' not in st.session_state:
    st.session_state.column_names = None

if 'df_details' not in st.session_state:
    st.session_state.df_details = None

if 'refreshed' not in st.session_state:
    st.session_state.refreshed = {
        'peda_clicked' : 0,
        'aaa_clicked': 0,
        'va_clicked': 0
    } 

st.set_page_config(page_title="DataGenie", page_icon="🧞‍♂️")

# LLM Declaration
llm = ChatOpenAI(model_name='gpt-4-0125-preview')

st.markdown("<h1 style='text-align: center;'>Data Genie 🧞‍♂️</h1>", unsafe_allow_html=True)
st.text('I am your helpful Exploratory Data Analysis Assistant powered by Langchain OpenAI')

col1, col2, col3 = st.columns(3)
with col2:
    st.button("Let's begin the magic", on_click=clicked, args=['begin_button'])

if st.session_state.clicked['begin_button']:    
    with st.expander('Upload your .csv data here'):
        data = st.file_uploader(' ', type ='csv')
    if data is not None:
        st.session_state.data_exist = True
        df = pd.read_csv(data, low_memory=False)
        st.session_state.column_names = df.columns


        pd_agent = create_pandas_dataframe_agent(llm, df, verbose=True)
        if st.session_state.checkbox_menu['show_data_button']:
            st.divider()
            st.subheader('Show Data')
            
            show_selection = ['First few rows', 'Last few rows', 'Random']
            show_selected = st.selectbox('Select type of EDA to perform on this dataset:', options=show_selection)
            rows_to_show = st.number_input('How many rows to show?', format='%d', step=1, value = 5)
            st.write(to_show(df, show_selected, rows_to_show))

        if st.session_state.checkbox_menu['eda_button']:
            st.divider()
            st.subheader('Exploratory Data Analysis')

            df_details = describe_dataframe(df)
            st.session_state.df_details = df_details

            eda_chain = LLMChain(llm=llm, prompt=filled_eda_prompt)

            eda_selection = eda_selection_generator(eda_chain, df_details)
            st.session_state.eda_selection = eda_selection

            eda_list = eda_selection.split('.\n-')[1:]
            eda_list.insert(0, '[Default] Perform default EDA')
            
            st.markdown('#### EDA to Perform')

            eda_selected = st.selectbox('Based on the dataframe, here are the most common EDA steps to perform:', options=eda_list)
            
            if st.button('Perform EDA', on_click=additional_clicked_fun, args=['peda_clicked']):
                prompt = PromptTemplate.from_template(eda_selected)
                with st.chat_message('assistant'):
                    if eda_selected != '[Default] Perform default EDA':
                        individual_eda(pd_agent, eda_selected, st.session_state.refreshed['peda_clicked'])
                    else:
                        first_look_function(df, pd_agent)
                    
        if st.session_state.checkbox_menu['va_button']:
            st.divider()
            st.subheader("Visualization")
            user_question_vis = st.text_area("Tell me what you want to visualize/ investigate!")
            st.button('Start Visualization', on_click=additional_clicked_fun, args=['va_clicked'])
            if user_question_vis and st.session_state.refreshed['va_clicked']:
                with st.spinner("Generating Chart Type"):
                    chart = chart_generator(llm, df, user_question_vis)
                st.write("Chart to be Produced:")
                st.write(chart)
                with st.spinner("Performing Feature Engineering and Charting!"):
                    vis_generator(chart[0], llm, df)
           

        if st.session_state.checkbox_menu['aaa_button']:
            st.divider()
            st.subheader("Ask AI Anything")
            st.write('Hint: Check sidebar for Prompt Inspiration')
            user_prompt = st.text_area('Enter your question here!')
            st.button('Ask your question', on_click=additional_clicked_fun, args=['aaa_clicked'])
            if user_prompt and st.session_state.refreshed['aaa_clicked']:
                aaa_answer_generator(pd_agent, user_prompt, st.session_state.refreshed['aaa_clicked'])


with st.sidebar:
    if st.session_state.clicked['begin_button']:
        st.header('Guide')
        st.write('1. To begin, enter data in .csv format.')
        if st.session_state.data_exist == True:
            st.write('2. Choose what do you want to do?')
            show_data_button = st.checkbox('Show Data', True, on_change=checkbox_clicked, args=['show_data_button'])
            eda_button = st.checkbox('Exploratory Data Analysis', True, on_change=checkbox_clicked, args=['eda_button'])
                
            va_button = st.checkbox('Visualization', True, on_change=checkbox_clicked, args=['va_button'])
            aaa_button = st.checkbox('Ask AI Anything!', True, on_change=checkbox_clicked, args=['aaa_button'])

            st.divider()
            if show_data_button:
                with st.expander('Columns Names'):
                    st.markdown("Navigation: [Show Data](#show-data)", unsafe_allow_html=True)
                    st.subheader('Columns Names')
                    st.write(st.session_state.column_names)

            if eda_button:
                if len(st.session_state.eda_selection) != 0:
                    with st.expander('EDA: Suggested Steps'):
                        st.markdown("Navigation: [EDA](#exploratory-data-analysis)", unsafe_allow_html=True)
                        # st.button("Refresh EDA Suggestions", on_click=additional_clicked_fun, args=['eda_selection_clicked'])
                        st.write(st.session_state.eda_selection)


            if aaa_button:
                with st.expander('Prompt Inspiration'):
                    st.markdown("Navigation: [Ask AI Anything](#ask-ai-anything)", unsafe_allow_html=True)
                    aaa_chain = LLMChain(llm=llm, prompt=filled_aaa_prompt)
                    _dataframe_details = st.session_state.df_details
                    _eda_selection = st.session_state.eda_selection
                    aaa_samples = aaa_sample_generator(aaa_chain, _dataframe_details, _eda_selection)
                    st.write(aaa_samples)
            
    

        
