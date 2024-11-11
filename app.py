import asyncio
import re
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.auth import exceptions
from st_aggrid import AgGrid, GridOptionsBuilder
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import generate_entities, search_contact_details  # Import function from utils.py
import uuid
import numpy as np
import os

st.set_page_config(layout="wide")


# Function to authenticate Google Sheets API
def authenticate_google_sheets(credentials_file='credentials.json'):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        return client
    except exceptions.GoogleAuthError:
        return None

# Function to load data from Google Sheets link and retain worksheet reference for later writing
def load_google_sheets_data(sheet_url):
    try:
        client = authenticate_google_sheets()
        if client:
            sheet = client.open_by_url(sheet_url)
            worksheet = sheet.get_worksheet(0)
            data = pd.DataFrame(worksheet.get_all_records())
            return data, worksheet  # Return data and worksheet for later use
        else:
            st.error("Failed to authenticate with Google Sheets. Please check your credentials.")
            return None, None
    except gspread.exceptions.APIError as e:
        st.error(f"Failed to access Google Sheets. Error: {e}")
        return None, None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None

# Function to load data from an Excel file
def load_excel_data(file):
    try:
        data = pd.read_excel(file)
        return data
    except Exception as e:
        st.error(f"An error occurred while reading the Excel file: {e}")
        return None

# Function to load data from a CSV file
def load_csv_data(file):
    try:
        data = pd.read_csv(file)
        return data
    except Exception as e:
        st.error(f"An error occurred while reading the CSV file: {e}")
        return None

# Synchronous wrapper for async function
def sync_search_contact_details(formatted_query, entities):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(search_contact_details(formatted_query, entities))
    finally:
        loop.close()


def write_to_google_sheets(data, worksheet):
    # Replace NaN with None or empty string before updating
    data = data.where(pd.notna(data), None)  # or use .fillna("") to replace with empty string
    
    # Convert the DataFrame to a list of lists and update the worksheet
    worksheet.update([data.columns.values.tolist()] + data.values.tolist())



def clean_query(query):
    # Use regex to find and remove any text within curly braces, including the braces themselves
    cleaned_query = re.sub(r"\{.*?\}", "", query)
    # Optionally strip extra whitespace
    return cleaned_query.strip()




