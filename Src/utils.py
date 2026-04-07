# istalling necessaries libraries
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import utils as ut
from thefuzz import process, fuzz
from IPython.display import display


# --1. -- DUPLICATED AND NAN
def dupli_nan_count(df):
    """
    Checks for and displays duplicated rows and missing (NaN) values in a DataFrame.

    This function serves as a quick Exploratory Data Analysis (EDA) tool. It first 
    evaluates if there are any exact duplicate rows; if duplicates exist, it displays 
    them, otherwise it prints a clear confirmation message. Finally, it calculates 
    and displays the total count of NaN (missing) values for each column.

    Parameters:
    df : The input DataFrame to be inspected.

    Returns:
    None
    """
    # looking for dupplicated values and NaN
    duplicated = df.duplicated() 
    if duplicated.sum() == 0:
        print('No duplicates')
    else:
        display(df.loc[duplicated])
    print(f"\nNaN values:")
    display(df.isna().sum())

# -- 2.-- DATE ACCURACY
def date_accuracy(df, date_col:str, year_list:list):
    """
    Check date outliers for a respective period

    Parameters:
    • df: referential Data Frame
    • date_col: df's date/timestamp column
    • year_list: referential year's list

    Returns:
    The number of outliers has the column, 
    A list unique outliers
    """
    # defining year serie
    df['anno'] = pd.to_datetime(df[date_col], format='mixed', dayfirst=True).dt.year

    # filtering dates not in interested range
    df_outliers = df[~df['anno'].isin(year_list)]

    # showing unique outranged dates
    df_unique = df_outliers['anno'].unique()

    # print results
    print(f"{len(df_outliers)} rows out of range found.")
    print(df_unique)

# -- 3.-- OUTLIERS DETECTION
def outliers_auto_detection(df, multiplier=1.5):
    """
    Automatically detects outliers in all numeric columns of a DataFrame using 
    the Interquartile Range (IQR) method. 

    The function calculates the Q1 (25th percentile) and Q3 (75th percentile) 
    for each numeric column. Outliers are defined as values falling below 
    (Q1 - multiplier * IQR) or above (Q3 + multiplier * IQR). It also prints 
    the count of outliers per column and generates a horizontal boxplot for 
    visual inspection.

    Parameters:
    
    df : The input DataFrame containing the data to be analyzed.
    multiplier : float, optional .The standard default is 1.5. Use a higher value (e.g., 3.0) to 
        detect only extreme outliers.

    Returns:
    A boolean mask (Series) with the same index as the input DataFrame. 
    Returns True for rows that contain at least one outlier in any 
    numeric column, and False otherwise.
    """

    # selecting numeric columns
    numeric_cols = df.select_dtypes(['int64', 'float64'])

    # defining empty list to save columns with outliers
    outliers_col_list = []
    
    # defining global mask to save outliers row
    global_mask = pd.Series(False, index=df.index)

    # calculating IQR and upper e lower limit
    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - (multiplier * iqr)
        upper = q3 + (multiplier * iqr)

        # filtering outliers 
        col_mask = (df[col] < lower) | (df[col] > upper)

        # updating global_mask
        global_mask = global_mask | col_mask

        # defining outliers
        outliers = df[col_mask]
        print(f"{col}: {len(outliers)} found")

        # appending result to list
        if len(outliers) > 0:
            outliers_col_list.append(col)

    # visualizing
    if len(outliers_col_list) > 0:
        plt.figure(figsize=(10, 6)) 
        sns.boxplot(data=df[outliers_col_list], orient='h', color='#b22222')
        plt.xscale('log') 
        plt.title(f"Columns Outliers", fontsize=15, fontweight='bold')
        plt.show()
    
    return global_mask

# -- 4.-- DATA CLEANING FUNCTION
def basic_cleaning(df, mapping_dict):
    """
    It applies basic cleaning to df's data in order to easily process them

    Parameters:
    • df: dataframe that has to be cleaned
    • mapping_dict: dict to handle different references

    Returns:
    Df with cleaned data
    """

    df_c = df.copy()

    for col in df_c.columns:
        if df_c[col].dtype == 'object':

            # --- STEP 1: cleaning noises char ---
            df_c[col] = df_c[col].str.replace('@', 'a', regex=False)
            df_c[col] = df_c[col].str.replace(r'\s+', ' ', regex=True) 
            df_c[col] = df_c[col].str.strip().str.lower().replace(mapping_dict, regex=False)

        if 'date' in col or 'data' in col or 'timespamp' in col:
            df_c[col] = pd.to_datetime(df_c[col], format='mixed', dayfirst=True, errors='coerce')

    return df_c

