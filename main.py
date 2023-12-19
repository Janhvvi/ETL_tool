import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import mysql.connector
import pandas as pd
from sqlalchemy import create_engine
import re
from tkinter import filedialog
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import requests


global_connection = None
selected_table = None
selected_columns = None
cursor = None

def create_new_button(event, original_button, initial_positions):

    # Get the button's current position relative to the root window
    current_x = event.widget.winfo_rootx()
    current_y = event.widget.winfo_rooty()

    # Get the canvas's bounding box relative to the root window
    canvas_x = canvas.winfo_rootx()
    canvas_y = canvas.winfo_rooty()
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    # Check if the button is dropped inside the canvas
    if canvas_x <= current_x <= canvas_x + canvas_width and canvas_y <= current_y <= canvas_y + canvas_height:
        # If dropped inside the canvas, create a new button at the same position on the canvas
        new_button = tk.Button(canvas, text= event.widget.cget("text"))
        new_button.place(x=current_x - canvas_x, y=current_y - canvas_y)
        new_button.bind("<ButtonPress-1>", on_button_press)
        new_button.bind("<B1-Motion>", on_button_motion)
        new_button.bind("<ButtonRelease-1>", lambda event, button=new_button: create_new_button(event, button, initial_positions))
        

    # Check if the button is dropped inside the canvas
    if canvas_x <= current_x <= canvas_x + canvas_width and canvas_y <= current_y <= canvas_y + canvas_height:
        if event.widget.cget("text") == "MYSQL":
            # If dropped inside the canvas and the button is "MYSQL", create a new form
            form_window = tk.Toplevel(root)
            form_window.title("MySQL Configuration") 
            form_window.geometry("300x250+920+130")
            
            # Create labels and entry fields for username, password, hostname, and database name
            username_label = tk.Label(form_window, text="Username:")
            username_label.pack()
            username_entry = tk.Entry(form_window)
            username_entry.pack()

            password_label = tk.Label(form_window, text="Password:")
            password_label.pack()
            password_entry = tk.Entry(form_window, show="*")
            password_entry.pack()

            hostname_label = tk.Label(form_window, text="Hostname:")
            hostname_label.pack()
            hostname_entry = tk.Entry(form_window)
            hostname_entry.pack()

            db_name_label = tk.Label(form_window, text="Database Name:")
            db_name_label.pack()
            db_name_entry = tk.Entry(form_window)
            db_name_entry.pack()
            

            def submit_form():
                # Callback function for the "Submit" button in the form
                username = username_entry.get()
                password = password_entry.get()
                hostname = hostname_entry.get()
                db_name = db_name_entry.get()

                global global_connection
                global cursor
                # Call the establish_mysql_connection() function with the provided credentials
                global_connection = SQLconnection(username, password, hostname, db_name)

                if global_connection:
                    # Fetch table names from the database
                    cursor = global_connection.cursor()
                    cursor.execute("SHOW TABLES")
                    tables = [table[0] for table in cursor.fetchall()]
                    cursor.close()

                    # Function to display the data of the selected table in a new window
                    def display_table_data():
                        global selected_table
                        selected_table = table_var.get()
                        if selected_table:
                            cursor = global_connection.cursor()

                            # Fetch column names for the selected table
                            cursor.execute(f"DESCRIBE {selected_table}")
                            columns = [column[0] for column in cursor.fetchall()]

                            # Create a window to display column names as check buttons
                            columns_window = tk.Toplevel(root)
                            columns_window.title(f"Select Columns from {selected_table}")
                            columns_window.geometry("+750+100")  # You can adjust the position if needed

                            column_vars = {}
                            for column in columns:
                                var = tk.IntVar()
                                column_vars[column] = var
                                tk.Checkbutton(columns_window, text=column, variable=var).pack(anchor=tk.W)

                            # Add a submit button to fetch and display data from the selected columns
                            def show_selected_columns():
                                global selected_columns
                                selected_columns = [col for col, var in column_vars.items() if var.get()]

                                if selected_columns:
                                    cursor.execute(f"SELECT {','.join(selected_columns)} FROM {selected_table}")
                                    table_data = cursor.fetchall()

                                    # Clear the textArea
                                    textArea.delete(1.0, tk.END)

                                    # Display column headers
                                    headers = ' | '.join(selected_columns)
                                    textArea.insert(tk.END, headers + '\n')
                                    textArea.insert(tk.END, "-" * len(headers) + '\n')  # Underline headers with dashes for clarity

                                    # Display data for each row below headers
                                    for row in table_data:
                                        row_data = ' | '.join([str(value) for value in row])  # Convert values to string before joining
                                        textArea.insert(tk.END, f"{row_data}\n")

                                else:
                                    textArea.delete(1.0, tk.END)
                                    textArea.insert(tk.END, "No columns selected.")



                            tk.Button(columns_window, text="Show Data", command=show_selected_columns).pack(pady=10)

                        else:
                           messagebox.showinfo("Info", "Please select a table first.")


                    # Create and display checkbuttons for each table in a new window
                    tables_window = tk.Toplevel(root)
                    tables_window.title("Select a Table")
                    tables_window.geometry("+700+100")


                    table_var = tk.StringVar()
                    for table in tables:
                        tk.Radiobutton(tables_window, text=table, variable=table_var, value=table).pack(anchor=tk.W)

                    tk.Button(tables_window, text="Submit", command=display_table_data).pack(pady=10)
                else:
                    messagebox.showerror("Error", "Invalid credentials. MySQL connection failed.")
                

            submit_button = tk.Button(form_window, text="Submit", command=submit_form)
            submit_button.pack()
            
        elif event.widget.cget("text") == "CSV":
            # Create a new form for CSV configuration
            form_window = tk.Toplevel(root)
            form_window.title("CSV Configuration")
            form_window.geometry("300x250+920+130")
          
        
            def submit_csv_form():
                # Use a file dialog to get the CSV file path
                filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])

                if not filepath:  # If the user cancels the file dialog
                    return

                global global_connection
                global_connection = CSVConnection(filepath)
               
                try:
                    # Read the CSV file using pandas
                    df = pd.read_csv(filepath)
        
                    # Function to display the data of the selected columns in the textArea
                    def show_selected_columns():
                        global selected_columns
                        selected_columns = [col for col, var in column_vars.items() if var.get()]
        
                        if selected_columns:
                            # Clear the textArea
                            textArea.delete(1.0, tk.END)
        
                            # Display column headers
                            headers = ' | '.join(selected_columns)
                            textArea.insert(tk.END, headers + '\n')
                            textArea.insert(tk.END, "-" * len(headers) + '\n')  # Underline headers with dashes for clarity
        
                            # Display data for each row below headers
                            for _, row in df[selected_columns].head(30).iterrows():
                                row_data = ' | '.join([str(value) for value in row])  # Convert values to string before joining
                                textArea.insert(tk.END, f"{row_data}\n")
        
                        else:
                            textArea.delete(1.0, tk.END)
                            textArea.insert(tk.END, "No columns selected.")
        
                    # Create and display checkbuttons for each column in a new window
                    columns_window = tk.Toplevel(root)
                    columns_window.title(f"Select Columns from CSV")
                    columns_window.geometry("+750+100")  # You can adjust the position if needed
        
                    column_vars = {}
                    for column in df.columns:
                        var = tk.IntVar()
                        column_vars[column] = var
                        tk.Checkbutton(columns_window, text=column, variable=var).pack(anchor=tk.W)
        
                    tk.Button(columns_window, text="Show Data", command=show_selected_columns).pack(pady=10)
        
                except Exception as e:
                    messagebox.showerror("Error", f"Error occurred while reading the CSV: {str(e)}")
        
            upload_button = tk.Button(form_window, text="Upload CSV File", command=submit_csv_form)
            upload_button.pack(pady=10)

        elif event.widget.cget("text") == "Excel":
            # Create a new form for Excel configuration
            form_window = tk.Toplevel(root)
            form_window.title("Excel Configuration")
            form_window.geometry("300x250+920+130")

            def submit_excel_form():
                # Use a file dialog to get the Excel file path
                filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls;*.xlsx"), ("All files", "*.*")])

                if not filepath:  # If the user cancels the file dialog
                    return

                global global_connection
                global_connection = CSVConnection(filepath)  # Assuming CSVConnection can handle Excel paths as well
                try:
                    # Read the Excel file using pandas
                    df = pd.read_excel(filepath)

                    # Function to display the data of the selected columns in the textArea
                    def show_selected_columns():
                        global selected_columns
                        selected_columns = [col for col, var in column_vars.items() if var.get()]

                        if selected_columns:
                            # Clear the textArea
                            textArea.delete(1.0, tk.END)

                            # Display column headers
                            headers = ' | '.join(selected_columns)
                            textArea.insert(tk.END, headers + '\n')
                            textArea.insert(tk.END, "-" * len(headers) + '\n')  # Underline headers with dashes for clarity

                            # Display data for each row below headers
                            for _, row in df[selected_columns].head(30).iterrows():
                                row_data = ' | '.join([str(value) for value in row])  # Convert values to string before joining
                                textArea.insert(tk.END, f"{row_data}\n")

                        else:
                            textArea.delete(1.0, tk.END)
                            textArea.insert(tk.END, "No columns selected.")

                    # Create and display checkbuttons for each column in a new window
                    columns_window = tk.Toplevel(root)
                    columns_window.title(f"Select Columns from Excel")
                    columns_window.geometry("+750+100")  # You can adjust the position if needed

                    column_vars = {}
                    for column in df.columns:
                        var = tk.IntVar()
                        column_vars[column] = var
                        tk.Checkbutton(columns_window, text=column, variable=var).pack(anchor=tk.W)

                    tk.Button(columns_window, text="Show Data", command=show_selected_columns).pack(pady=10)
                except Exception as e:
                    messagebox.showerror("Error", f"Error occurred while reading the Excel file: {str(e)}")

            upload_button = tk.Button(form_window, text="Upload Excel File", command=submit_excel_form)
            upload_button.pack(pady=10)

        elif event.widget.cget("text") == "Amazon AWS":
            # If dropped inside the canvas and the button is "MYSQL", create a new form
            form_window = tk.Toplevel(root)
            form_window.title("Amazon AWS Configuration")
            form_window.geometry("300x250+920+130")
            
            # Create labels and entry fields for username, password, hostname, and database name
            username_label = tk.Label(form_window, text="Username:")
            username_label.pack()
            username_entry = tk.Entry(form_window)
            username_entry.pack()

            password_label = tk.Label(form_window, text="Password:")
            password_label.pack()
            password_entry = tk.Entry(form_window, show="*")
            password_entry.pack()

            hostname_label = tk.Label(form_window, text="Hostname:")
            hostname_label.pack()
            hostname_entry = tk.Entry(form_window)
            hostname_entry.pack()

            db_name_label = tk.Label(form_window, text="Database Name:")
            db_name_label.pack()
            db_name_entry = tk.Entry(form_window)
            db_name_entry.pack()
            

            def submit_form():
                # Callback function for the "Submit" button in the form
                username = username_entry.get()
                password = password_entry.get()
                hostname = hostname_entry.get()
                db_name = db_name_entry.get()

                global global_connection
                # Call the establish_mysql_connection() function with the provided credentials
                global_connection = SQLconnection(username, password, hostname, db_name)

                if global_connection:
                    # Fetch table names from the database
                    cursor = global_connection.cursor()
                    cursor.execute("SHOW TABLES")
                    tables = [table[0] for table in cursor.fetchall()]
                    cursor.close()

                    # Function to display the data of the selected table in a new window
                    def display_table_data():
                        global selected_table
                        selected_table = table_var.get()
                        if selected_table:
                            cursor = global_connection.cursor()

                            # Fetch column names for the selected table
                            cursor.execute(f"DESCRIBE {selected_table}")
                            columns = [column[0] for column in cursor.fetchall()]

                            # Create a window to display column names as check buttons
                            columns_window = tk.Toplevel(root)
                            columns_window.title(f"Select Columns from {selected_table}")
                            columns_window.geometry("+750+100")  # You can adjust the position if needed

                            column_vars = {}
                            for column in columns:
                                var = tk.IntVar()
                                column_vars[column] = var
                                tk.Checkbutton(columns_window, text=column, variable=var).pack(anchor=tk.W)

                            # Add a submit button to fetch and display data from the selected columns
                            def show_selected_columns():
                                global selected_columns
                                selected_columns = [col for col, var in column_vars.items() if var.get()]

                                if selected_columns:
                                    cursor.execute(f"SELECT {','.join(selected_columns)} FROM {selected_table}")
                                    table_data = cursor.fetchall()

                                    # Clear the textArea
                                    textArea.delete(1.0, tk.END)

                                    # Display column headers
                                    headers = ' | '.join(selected_columns)
                                    textArea.insert(tk.END, headers + '\n')
                                    textArea.insert(tk.END, "-" * len(headers) + '\n')  # Underline headers with dashes for clarity

                                    # Display data for each row below headers
                                    for row in table_data:
                                        row_data = ' | '.join([str(value) for value in row])  # Convert values to string before joining
                                        textArea.insert(tk.END, f"{row_data}\n")

                                else:
                                    textArea.delete(1.0, tk.END)
                                    textArea.insert(tk.END, "No columns selected.")



                            tk.Button(columns_window, text="Show Data", command=show_selected_columns).pack(pady=10)

                        else:
                           messagebox.showinfo("Info", "Please select a table first.")


                    # Create and display checkbuttons for each table in a new window
                    tables_window = tk.Toplevel(root)
                    tables_window.title("Select a Table")
                    tables_window.geometry("+700+100")


                    table_var = tk.StringVar()
                    for table in tables:
                        tk.Radiobutton(tables_window, text=table, variable=table_var, value=table).pack(anchor=tk.W)

                    tk.Button(tables_window, text="Submit", command=display_table_data).pack(pady=10)
                else:
                    messagebox.showerror("Error", "Invalid credentials. MySQL connection failed.")
                

            submit_button = tk.Button(form_window, text="Submit", command=submit_form)
            submit_button.pack()

        elif event.widget.cget("text") == "Remove Duplication":
            remove_duplicates_and_save()
                        
            # Create a new button on the canvas to show cleaned data
            show_data_button = tk.Button(canvas, text="Show Data wo Duplicate Values!",bg="cyan", command=show_cleaned_data_in_mysql)
            show_data_button.place(x=150, y=380)  # Adjust position if needed
        
        elif event.widget.cget("text") == "Remove Null Rows":
            remove_null_rows()
            # Create a new button on the canvas to show cleaned data
            show_data_button = tk.Button(canvas, text="  Show Data without Null Rows! ",bg="cyan", command=show_cleaned_data_in_mysql)
            show_data_button.place(x=150, y=380)
        
        elif event.widget.cget("text") == "Remove Null Columns":
            remove_null_columns()
            # Create a new button on the canvas to show cleaned data
            show_data_button = tk.Button(canvas, text="Show Data without Null columns!",bg="cyan", command=show_cleaned_data_in_mysql)
            show_data_button.place(x=150, y=380)
            
        elif event.widget.cget("text") == "Replace null w blanks":
            replace_null_with_blanks()
            # Create a new button on the canvas to show cleaned data
            show_data_button = tk.Button(canvas, text="  Show Data after Replacing !  ",bg="cyan", command=show_cleaned_data_in_mysql)
            show_data_button.place(x=150, y=380)
            
        elif event.widget.cget("text") == "Replace null by type":
            replace_null_with_appropriate_type()
            # Create a new button on the canvas to show cleaned data
            show_data_button = tk.Button(canvas, text="    Show Data after Replacing !  ",bg="cyan", command=show_cleaned_data_in_mysql)
            show_data_button.place(x=150, y=380)
            
        elif event.widget.cget("text") == "Proper Type casting":
            type_casting(correct_email)
            
            # Create a new button on the canvas to show cleaned data
            show_data_button = tk.Button(canvas, text=" Show Data after Type Casting !  ",bg="cyan", command=show_cleaned_data_in_mysql)
            show_data_button.place(x=150, y=380)
            
        elif event.widget.cget("text") == "Time-zone Enrich.":
            time_zone_enrichment()
            # Create a new button on the canvas to show cleaned data
            show_data_button = tk.Button(canvas, text=" Time Zone Enriched data!  ",bg="cyan", command=show_cleaned_data_in_mysql)
            show_data_button.place(x=150, y=380)
        
        elif event.widget.cget("text") == "Geo-spatial Enrich.":
            geospatial_enrichment()
            show_data_button = tk.Button(canvas, text="Enriched data! ",bg="cyan",command= show_cleaned_data_in_mysql)
            show_data_button.place(x=150,y= 380)
        
        elif event.widget.cget("text") == "Link Enrich.":
            link_enrichment()
            show_data_button = tk.Button(canvas, text="Enriched data! ",bg="cyan",command= show_cleaned_data_in_mysql)
            show_data_button.place(x=150,y= 380)
        else:            
            # If dropped inside the canvas, create a new button at the same position on the canvas
            new_button = tk.Button(canvas, text=event.widget.cget("text"))
            new_button.place(x=current_x - canvas_x, y=current_y - canvas_y)
            new_button.bind("<ButtonPress-1>", on_button_press)
            new_button.bind("<B1-Motion>", on_button_motion)
            new_button.bind("<ButtonRelease-1>", lambda event, button=new_button: create_new_button(event, button, initial_positions))
    
    else:
        original_button.place(x=initial_positions[original_button]["x"], y=initial_positions[original_button]["y"])
            #original_button.data = None
      
