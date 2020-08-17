import csv
import os
from datetime import datetime
import pandas as pd 
from invoice_manipulation import invoice
from variables import vendor_usage_running_tab, folder_vendor_usage
from invoice_to_csv import building_code, get_charge_amount, get_charge_code, get_issuer_code

#globalzzzzz
def vendor_tab(invoice, usageCSV):

    
    buildingCode = building_code(invoice)
    issuer = invoice.issuer
    accountNumber = invoice.accountNumber
    glCode = get_issuer_code(invoice) #GL code, forgot what it was called when i wrote this
    chargeCode = get_charge_code(invoice)
    usage = get_meter_usage()
    chargeAmount = get_charge_amount()
    
    fullDate = invoice.date
    date = str(fullDate.month) + '/' + str(fullDate.day) + '/' + str(fullDate.year) 

    ## PSEG usageCSV ##
    if(invoice.issuer == 'PSE&G'): 
         # Gas 
        if(hasattr(invoice, 'gas_charge')):
            usageCSV.write("%s,%s,%s,%s,%s,%s,%s,%s\n"%(buildingCode,issuer,accountNumber,usage,
            invoice.gas_meter, date, invoice.therms, 'therms'))
        # Electric
        if(hasattr(invoice, 'amount_total_electric')):
            #Parsing and reformatting
            kws = "".join(str(invoice.kws).split(','))
            usageCSV.write("%s,%s,%s,%s,%s,%s,%s,%s\n"%(buildingCode,invoice.issuer,accountNumber,invoice.amount_total_electric,
            invoice.electric_meter, str(invoice.date.month) + "/" + str(invoice.date.day) + "/" + str(invoice.date.year), kws, 'kws'))


    else: 


    if(invoice.issuer == 'Atlantic City Electric'): 
        
        if(hasattr(invoice, 'amount_total_electric')):
            #Parsing and reformatting
            kws = "".join(str(invoice.kws).split(','))
            usageCSV.write("%s,%s,%s,%s,%s,%s,%s,%s\n"%(buildingCode,invoice.issuer,accountNumber,invoice.amount_total_electric,
            invoice.electric_meter, str(invoice.date.month) + "/" + str(invoice.date.day) + "/" + str(invoice.date.year), kws, 'kws'))