# --5.-- FIXING QUANTITIES ERRORS
def fix_unit_errors(df, unit_col:str, price_col:str, item_col:str, cat_col:str, threshold:int, premium_list:list, safe_cats:list):
    """
    Fixes typical HoReCa typos (e.g. 'g' instead of 'kg')
    Finds out uom in g and quantity in kg, 
    Threshold save ingredients used in gr such as truffle, caviar, spices (Saffron)
    """
    # We always create a copy so as not to dirty the original dataset
    df_fixed = df.copy()
    
    # building the smart mask
    smart_fix_mask = (
        (df_fixed[unit_col] == 'g') & 
        (df_fixed[price_col] > threshold) & 
        (df_fixed[cat_col].isin(safe_cats)) &
        (~df_fixed[item_col].str.contains('|'.join(premium_list), case=False, na=False))
    )
    
    # applaing corrections
    df_fixed.loc[smart_fix_mask, unit_col] = 'kg'
    
    # printing a useful log for those who run the code
    fixed_count = smart_fix_mask.sum()
    if fixed_count > 0:
        print(f"BUSINESS RULE: Fixed {fixed_count} unit errors ('g' to 'kg') for products > {threshold}€")
    else:
        print("BUSINESS RULE: No unit error (g -> kg) found.")
        
    return df_fixed

# -- 6.-- STANDARDIZE QTY FUNCTION
def standardize_quantities(df, qty_cols:str, unit_col:str):
    """
    Standardize quantities in kg or lt based on a unit of measurement column.
    
    Parameters:
     df (DataFrame): The dataframe to clean.
     qty_cols(str or list): Name of the column (or list of columns) of quantities.
     unit_col (str): Name of the unit column.

    Returns:
    Df with standardized quanrtities
    """
    df_c = df.copy()
    
    # If we pass only one column as a string, we turn it into a list for convenience
    if isinstance(qty_cols, str):
        qty_cols = [qty_cols]
        
    # Conversion map to base unit (kg / lt)
    multipliers = {
        'g': 0.001, 'gr': 0.001, 'gr.': 0.001,'grammi': 0.001, '1000g': 1.0,
        'ml': 0.001, 'millilitri': 0.001, 'ml.': 0.001, '1000ml': 0.001,
        'kg.': 1.0, 'kg': 1.0, 'kilo': 1.0, 
        'lt': 1.0, 'l': 1.0, '1l': 1.0, 'l.': 1.0, 'lt.': 1.0,    
    }
    
    # We clean strings of the unit of measurement to avoid errors (e.g. " Kg " -> "kg")
    df_c[unit_col] = df_c[unit_col].astype(str).str.strip().str.lower()
    
    # 1. Let's create the conversion factor. If the unit is not in the dictionary (e.g. 'pz', 'cassa'), 1.0 remains
    conv_factor = df_c[unit_col].map(multipliers).fillna(1.0)
    
    # 2 multipling all the quantity columns you explicitly requested
    for col in qty_cols:
        df_c[col] = (df_c[col] * conv_factor).round(2)
        
    # 3. standardizing the labels of the units of measurement (g -> kg, ml -> lt)
    unit_label_map = {
        'g': 'kg', 'gr': 'kg', 'gr.': 'kg','grammi': 'kg', '1000g': 'kg', 'kilo': 'kg',
        'ml': 'lt', 'millilitri': 'lt', 'ml.':'lt', '1000ml': 'lt', 'l': 'lt', 'l.':'lt','1l': 'lt', 'lt.': 'lt',
        'pezzi': 'pz', 'pezzo':'pz', 'cad': 'pz', 'nr': 'pz', '1': 'pz',
        'bottiglia': 'bt', 'bott': 'bt', '750ml': 'bt', '0.75': 'bt'
    }
    df_c[unit_col] = df_c[unit_col].replace(unit_label_map) 
    
    return df_c