def remove_duplicates_and_save():
    data = source()
    
    cleaned_data = data.drop_duplicates(subset=selected_columns)
    data = cleaned_data
    textArea.insert(END, f"\n Duplicate rows removed! \n")
    
    destination(data)
    
def remove_null_rows():
    data = source()
    
    cleaned_data = data.dropna(how='all',subset=selected_columns)
    data = cleaned_data
    textArea.insert(END, f"\n Null rows removed! \n")
    
    destination(data)
            
def remove_null_columns():
    data = source()
    
    #cleaned_data = data[selected_columns]
    #cleaned_data = cleaned_data.dropna(axis=1,how='all')
    null_columns = data[selected_columns].columns[data[selected_columns].isnull().all()].tolist()
    
    data = data.drop(columns=null_columns)
    textArea.insert(END, f"\n Null columns removed! \n")
    
    destination(data)

def replace_null_with_blanks():
    data = source()
    
    data[selected_columns] = data[selected_columns].fillna('')
    textArea.insert(END, f"\n Null values replaced with blanks! \n")
   
    destination(data)

def replace_null_with_appropriate_type():
    data = source()
    
    for col in data.columns:
        # Check data type of each column
        if data[col].dtype == 'object':  # For text columns
            data[col].fillna('No Value', inplace=True)
        elif data[col].dtype in ['int64', 'float64']:  # For numeric columns
            median_value = data[col].median()
            data[col].fillna(median_value, inplace=True)
        elif data[col].dtype == 'datetime64[ns]':  # For datetime columns
            data[col].fillna(method='ffill', inplace=True)    
    textArea.insert(END, f"\n Null values replaced with it's appropriate datatype! \n")
    
    destination(data)


