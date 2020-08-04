import os
from invoice_manipulation import invoice
from datetime import datetime
from variables import folder_with_pdfs, folder_for_renamed_pdfs
from invoice_to_csv import building_code


#" Property_Code + "PSEG #" + Account_Number + " $" + Amount + MM-DD-YY + ".pdf"

def rename(pdf, invoice):
     #remove blank space from account number 
    accountNumber = ''
    if(str(invoice.account_number).endswith(' ')):
        accountNumber = str(invoice.account_number)[:-1]
    else:
        accountNumber = str(invoice.account_number)
    
    date = str(invoice.date.month) +"-" + str(invoice.date.day) + "-" +  str(invoice.date.year)

    #grab building code 
    buidlingCode = building_code(accountNumber) 
    if(invoice.issuer == 'Verizon'):
        print(invoice.primary_phone)
        phone = invoice.primary_phone
        if(isinstance(phone, list)):
            phone = invoice.primary_phone[0] 
        buidlingCode = building_code(str(phone).replace(" ",""))

        if(isinstance(invoice.account_number, list)):
            accountNumber = str(invoice.account_number[0]).replace(" ", "")

        

    newName = ""
    newName = str(buidlingCode) + " " + invoice.issuer + " " + str(accountNumber) + " " + "$" + str(invoice.amount) + " " + date + ".pdf"

    src = folder_with_pdfs + "/" + pdf 
    dst = folder_for_renamed_pdfs + "/" + newName

    os.rename("/Users/joshcohen/Documents/david_python_projects/"+src, dst)