# -- 7.-- MANAGING QUANTITY EXCEPTION
def quantity_exception_manage(df, product_col, quantity_col, uom_col, conversion_map:dict, price_col=None):
    """
    Apply tuple-based math conversions: (factor, from_unit, to_unit)
    from_unit can be a string ('pz') or a list of strings (['pz', 'bt'])

    Parameters:
    • df: referential df,
    • product_col: Serie with items/ingredients names,
    • quantity_col: Serie with product quantity amount
    • uom_col: referncial quanity unit of measurement
    • conversatio_map: dict with product:quantity used for specific items
    • price_col: Serie with item's price, to be recalculated in relation to quantity factor

    Returns:
    dfs with quantities and prices recalculated
    """
    df_c = df.copy()
    df_c[product_col] = df_c[product_col].str.lower()
    
    converted_count = 0
    
    for product, (factor, from_unit, to_unit) in conversion_map.items():
        
        # checking if "from_unit" is a str or a list
        if isinstance(from_unit, (list, tuple)):
            unit_mask = df_c[uom_col].isin(from_unit)
        else:
            unit_mask = df_c[uom_col] == from_unit
            
        # We create the mask by merging the name and condition on the unit
        mask = (df_c[product_col] == product) & unit_mask
        
        if mask.any():
            # 1. multiplies the amount
            df_c.loc[mask, quantity_col] *= factor
            
            # 2. If the price column exists, it divides it (e.g. invoices)
            if price_col and price_col in df_c.columns:
                df_c.loc[mask, price_col] /= factor
                
            # 3. Update final measurement unit
            df_c.loc[mask, uom_col] = to_unit
            
            converted_count += mask.sum()
            print(f"Converted {mask.sum()} rows of {product} from {from_unit} to {to_unit}")
            
    if converted_count == 0:
        print("No conversion applied. Verify that the names and units match.")
            
    return df_c

# -- 8.-- FUZZING FUNCTON
def get_best_match(df_name, bench_name, threshold=80):
    """
    It compares a list of names to a benchmark and returns a mapping dictionary.
    
    Parameters:
    • df_name (pd.Series or list): The DataFrame column with the "dirty" names to fix.
    • bench_name (pd.Series or list): The column/list with the correct names (e.g. from the benchmark file).
    • threshold (int): Minimum score (0-100) to consider the match valid. By default 80.
    
    Return:
    dict: A dictionary in the format {'dirty_name': 'clean_name'}
    """
    # extract unique names from both lists, removing NaN values
    unique_name = df_name.dropna().unique().astype(str) 
    unique_bench_name = bench_name.dropna().unique().astype(str)
    
    # create an empty mapping dictionary
    mapping_dict = {}

    # loop through each unique name in the DataFrame column
    for name in unique_name:
        # checking best match
        best_match = process.extractOne(name, unique_bench_name, scorer=fuzz.token_set_ratio)

        # checking score and adding to dict
        if best_match and best_match[1] >= threshold:
            mapping_dict[name] = best_match[0]
        else:
            mapping_dict[name] = pd.NA
    
    failed_matches = sum(1 for v in mapping_dict.values() if pd.isna(v))
    print(f"Failed matches: {failed_matches}/{len(mapping_dict)}")

    return mapping_dict


# -- 9.-- IMPUTING MISSING VALUES
def imputing_benchmark_price(df, imputed_col:str, name_col:str, price_col:str):
    """
    Imputing missing price 

    Parameters:
    • df: referential df
    • imputed_col: column to modify
    • name_col: benchmark product name column
    • price_col: referential price column used to impute missing price

    Returns:
    Df without missing price
    """
    # 1. resetting the index to avoid chaos from incorrect alignment
    df = df.reset_index(drop=True)
    
    # 2. creating a clean "Map": only rows with name and price present
    # removing duplicates to have 1 price for every name
    lookup_table = df.dropna(subset=[name_col, price_col]).drop_duplicates(name_col)
    price_dict = lookup_table.set_index(name_col)[price_col].to_dict()
    
    # 3. appling the mapping and fill the gaps
    mapped_values = df[name_col].map(price_dict)
    df.loc[:, imputed_col] = df[imputed_col].fillna(mapped_values)
    
    return df

# -- 10.-- DELTA PRICE FLAG
def prices_delta_flag(df, price_col:str, benchmark_price:str):
    """
    Calculates the percentage deviation between a given price and a benchmark 
    price, and flags anomalies that exceed a 20% threshold.

    This function computes the absolute percentage difference between the specified 
    price column and the benchmark price column. It then creates a boolean flag 
    indicating whether the deviation is strictly greater than 20%. Finally, it 
    prints the total count of detected anomalies to the console.

    Parameters:
    df : The input DataFrame containing the pricing data.
    price_col : The name of the column containing the price to evaluate (e.g., actual cost).
    benchmark_price : The name of the column containing the reference benchmark price.

    Returns:
    The modified DataFrame with two additional columns:
    - 'prices_deviation_%': The absolute percentage deviation as a decimal (float).
    - 'prices_flag': A boolean mask (True/False) where True indicates an anomaly 
        (deviation > 20%).
    """

    df['prices_deviation_%'] = abs(df[price_col] - df[benchmark_price]) / df[benchmark_price]
    df['prices_flag'] = df['prices_deviation_%'] > 0.20
    
    if df['prices_flag'].sum() > 0:
        print('Prices anomalies:',  df['prices_flag'].sum())
    else:
        print('There are no prices anomalies')

    return df