def correct_email(email):
    engine = global_connection
    if engine is None:
        textArea.insert(END, "Error: Unable to establish a connection to the database!\n")
        return None
    
    if not email:
        return 'unknown@domain.com'
    else:
    # Removing any extra spaces
        email = email.strip()
    
    # If no '@', assume missing and append '@domain.com'
    if '@' not in email:
        email += '@domain.com'
    elif email.count('@') > 1:
        # Multiple '@' signs, remove all extra
        parts = email.split('@')
        email = parts[0] + '@' + parts[-1]
        
    # If no TLD, assume '.com'
    if '.' not in email.split('@')[-1]:
        email += '.com'
        
    return email

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}"

def is_email(value):
    """Check if a value is an email based on regex."""
    if not isinstance(value, str):
        return False
    return re.match(EMAIL_REGEX, value)

def column_is_email(column_data, sample_size=100):
    """Determine if a column is mostly emails by sampling."""
    sample = column_data.sample(sample_size, replace=True) if len(column_data) > sample_size else column_data
    email_count = sum(sample.apply(is_email))
    return email_count / len(sample) > 0.9  # More than 90% look like emails

def type_casting(correct_email):
    data = source()
    
    for column in data.columns:
        # Check if column content is numeric and not an integer
        if pd.api.types.is_numeric_dtype(data[column]) and not pd.api.types.is_integer_dtype(data[column]):
            data[column] = data[column].astype("Int64")

        # Check if column content seems to be string-like (object type in pandas)
        #elif pd.api.types.is_object_dtype(data[column]):
        #    first_val = data[column].iloc[0]

        # Check if column content seems to be string-like (object type in pandas)
        elif pd.api.types.is_object_dtype(data[column]):
            if column_is_email(data[column]):
                data[column] = data[column].apply(correct_email)
            else:
                data[column] = data[column].astype(str)
    
    textArea.insert(END, f"\n Data type casting successful!\n")
    
    destination()

