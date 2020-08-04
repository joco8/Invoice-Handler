from invoice2data import extract_data
from invoice2data.extract.loader import read_templates
import csv
import os
from datetime import datetime
import pandas as pd 
from invoice_manipulation import invoice
from invoice_to_csv import write_to_csv
from rename_pdf import rename
from variables import folder_with_pdfs, folder_for_renamed_pdfs, AP_csv_file_name, folder_for_csv, vendor_usage_running_tab, folder_vendor_usage
from running_tab import vendor_tab



######### MAIN METHOD #OOB  #############
#takes in folder with pdfs
def mainFunc(pdfsFolder):

    numberOfInvoices = 0
    totalInvoiceExpense = 0
    ##TODO clean up so we're only writing to CSV once
    
    invoiceCSVName = folder_for_csv + '/' + AP_csv_file_name
    f = open(invoiceCSVName, 'w')
    f.write('header\n')

    runningTabCSV = folder_vendor_usage + '/' + vendor_usage_running_tab
    tabCSV = open(runningTabCSV, 'w')
    tabCSV.write("%s,%s,%s,%s,%s,%s,%s\n"%('building code', 'vendor', 'account number', 'usage cost', 'meter number', 'bill end date', 'usage'))
    

    for filename in os.listdir(pdfsFolder):
        if not filename.startswith('.'):
            numberOfInvoices += 1
            inv = invoice(pdfsFolder, filename)
            
            write_to_csv(inv, f, filename)
        
            if(hasattr(inv, 'amount')):
                if(hasattr(inv, 'credit_bool')):
                    totalInvoiceExpense -= inv.amount
                else:
                    totalInvoiceExpense += inv.amount
                vendor_tab(inv, tabCSV)
            #rename(filename, inv)
            
                    # f.write("%s,%s,%s,%s\n"%(filename, 'Error in File', error, "Please manually fill in the info for this file"))
                    # print("\n\n\n\n\n\n\n\n\nERROR FOUND")

                
            
            
                
            
    
    f.close()
    tabCSV.close()


    ##TODO clean up so we're only writing to CSV once
    g = open(invoiceCSVName, "r")
    reader = csv.reader(g)
    mylist = list(reader)
    g.close()
    mylist[0]= ['BTCH','','',totalInvoiceExpense, numberOfInvoices]
    my_new_list = open(invoiceCSVName, 'w', newline = '')
    csv_writer = csv.writer(my_new_list)
    csv_writer.writerows(mylist)
    my_new_list.close()

#Function calls 

mainFunc(folder_with_pdfs)