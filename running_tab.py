import csv
import os
from datetime import datetime
import pandas as pd 
from invoice_manipulation import invoice
from variables import vendor_usage_running_tab, folder_vendor_usage
from invoice_to_csv import building_code

#globalzzzzz
def vendor_tab(invoice, csv):
    #remove blank space from account number 
    accountNumber = ''
    if(str(invoice.account_number).endswith(' ')):
        accountNumber = str(invoice.account_number)[:-1]
    else:
        accountNumber = str(invoice.account_number)
    
    #grab building code 
    buidlingCode = building_code(accountNumber)


    ## PSEG CSV ##
    if(invoice.issuer == 'PSE&G'): 
        
        # Gas 
        if(hasattr(invoice, 'gas_charge')):
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s\n"%(buidlingCode,invoice.issuer,accountNumber,invoice.gas_charge,
            invoice.gas_meter, str(invoice.date.month) + "/" + str(invoice.date.day) + "/" + str(invoice.date.year), invoice.therms, 'therms'))
        # Electric
        if(hasattr(invoice, 'amount_total_electric')):
            #Parsing and reformatting
            kws = "".join(str(invoice.kws).split(','))
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s\n"%(buidlingCode,invoice.issuer,accountNumber,invoice.amount_total_electric,
            invoice.electric_meter, str(invoice.date.month) + "/" + str(invoice.date.day) + "/" + str(invoice.date.year), kws, 'kws'))


    if(invoice.issuer == 'Atlantic City Electric'): 
        
        if(hasattr(invoice, 'amount_total_electric')):
            #Parsing and reformatting
            kws = "".join(str(invoice.kws).split(','))
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s\n"%(buidlingCode,invoice.issuer,accountNumber,invoice.amount_total_electric,
            invoice.electric_meter, str(invoice.date.month) + "/" + str(invoice.date.day) + "/" + str(invoice.date.year), kws, 'kws'))