def save_dataframe_to_mysql(cleaned_data, engine, table_name):
    """
    Save a DataFrame to a MySQL database using the given connection.
    """
    try:
        cleaned_data.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
    except Exception as e:
        print("Error while saving DataFrame to MySQL:", str(e))
        messagebox.showerror("Error", f"Error saving data to MySQL: {str(e)}")
    
def time_zone_enrichment():
    data = source()
    
    # Check if 'Latitude' and 'Longitude' are among the columns selected.
    if 'latitude' not in selected_columns or 'longitude' not in selected_columns:
        textArea.insert(END, "\nError: Latitude and/or Longitude columns not found in the selected columns!\n")
        return
    
    obj = TimezoneFinder()
    # Enrich data with timezones
    def get_timezone(row):
        
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            return None
        
        return obj.timezone_at(lat=row['latitude'], lng=row['longitude'])

    data['timezone_1'] = data.apply(get_timezone, axis=1)
    textArea.insert(END, f"\n Time Zone Added! \n")
    
    destination(data)

def geospatial_enrichment():
    data = source()
        
    top_20_data = data.iloc[:20].copy()
    geolocator = Nominatim(user_agent="app",timeout=1)
    global function_call_count

    function_call_count = 0
    def get_geospatial_info(row):
        global function_call_count
        address_str = f"{row['city']}, {row['state']}, {row['country']}, {row['zip_code']}"
        function_call_count += 1
        if pd.isna(address_str):
            return pd.Series([None, None])

        try:
            location = geolocator.geocode(address_str, exactly_one=True)
            #time.sleep(1)
            print(f'Checked  {function_call_count}')

        except Exception as e:
            textArea.insert(END, f"Error while geocoding: {e}")
            return pd.Series([None, None])
        
        if location:
            return pd.Series([location.latitude, location.longitude,location.address])
        else:
            return pd.Series([None, None])

    top_20_data[['new_latitude', 'new_longitude','new_address']] = top_20_data.apply(get_geospatial_info, axis=1)
    textArea.insert(END, f"\n Geospatial Location Added! \n")

    data = pd.concat([top_20_data, data.iloc[20:]], axis=0)
    destination(data)

