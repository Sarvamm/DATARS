import streamlit as st
@st.cache_data
def callOllama(prompt, model="gemma3"):
    #Call the Ollama API with the given prompt.
    response = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.get('message', {}).get('content', "No response.")

def stream_ollama(prompt, model="gemma3"):
    for chunk in ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    ):
        yield chunk["message"]["content"]

@st.cache_data
def plot_pairplot(df):
    pp = sns.pairplot(df, height=3)
    pp.savefig("outputs/pairplot.png")
    return "outputs/pairplot.png"

@st.cache_data
def analyze_data(context):
    prompt = f"""The following statistics were extracted from a data set, summarise this info in bullet points.
    Only reply in bullet points:
    {context}"""
    # response = callOllama(prompt, model="gemma3"
    # return response
    container = st.empty()
    response = ""
    for chunk in stream_ollama(prompt, model="gemma3"):
        response += chunk
        container.markdown(response)

@st.cache_data
def analyze_correlation(file_name, corr):
    prompt = f"""Summarize the observations from the correlation data in bullet points. First list columns
    with high correlation, then list columns with low correlation.
    Only reply in bullet points:
    File Name: {file_name}
    Correlation Data:
    {corr}"""
    response = callOllama(prompt, model="qwen2.5-coder:7b")
    return response
@st.cache_data
def question():
    prompt = f"""Based on the following info extracted from a data set, write intersting questions 
    a data analyst can plot, present your output only in the following format:
    ['Question1', 'Question2', 'Question3']
    also do not use apostropes in the output.
    eg: ['What is the average age of customers?', 'How many unique products are sold?']
    
    Data Name: {file_name}
    Columns: {columns} """
    response = callOllama(prompt, model="gemma3")
    return response

def get_context(uploaded_file, df):
    file_name = uploaded_file.name
    columns = df.columns.tolist()
    numerical_columns = df.select_dtypes(include=['number']).columns.tolist()
    categorical_columns = df.select_dtypes(exclude=['number']).columns.tolist()
    categorised_data = {'Numerical': numerical_columns, 'Categorical': categorical_columns}
    return f"""
    Dataset File Name: {file_name}

    Initial Preview (First 3 Rows of DataFrame):
    {df.head(3)}

    Columns of the DataFrame:
    {df.columns.tolist()}

    Columns categorised as Numerical and Categorical:
    {categorised_data}

    Statistical Summary of Numerical Columns:
    {df.describe()}

    Data Types for Each Column:
    {df.dtypes}

    Dimensions of the Dataset (Rows, Columns):
    {df.shape}

    Count of Missing (Null) Values in Each Column:
    {df.isnull().sum()}

    Count of Unique Values per Column:
    {df.nunique()}

    Frequency Distribution of Unique Values (Value Counts):
    {df.value_counts()}

    Total Number of Duplicate Rows in the DataFrame:
    {df.duplicated().sum()}
    """


if st.session_state.df is not None:
    df = st.session_state.df
    import ollama
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.express as px
    import plotly.express as px
    
if st.session_state.file is not None:
    uploaded_file = st.session_state.file 

    file_name = uploaded_file.name
    columns = df.columns.tolist()
    context = get_context(uploaded_file, df)


    st.write("### Data Preview")
    if st.checkbox('DataFrame preview:', value=True):
        st.write(df)
    

    st.subheader("Dataset Summary")
    st.write(analyze_data(context))

    try:
        corr = df.corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            corr, 
            annot=True, 
            fmt=".2f", 
            cmap="RdBu_r", 
            cbar_kws={"label": "Correlation"}, 
            ax=ax
        )
        ax.set_title("Heatmap of Numeric Values")
        left, right = st.columns(2)
        st.subheader("Correlation Matrix")
        left.pyplot(fig)
        right.write(analyze_correlation(file_name, corr))
    except Exception as e:
        pass

    try:    
        numeric_df = df.select_dtypes(include=['number'])  # Filter only numeric columns
        fig = px.box(
        numeric_df,
        points="all",  # Show all points (outliers)
        title="Boxplot of Numeric Values",
        )
        fig.update_layout(
            xaxis_title="Columns",
            yaxis_title="Values",
            xaxis_tickangle=90,  # Rotate x-axis labels for better readability
        )
        st.subheader("Outliers Detection")
        st.plotly_chart(fig)
    except Exception as e:
        pass

    try:    
        if len(df.select_dtypes(include=['number']).columns) < 7:
            image_path = plot_pairplot(df)
            st.image(image_path, caption="Pairplot")
    except Exception as e:
        pass
    
    if st.session_state.questions is None:
        from Functions import question
        st.session_state.questions = question()
    questions = eval(st.session_state.questions)

    for ques in questions:

        prompt = f'''
        Answer the following question using only code snippets.The dataset is called `df` and has the following columns:
        {", ".join(columns)}
        The code should be written in Python using plotly express and should be compatible with Streamlit.
        Reply only with the code and nothing else. Do not import anything. Do not write
        comments.Do not use streamlit headers or any text only do the plots..
        The data types of the columns are: {df.dtypes.to_dict()}

        The question is: 
        {ques}
        write the question using st.subheader() and then plot the graph using st.plotly_chart()
        '''

        code = callOllama(prompt, model="qwen2.5-coder:7b")

        try:
            exec(code[9:len(code)-3], globals())
        except Exception as e:
            pass
        
    

else:
    st.markdown(f'''
            ### 📂 Upload Your Dataset to Get Started

This app helps you explore and understand your data with AI-powered insights and visualizations.

#### ✅ Features:
- Automatic data summary (shape, types, missing values, etc.)
- AI-generated analysis and questions
- Correlation heatmaps & outlier detection
- Auto-created charts using Plotly Express

> **Supported file types**: ["csv", "xlsx", "xls", "json", "txt", "tsv", "parquet"]  
> Make sure your dataset has a header row.

⬆️ Upload your file to begin!
''')
    st.warning("Upload a file to get started.")
