from invoice2data import extract_data
from invoice2data.extract.loader import read_templates
import csv
import os
from datetime import datetime
import pandas as pd 
from invoice_manipulation import invoice
from invoice_to_csv import write_to_csv, return_total_expense
from rename_pdf import rename
from variables import folder_with_pdfs, folder_for_renamed_pdfs, AP_csv_file_name, folder_for_csv, vendor_usage_running_tab, folder_vendor_usage




######### MAIN METHOD #OOB  #############
#takes in folder with pdfs
def mainFunc(pdfsFolder):

    ##TODO clean up so we're only writing to CSV once
    
    invoiceCSVName = folder_for_csv + '/' + AP_csv_file_name
    f = open(invoiceCSVName, 'w', newline='\n')
    f.write('header\n')

    runningTabCSV = folder_vendor_usage + '/' + vendor_usage_running_tab
    tabCSV = open(runningTabCSV, 'w')
    tabCSV.write("%s,%s,%s,%s,%s,%s,%s\n"%('building code', 'vendor', 'account number', 'usage cost', 'meter number', 'bill end date', 'usage'))
    
    failedInvoices = []
    creditInvoices = []

    numbFiles = 0
    numbWorking = 0
    numbNotWorking = 0 
    creditInvs = 0

    for filename in os.listdir(pdfsFolder):
        if not filename.startswith('.'):
            numbFiles += 1  
            inv = invoice(pdfsFolder, filename)
           
            testBool = write_to_csv(inv, f, filename, tabCSV, failedInvoices, creditInvoices)
            if(testBool):
                numbWorking += 1
    
    #Write filenames of bad invoices
    for filename in failedInvoices:
        numbNotWorking += 1
        f.write("%s,%s\n"%(filename,"Failed to parse"))

    for arr in creditInvoices:
        creditInvs += 1 
        f.write("%s,%s,%s\n"%(arr[0],arr[1], 'Credit Invoice'))

    if(numbFiles != numbNotWorking + numbWorking + creditInvs):
        print(str(numbFiles) + "  Numb Files" )
        print(str(numbWorking) + "  Numb Working Files")
        print(str(numbNotWorking) + " Numb not working")
        print(str(creditInvs) + "  credit invs")
        missing = str(numbFiles - (numbNotWorking + numbWorking + creditInvs))
        f.write("%s\n"%(missing + "File(s) not accounted for"))
                    

                
            
            
                
            
    
    f.close()
    tabCSV.close()


    ##TODO clean up so we're only writing to CSV once
    expenseArr = return_total_expense()
    numberOfInvoices = expenseArr[0]
    totalInvoiceExpense = expenseArr[1]

    g = open(invoiceCSVName, "r")
    reader = csv.reader(g)
    mylist = list(reader)
    g.close()
    mylist[0]= ['BTCH','','',round(totalInvoiceExpense,2), numberOfInvoices]
    my_new_list = open(invoiceCSVName, 'w', newline = '\n')
    csv_writer = csv.writer(my_new_list)
    csv_writer.writerows(mylist)
    my_new_list.close()

#Function calls 

mainFunc(folder_with_pdfs)