def link_enrichment():
    data = source()
    
    top_20_data = data.iloc[:20].copy()

    global function_call_count
    function_call_count = 0

    def check_link_status(row):
        global function_call_count
        url = row['url'] 
        function_call_count += 1
        print(f'Checked {function_call_count}')

        try:
            response = requests.head(url)
            if response.status_code == 200:
                return "Active"
            else:
                return "Inactive"
        except Exception as e:
            textArea.insert(END, f"Error while checking URL {url}: {e}")
            return "Error"
        

    top_20_data['url_status'] = top_20_data.apply(check_link_status, axis=1)
    textArea.insert(END, f"\n URL Status Added! \n")

    data = pd.concat([top_20_data, data.iloc[20:]], axis=0)
    destination(data)

def source():
    if global_connection is None:
        textArea.insert(END, "Error: No active database connection!\n")
        return None

    try:
        if isinstance(global_connection, CSVConnection):
            if global_connection.filepath.endswith('.csv'):
                data = pd.read_csv(global_connection.filepath)
            elif global_connection.filepath.endswith(('.xls', '.xlsx')):
                data = pd.read_excel(global_connection.filepath)
            else:
                textArea.insert(END, "Error: Unsupported file type!\n")
                return None
        else:
            data = pd.read_sql(f"SELECT * FROM {selected_table}", global_connection)
        return data
    except FileNotFoundError:
        textArea.insert(END, "Error: Data file not found!\n")
        return None

