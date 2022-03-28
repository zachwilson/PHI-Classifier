import pandas as pd
import numpy
import math
import random
import datetime
import dateutil
import re
import csv

def read_data():
    file_string = input("please enter a comma sepperated list of files\n=>")
    files = file_string.split(',')
    frames = []
    for data_file in files:
        ext = data_file.split('.')[-1]
        if ext == 'xlsx':
            xl = pd.ExcelFile(data_file)
            sheets = input("Excel file detected please enter the numbers of the sheets you want scanned\n=>")
            sheets = sheets.split(',')
            for sheet in sheets:
                df = pd.read_excel(data_file,sheet_name=int(sheet.strip()))
                df.name = data_file + '-' +  str(sheet)
                frames.append(df)
        elif ext == 'csv':
            seperator = input('Please Input the seperator of ' + data_file + '\n=>')
            df = pd.read_csv(data_file,sep=seperator)
            df.name = data_file
            frames.append(df)
    return frames

def identify_mrn(data):
    mrn_cols = []
    for col in data:
        mrn_identifiers = ['mrn']
        if any([ident in col.lower() for ident in mrn_identifiers]):
            mrn_cols.append(col)
    #Add columns identified based on values
    return mrn_cols

def identify_dates(data):
    date_cols = []
    for col in data:
        date_identifiers = ["date","time","year","day","month",'check-in','check-out']
        if any([ident in col.lower() for ident in date_identifiers]):
            date_cols.append(col)
    #Check values
    row = data.iloc[0]
    for index in range(row.size):
        col = data.columns[index]
        if col in date_cols:
            continue
        if type(row[index]) == pd.Timestamp or type(row[index]) == datetime.datetime:
            date_cols.append(col)
        else:
            try:
                for i in range(0,10):
                    dateutil.parser.parse(data[col][i])
                date_cols.append(col)
            except:
                pass
    return date_cols

def identify_names(data):
    name_cols = []
    for col in data:
        name_identifiers = ["name","patient","subject"]
        if any([ident in col.lower() for ident in name_identifiers]):
            name_cols.append(col)
    #Add columns identified based on values
    return name_cols

def identify_addresses(data):
    address_cols = []
    for col in data:
        address_identifiers = ["address","location",'home']
        if any([ident in col.lower() for ident in address_identifiers]):
            address_cols.append(col)
    #Add columns identified based on values
    return address_cols

def identify_csn(data):
    csn_cols = []
    for col in data:
        csn_identifiers = ["csn"]
        if any([ident in col.lower() for ident in csn_identifiers]):
            csn_cols.append(col)
    #Add columns identified based on values
    row = data.iloc[0]
    for index in range(row.size):
        col = data.columns[index]
        if col in csn_cols:
            continue
        match = True
        for i in range(0,10):
            val = data[col][i]
            reg = "^[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]$"
            if not re.match(reg,str(val)):
                match = False
        if match:
            csn_cols.append(col)
    return csn_cols

def identify_phone(data):
    phone_cols = []
    for col in data:
        phone_identifiers = ["phone",'contact number']
        if any([ident in col.lower() for ident in phone_identifiers]):
            phone_cols.append(col)
    #Add columns identified based on values
    row = data.iloc[0]
    for index in range(row.size):
        col = data.columns[index]
        if col in phone_cols:
            continue
        match = True
        for i in range(0,10):
            val = data[col][i]
            reg = "^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$"
            if not re.match(reg,str(val)):
                match = False
        if match:
            phone_cols.append(col)
    return phone_cols

""" def age_mask(data, col):
    today = datetime.date.today()
    masked = []
    for element in data[col]:
        if pd.isnull(element):
            masked.append("N\A")
            continue
        date = pd.Timestamp.to_pydatetime(element).date()
        time_between = today - date
        age = math.floor(time_between.days / 365)
        if age >= 90:
            masked.append('>90')
        else:
            masked.append(str(age))
    data = data.drop(col,axis = 1)
    data["age"] = masked
    return data

def date_shift(data):
    #https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5070517/
    pass """