def app():
    st.title('DataEX Data Loader')
    st.sidebar.header("Data Source Selection")
    file_type = st.sidebar.selectbox(
        'Select data source type:', 
        ['Upload Excel File', 'Upload CSV File', 'Google Sheets Link']
    )

    data = None
    worksheet = None  # To hold reference for Google Sheets
    load_data_section = True

    with st.sidebar.expander("Load Data"):
        if file_type == 'Upload Excel File':
            uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls'])
            if uploaded_file is not None:
                data = load_excel_data(uploaded_file)
                load_data_section = False

        elif file_type == 'Upload CSV File':
            uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
            if uploaded_file is not None:
                data = load_csv_data(uploaded_file)
                load_data_section = False

        elif file_type == 'Google Sheets Link':
            google_sheet_url = st.text_input("Enter the Google Sheets URL:")
            if google_sheet_url:
                data, worksheet = load_google_sheets_data(google_sheet_url)
                load_data_section = False

    # If data is loaded, show the full data preview and selected column preview
    if data is not None and not load_data_section:
        st.success("Data loaded successfully!")

        # Button to go back to data source selection
        if st.button("Back to Data Selection"):
            st.experimental_rerun()

        # Display the full dataset in a paginated grid view
        st.write("### Full Data Preview")
        gb = GridOptionsBuilder.from_dataframe(data)
        gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=20)
        gb.configure_default_column(editable=False, resizable=True, filter=True, sortable=True)
        full_data_grid_options = gb.build()
        AgGrid(data, gridOptions=full_data_grid_options, height=400, width="100%")

        # Display a selection for columns and preview the selected column
        st.write("### Select Column and Enter Query")
        columns = data.columns.tolist()
        selected_column = st.selectbox("Select a column to display:", columns)

        if selected_column:
            st.write(f"### Data for column: {selected_column}")
            
            # Create a DataFrame with only the selected column for preview
            column_data_df = data[[selected_column]].dropna()  # Drop NaN values

            # Set up AgGrid for previewing the selected column data
            gb = GridOptionsBuilder.from_dataframe(column_data_df)
            gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=20)
            gb.configure_default_column(editable=False, resizable=True, filter=True, sortable=True)
            selected_column_grid_options = gb.build()
            AgGrid(column_data_df, gridOptions=selected_column_grid_options, height=400, width="100%")

            # Allow user to enter query and select number of rows to process
            user_query = st.text_input("Enter the query (e.g., 'contact details of {company_name}')") 
            num_rows = st.number_input("Select number of rows to process (1-25):", min_value=1, max_value=25, value=10)

            # Execute only when the user clicks Submit
            if st.button("Submit"):
                # Regular expression to check if the query contains any placeholder in the format {some_value}
                if not re.search(r'\{.*\}', user_query):
                    st.error("Please enter a valid query with a placeholder in the format '{some_value}'. For example: 'contact details of {company_name}'.")
                
                else:
                    
                    cleaned_user_query = clean_query(user_query)
                    
                    query_resultant = generate_entities(cleaned_user_query)
                    question_status = query_resultant["question_status"]
                    entities = query_resultant["entities"]
                    
                    print(query_resultant)
                    
                    if question_status is not True:
                        st.error("Please enter a valid query with extraction entities in it. For example: 'Give me the email, phone of {company_name}'.")     
                        
                    selected_rows = column_data_df[selected_column].head(num_rows).tolist()  # Select top 'num_rows' values
                    results = []
                    failed_requests = []

                    # Initialize new columns for Process and Status
                    data['Process'] = None
                    data['Status'] = None

                    # Execute Tavily API queries concurrently
                    with ThreadPoolExecutor(max_workers=num_rows) as executor:
                        futures = {}
                        for row_index, row in enumerate(selected_rows):
                            row_value = str(row)  # Convert row to string if necessary
                            
                            placeholders = re.findall(r'\{([^}]+)\}', user_query)
                            formatted_query = user_query
                            for placeholder in placeholders:
                                formatted_query = formatted_query.replace(f"{{{placeholder}}}", str(row_value))                
                
                            futures[executor.submit(sync_search_contact_details, formatted_query, entities)] = row_index

                        # Handle the results after all futures are completed
                        for future in as_completed(futures):
                            row_index = futures[future]
                            try:
                                web_result, extracted_data = future.result()
                                
                                print(extracted_data)

                                if isinstance(web_result, str):
                                    web_result = str(web_result)  # Convert the result to a string if it's a dictionary
                                    for key, value in extracted_data.items():
                                        data.at[row_index, key] = value

                                data.at[row_index, 'Process'] = 'Success'
                                data.at[row_index, 'Status'] = web_result
                            except Exception as e:
                                data.at[row_index, 'Process'] = 'Failed'
                                data.at[row_index, 'Status'] = str(e)

                    # Display the results from the API in AgGrid
                    st.write("### Tavily API Results")
                    results_df = data
                    
                    gb = GridOptionsBuilder.from_dataframe(results_df)
                    gb.configure_pagination(enabled=True, paginationAutoPageSize=True, paginationPageSize=10)
                    gb.configure_default_column(editable=False, resizable=True, filter=True, sortable=True)
                    results_grid_options = gb.build()
                    AgGrid(results_df, gridOptions=results_grid_options, height=400, width="100%")

                    if worksheet:
                        write_to_google_sheets(data, worksheet)  # Write back to Google Sheets
                        st.success("Data written back to Google Sheets successfully.")

                    # Save the updated data to a new file
                    random_string = str(uuid.uuid4())[:8]
                    new_folder = "processed_files"
                    if not os.path.exists(new_folder):
                        os.makedirs(new_folder)

                    new_filename = f"{new_folder}/processed_{random_string}.csv"
                    data.to_csv(new_filename, index=False)

                    st.success(f"Processed file saved to: {new_filename}")

if __name__ == "__main__":
    app()