def destination(data):
    if data is not None:
        engine = establish_mysql_engine('root', 'root', 'localhost', 'testing')
        if engine:
            save_dataframe_to_mysql(data, engine, table_name="emp")
        else:
            messagebox.showerror("Error", "Failed to establish a connection to MySQL.")
            
def SQLconnection(username, password, host, db_name):
    # Function to establish the MySQL connection with the provided credentials
    try:
        connection = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=db_name
        )
        
        if connection.is_connected():
            return connection
        else:
            messagebox.showerror("Error", "MySQL connection failed.")
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error occurred: {str(e)}")
        
class CSVConnection:
    def __init__(self, filepath):
        self.filepath = filepath

def establish_mysql_engine(username, password, host, db_name):
    """Function to create and return a SQLAlchemy engine for MySQL."""
    try:
        # Create an engine using the provided credentials and database details
        engine_url = f"mysql+mysqlconnector://{username}:{password}@{host}/{db_name}"
        engine = create_engine(engine_url)
        return engine
    except Exception as e:
        messagebox.showerror("Error", f"Error creating engine: {str(e)}")
        return None

# Initialize the initial_positions dictionary before calling create_new_buttons function
initial_positions = {}

def create_new_buttons(button_num):
    for widget in left_frame.winfo_children():
        widget.destroy()
        initial_positions.clear()

    if button_num == 1:
        new_button1 = tk.Button(left_frame, text="MYSQL", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button1.place(x=0,y=10)
        widgetText1 = "MYSQL"

        new_button2 = tk.Button(left_frame, text="CSV", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button2.place(x=0,y=70)
        widgetText2 = "CSV"

        new_button3 = tk.Button(left_frame, text="Amazon AWS", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button3.place(x=0,y=140)
        widgetText3 = "Amazon AWS"
        
        new_button4 = tk.Button(left_frame, text="Excel", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button4.place(x=0,y=210)
        widgetText4 = "Excel"
        
        initial_positions.update({
            new_button1: {"x": 0, "y": 10, "text": widgetText1},
            new_button2: {"x": 0, "y": 70, "text": widgetText2},
            new_button3: {"x": 0, "y": 140, "text": widgetText3},
            new_button4: {"x": 0, "y": 210, "text": widgetText4},
        })
    elif button_num == 2:
        new_button1 = tk.Button(left_frame, text="Remove Duplication", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button1.place(x=0,y=10)
        widgetText1 = "Remove Duplication"

        new_button2 = tk.Button(left_frame, text="Remove Null Rows", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button2.place(x=0,y=70)
        widgetText2 = "Remove Null Rows"

        new_button3 = tk.Button(left_frame, text="Remove Null Columns", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button3.place(x=0,y=140)
        widgetText3 = "Remove Null Columns"
        
        new_button4 = tk.Button(left_frame, text="Replace null w blanks", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button4.place(x=0,y=210)
        widgetText4 = "Replace Null with Blanks(String)"
        
        new_button5 = tk.Button(left_frame, text="Replace null by type", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button5.place(x=0,y=280)
        widgetText5 = "Replace null by type"
        
        new_button6 = tk.Button(left_frame, text="Proper Type casting", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button6.place(x=0,y=350)
        widgetText6 = "Proper Type casting"
        initial_positions.update({
            new_button1: {"x": 0, "y": 10, "text":  widgetText1},
            new_button2: {"x": 0, "y": 70, "text":  widgetText2},
            new_button3: {"x": 0, "y": 140, "text": widgetText3},
            new_button4: {"x": 0, "y": 210, "text": widgetText4},
            new_button5: {"x": 0, "y": 280, "text": widgetText5},
            new_button6: {"x": 0, "y": 350, "text": widgetText6},
        })
    elif button_num == 3:
        new_button1 = tk.Button(left_frame, text="Time-zone Enrich.", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button1.place(x=0,y=10)
        widgetText1 = "Time-zone Enrich."

        new_button2 = tk.Button(left_frame, text="Semantic Enrich.", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button2.place(x=0,y=70)
        widgetText2 = "Semantic Enrich."

        new_button3 = tk.Button(left_frame, text="Geo-spatial Enrich.", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button3.place(x=0,y=140)
        widgetText3 = "Geo-spatial Enrich."
        
        new_button4 = tk.Button(left_frame, text="Link Enrich.", width=20, relief='solid',
                                activeforeground='white', activebackground='dark blue', bd=2,
                                bg='dark blue', fg='white', font=("Consolas", 12, "bold"))
        new_button4.place(x=0,y=210)
        widgetText4 = "Link Enrich."
        initial_positions.update({
            new_button1: {"x": 0, "y": 10, "text": widgetText1},
            new_button2: {"x": 0, "y": 70, "text": widgetText2},
            new_button3: {"x": 0, "y": 140, "text": widgetText3},
            new_button4: {"x": 0, "y": 210, "text": widgetText4},
        })

    new_button1.bind("<ButtonPress-1>", on_button_press)
    new_button1.bind("<B1-Motion>", on_button_motion)
    new_button1.bind("<ButtonRelease-1>", lambda event, button=new_button1: create_new_button(event, button, initial_positions))

    new_button2.bind("<ButtonPress-1>", on_button_press)
    new_button2.bind("<B1-Motion>", on_button_motion)
    new_button2.bind("<ButtonRelease-1>", lambda event, button=new_button2: create_new_button(event, button, initial_positions))

    new_button3.bind("<ButtonPress-1>", on_button_press)
    new_button3.bind("<B1-Motion>", on_button_motion)
    new_button3.bind("<ButtonRelease-1>", lambda event, button=new_button3: create_new_button(event, button, initial_positions))
    
    new_button4.bind("<ButtonPress-1>", on_button_press)
    new_button4.bind("<B1-Motion>", on_button_motion)
    new_button4.bind("<ButtonRelease-1>", lambda event, button=new_button4: create_new_button(event, button, initial_positions))

    new_button5.bind("<ButtonPress-1>", on_button_press)
    new_button5.bind("<B1-Motion>", on_button_motion)
    new_button5.bind("<ButtonRelease-1>", lambda event, button=new_button5: create_new_button(event, button, initial_positions))

    new_button6.bind("<ButtonPress-1>", on_button_press)
    new_button6.bind("<B1-Motion>", on_button_motion)
    new_button6.bind("<ButtonRelease-1>", lambda event, button=new_button6: create_new_button(event, button, initial_positions))

    
    
def show_cleaned_data_in_mysql():
    username = 'root'
    password = 'root'
    host = 'localhost'
    db_name = 'testing'

    connection = SQLconnection(username, password, host, db_name)
    if connection:
        query = "SELECT * FROM emp"
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()

        # Get column names
        cursor.execute("DESCRIBE emp")
        columns = [column[0] for column in cursor.fetchall()]
        
        # Create a new window to display the data
        data_window = tk.Toplevel(root)
        data_window.title("Cleaned Data from MySQL")
        data_text_area = Text(data_window, wrap=tk.WORD, width=180, height=45)
        data_text_area.pack(padx=10, pady=10)

        # Display column headers similar to show_selected_columns function
        headers = ' | '.join(columns)
        data_text_area.insert(tk.END, headers + '\n')
        data_text_area.insert(tk.END, "-" * len(headers) + '\n')  # Underline headers with dashes for clarity

        # Insert data into the text area
        for row in result:
            row_data = ' | '.join([str(value) for value in row])  # Convert values to string before joining
            data_text_area.insert(tk.END, f"{row_data}\n")

        cursor.close()
        connection.close()
    else:
        messagebox.showerror("Error", "Failed to connect to MySQL.")

def button_click(button_num):
     print(f"Button {button_num} clicked.")
     create_new_buttons(button_num)


root = tk.Tk()
root.title("Button and Canvas Example")
root.geometry("1200x800")
root.configure(background='sky blue')

# Create a frame for the top buttons
top_buttons_frame = tk.Frame(root, bg='white', width=500, height=40)
top_buttons_frame.pack(pady=10)

image1 = tk.PhotoImage(file = "C:/images/source.png")
image2 = tk.PhotoImage(file = "C:/images/cleaning.png")
image3 = tk.PhotoImage(file = "C:/images/sink.png")
image4 = tk.PhotoImage(file="C:/images/inc1.png") 

# Create three buttons at the top (arranged horizontally)
button1 = tk.Button(top_buttons_frame, text="Data Source", command=lambda: button_click(1),
                    image=image1, bg='#ffffff', activebackground='#ffffff', bd=0)
button2 = tk.Button(top_buttons_frame, text="Data Cleaning", command=lambda: button_click(2),
                    image=image2, bg='#ffffff', activebackground='#ffffff', bd=0)
button3 = tk.Button(top_buttons_frame, text="Incremental Loading", command=lambda: button_click(2),
                    image=image4, bg='#ffffff', activebackground='#ffffff', bd=0)
button4 = tk.Button(top_buttons_frame, text="Data Enrichment", command=lambda: button_click(3),
                    image=image3, bg='#ffffff', activebackground='#ffffff', bd=0)

button1.place(x=0, y=3)
button2.place(x=125, y=3)
button3.place(x=250,y=3)
button4.place(x=375, y=3)


# Create a canvas in the middle
canvas = tk.Canvas(root, width=500, height=400, bg="white")
canvas.pack(padx=10, pady=10)

left_frame = Frame(root, background='sky blue', height=400, width=200)
left_frame.place(x=50, y=90)

# Right Frame
rightFrame = Frame(root, padx=15, pady=15, background='sky blue')
rightFrame.place(x=950, y=50)

# label = LabelFrame(rightFrame, text="Parameters",height=25, width=250, bg="sky blue", font='bold')
# label.grid(row=0, column=0)

label1 = LabelFrame(rightFrame, text="Configuration",height=25, width=250, bg="sky blue", font='bold')
label1.grid(row=1, column=0)

# Create text widget and specify size.
textArea = Text(rightFrame, height = 25, width = 40)
textArea.grid(row=2, column=0)

# Bottom Frame
bottomFrame = Frame(root, padx=15, pady=15, height=10)
# bottomFrame.place(x=400, y=480)
bottomFrame.pack(pady=10)

# Create the table with two columns (Name and Status)
table_columns = ("Progress", "Status")
tree = ttk.Treeview(bottomFrame, columns=table_columns, show="headings", height=5)

for col in table_columns:
    tree.heading(col, text=col)
tree.pack()

def create_table():
    table_data = [
        ("Task 1", "In Progress"),
        ("Task 2", "Completed"),
        ("Task 3", "Not Started"),
    ]
    for i, (name, status) in enumerate(table_data):
        tree.insert("", tk.END, values=(name, status))

create_table()

def on_button_press(event):
    # Store the widget type and its initial position
    widget_type = event.widget.winfo_class()
    widget_text = event.widget.cget("text")
    initial_x = event.x
    initial_y = event.y
    data = (widget_type, widget_text, initial_x, initial_y)
    event.widget.data = data

def on_button_motion(event):
    # Calculate the difference in position since drag start
    widget_type, widget_text, initial_x, initial_y = event.widget.data
    dx = event.x - initial_x
    dy = event.y - initial_y

    # Move the widget to the new position
    event.widget.place(x=event.widget.winfo_x() + dx, y=event.widget.winfo_y() + dy)


root.mainloop()