def simple_date_shift():
    #This chunk creates the big data frame
    files = read_data()
    big_frame = files[0]
    for file in files:
        big_frame = big_frame.merge(file,how='outer')
    data = big_frame
    #Get the subject and date columns
    ident_col = input("enter the column containing individual subjects\n=>")
    date_cols = input("enter the columns that have dates seperated by a comma\n=>")
    date_cols = date_cols.strip().split(',')
    shifts = {}
    #Get a list of every unique identifier in the subject column
    uniques = data[ident_col].unique()
    #Assign each one a random amount to shift by
    for element in uniques:
        shift = random.SystemRandom().randint(1,366)
        shifts[element] = shift
    #Itterate over the data frame shifting any date by the amount previously generated
    for index,row in data.iterrows():
        #To make things simpler I make a new row with the shifts and replace instead of changing the old row
        new_row = []
        for col in data:
            if col in date_cols:
                #If the entry was not processed as a date remove it instead of shifting it
                if not (type(row[col]) == pd.Timestamp or type(row[col]) == datetime.datetime):
                    new_row.append(numpy.nan)
                    continue
                new_row.append(row[col] + pd.Timedelta(days = shifts[row[ident_col]]))
            else:
                new_row.append(row[col])
        data.iloc[index] = new_row
    name = input("Please enter name of new file\n=>")
    data.to_csv(name + '.csv',index=False)
    return data

def detect_PHI():
    phi = {}
    files = read_data()
    #Each type of PHI gets its own identification function
    #Each function returns a list of columns that might contain that type of PHI
    for data in files:
        for column in identify_mrn(data):
            phi[data.name + ': ' + column] = ('MRN',data[column][:10])
        for column in identify_dates(data):
            phi[data.name + ': ' + column] = ('dates',data[column][:10])
        for column in identify_names(data):
            phi[data.name + ': ' + column] = ('names',data[column][:10])
        for column in identify_addresses(data):
            phi[data.name + ': ' + column] = ('addresses',data[column][:10])
        for column in identify_csn(data):
            phi[data.name + ': ' + column] = ('CSN',data[column][:10])
        for column in identify_phone(data):
            phi[data.name + ': ' + column] = ('Phone',data[column][:10])
    print('Here are the suspected PHI columns')
    print('file: column, phi type')
    for column in phi:
        print(column + ', ' + phi[column][0])
        print('\nData Examples:')
        for example in phi[column][1]:
            print(example)
        print('-------------')

def generate_ids(list_of_people):
    # This just takes a list of people and assigns a random ID to each of them
    ids = {}
    for person in list_of_people:
        found = False
        while not found:
            id = random.SystemRandom().randint(1,len(list_of_people)*10)
            if not id in ids:
                ids[person] = id
                found = True
    return ids

def create_subject_id():
    #Read in the files and combine them
    files = read_data()
    big_frame = files[0]
    for file in files:
        #An outer join presevers all of the data in every table i.e. Union
        big_frame = big_frame.merge(file,how='outer')
    #Get the subject Coulmn and assign IDs
    subject_col = input('Input Subject Column\n=>')
    people = big_frame[subject_col].unique()
    id_mapping = generate_ids(people)
    big_frame['Subject ID'] = big_frame[subject_col].map(id_mapping)
    #Get the PHI Coulmns and split them off into their own data frame
    phi_columns = input('Please enter the Personally identifing collumns seperated by commas\n=>')
    phi_columns = phi_columns.split(',')
    phi_columns = list(map(lambda x:x.strip(),phi_columns))
    map_cols = phi_columns + ['Subject ID']
    map_frame = big_frame[map_cols].copy()
    #Drop all PHI columns from the first data frame
    big_frame = big_frame.drop(phi_columns,axis=1)
    #Save the two new data frames
    output_name = input("Please enter name of new file without extension\n=>")
    big_frame.to_csv(output_name + '.csv',index=False)
    map_frame.to_csv(output_name + '_Sub_ID_map.csv',index=False)

"""def module_select():
    #This is old and was used as an interface
    modules = {'1':detect_PHI,'2':create_subject_id}
    while True:
        selection = input('Please enter the number of the module you wish to use\n1: Detect PHI\n2:create subject IDs\n0: Exit\n=>')
        if selection == '0':
            break
        elif selection in modules:
            modules[selection]()
        else:
            print('Invalid module Please try agian')

def get_disease_list():
    pass

def mask_rare_diseases():
    data = read_data()
    diseases = get_disease_list()
    disease_col = input('Enter Column with desease name\n=>')
    while True:
        mask_type = input('Enter the number of the masking type you would like\n1: Remove only the desease name\n2: Remove the entire row in the table\n=>')
        if mask_type in ['1','2']:
            break
        else:
            print('Unrecognized masking option, Please try again')
    to_drop = []
    for i in range(data[disease_col]):
        if data[disease_col][i] in diseases:
            to_drop.append(i)
    if mask_type == '1':
        for index in to_drop:
            data[disease_col][index] = None
    if mask_type == '2':
        data = data.drop(to_drop)
    return data """


if __name__ == "__main__":
    #data = read_data("Classifier_test.xlsx")
    #print(simple_date_shift(data,'feMRN',['fbirth_date','fAdmission_Dttm','fDischarge_Dttm']))
    #print(mask_phi("Classifier_test.xlsx"))
    print(simple_date_shift())
