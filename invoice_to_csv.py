#invoice_to_csv

from invoice2data import extract_data
from invoice2data.extract.loader import read_templates
import csv
import os
from datetime import datetime
import pandas as pd 
from variables import vendor_usage_running_tab, folder_vendor_usage, folder_with_pdfs, folder_for_renamed_pdfs

numberOfInvoices = 0
totalInvoiceExpense = 0

global wroteInvBool

#variables that will be used for vendor usage csv, will have same values stored here though
global usage__charge # gas_charge, amount_total_electric
global usage__meterNumber 
global usage__usageAmount 
global usage__date
global usage__glCode 
global usage__issuerAbbriviation
global usage__accountNumber
global usage__buildingCode
global usage__usageType

#Takes a single invoice adds info to an existing CSV file (csv) 
def write_to_csv(invoice, csv, filename, usageCSV, failedInvoices, creditInvoices):
    # print(filename)
    wroteInvBool = False


    try:
        print(invoice.issuer, hasattr(invoice, 'issuer'))
        if((invoice.issuer == 'null')):
            failedInvoices.append(filename)
            return



        #cross invoice object 
        fullDate = invoice.date
        date = str(fullDate.month) + '/' + str(fullDate.day) + '/' + str(fullDate.year) 
        buildingCode = building_code(invoice)  #grab building code - Takes invoice as input
        invoiceNumber = invoice.invoice_number
        invAmount = invoice.amount
        accountNumber = get_account_number(invoice)
        issuerCode = get_issuer_code(invoice)
        # print(issuerCode)
        chargeCode = get_charge_code(invoice)
        meterReading = get_meter_amount(invoice, "")

        #set globals
        usage__charge = invAmount # this will be reset for PSEG gas or electric in PSEG section
        usage__meterNumber = '0'
        usage__usageAmount = '0'
        usage__date = date
        usage__glCode = chargeCode
        usage__issuerAbbriviation = issuerCode
        usage__accountNumber = accountNumber
        usage__buildingCode = buildingCode

        if(hasattr(invoice, "credit_bool")):
            newName = str(buildingCode) + " " + invoice.issuer + " " + str(accountNumber) + " " + "$" + str(invAmount) + " " + date.replace('/',"-") + ".pdf"
            creditInvoices.append([newName, filename])
            rename(invoice, filename, accountNumber, buildingCode, invoice.issuer, "("+ str(invAmount) + ")", date)
            return

        if(invoice.issuer == "Comcast"):
            invoiceNumber = date.replace("/",'') + accountNumber[12:] 

        if(invoice.issuer != "PSE&G"):
            # print("Are we here")
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%('INVH',invoiceNumber,date,round(invAmount,2),
                accountNumber,"U",issuerCode, date,date,"1","YES",filename))

            #DST Line 
            csv.write("%s,%s,%s,%s,%s\n"%("DIST",buildingCode,chargeCode,
                meterReading, round(invAmount,2)))
            
            add_to_total_expense(invAmount)
            wroteInvBool = True
            rename(invoice, filename, accountNumber, buildingCode, invoice.issuer, invAmount, date)
            
            if(invoice.issuer == 'American Water'):
                if(hasattr(invoice, 'total_gallons')):
                    usage__usageAmount = invoice.total_gallons
            


            
        else:
            ## THIS IS JUST FOR PSEG #### 
            psegInfo = check_pseg_info(invoice)
            if(psegInfo == -1):
                csv.write("%s,%s,%s\n"%("Could not parse pdf", filename, ', , , , , , , , Error'))
            gas = electric = electricSupply = gasSupply = other = unmetered = 0
            psegCharges = ['gas_charge', 'amount_total_electric', 'other_charges']
            addsUp = 0
            for charge in psegCharges:
                if(hasattr(invoice, charge)):
                    addsUp = addsUp + float(invoice.__getattribute__(charge))
            if(addsUp != invAmount):
                wroteProperly = write_pseg_from_lines(invoice, csv, buildingCode,invoiceNumber, date, invAmount, accountNumber, issuerCode,filename, failedInvoices)
                if(wroteProperly):
                    wroteInvBool = True
            else:
                ######### if DIST lines add up to invoice lines ############# 
                csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%('INVH',invoiceNumber,date,invAmount,
                    accountNumber,"U",issuerCode, date,date,"1","YES",filename))
            
                for charge in psegCharges:
                    # print(charge)
                    if(hasattr(invoice, charge)):
                        # print('has attribute')
                        #DST Line 
                        chargeCode = get_charge_code(str(charge)) #returns the GL CODE 
                        meterAmount = get_meter_amount(invoice, charge)
                        chargeAmount = get_charge_amount(invoice ,charge)
                        csv.write("%s,%s,%s,%s,%s\n"%("DIST",buildingCode,chargeCode,
                            meterAmount, chargeAmount))
                add_to_total_expense(round(invAmount,2))
                rename(invoice, filename, accountNumber, buildingCode, invoice.issuer, invAmount, date)
                wroteInvBool = True
                

            
            

                ## Running Total for header BTCH Lines ## 
            
        # write_vendor_usage(invoice, filename, True)

    except Exception as error:
        print(error)
        wroteInvBool = False
        failedInvoices.append(filename)
        # write_vendor_usage(invoice, filename, False)
        pass
    
    return wroteInvBool
        


def write_pseg_from_lines(invoice, csv, buildingCode, invoiceNumber, date, invAmount, accountNumber, issuerCode,filename, failedInvoices):

    successfullyWroteCsv = False

    electricAndOthersFlag = False
    
    # Go through the Billing Summary table and pick out every charge in a less regexy way 
    dstSum = 0 #count if these lines add up if not, just write  a line that that describes this
    if(hasattr(invoice, 'lines')):
        for line in invoice.lines:
            #print(line['charge_description'], " " ,line['charge_amount'])
            if(('charges' in line['charge_description']) | ('Charges' in line['charge_description'])):
               # print(line)
                if('Electric' in line['charge_description']):
                    dstAmount = line['charge_amount'].replace('$','')
                    if(line['charge_description'].endswith('-')):
                        dstAmount = '-' + dstAmount

                    
                    dstSum += float(dstAmount.replace(',','')) 
                elif(('gas' in line['charge_description']) | ('Gas' in line['charge_description'])):
                    dstAmount = line['charge_amount'].replace('$','')
                    if(line['charge_description'].endswith('-')):
                        dstAmount = '-' + dstAmount

                    
                    dstSum += float(dstAmount.replace(',','')) 
                elif(('unmetered' in line['charge_description']) | ('Unmetered' in line['charge_description'])):
                    dstAmount = line['charge_amount'].replace('$','')
                    if(line['charge_description'].endswith('-')):
                        dstAmount = '-' + dstAmount

                    
                    dstSum += float(dstAmount.replace(',','')) 
                elif('month' in line['charge_description']):
                    print('expected total')
                else:
                    dstAmount = line['charge_amount'].replace('$','')
                    if(line['charge_description'].endswith('-')):
                        dstAmount = '-' + dstAmount        
                            
                    dstSum += float(dstAmount.replace(',','')) 
                    if(invAmount == invoice.amount_total_electric + round(float(dstAmount.replace(',','')),2) ):
                        electricAndOthersFlag = True 
                       # print("Electric adds up")
                        
        if((dstSum != invAmount) & (round(dstSum,2) != invAmount)):
           ## print("Printing in sum doesn't add up in Line by line for loop")
            failedInvoices.append(filename)
        else:
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%('INVH',invoiceNumber,date,round(invAmount,2),
                accountNumber,"U",issuerCode, date,date,"1","YES",filename))
            dstSum = 0
        
            for line in invoice.lines:
            #print(line['charge_description'], " " ,line['charge_amount'])
                if(('charges' in line['charge_description']) | ('Charges' in line['charge_description'])):
                   # print(line['charge_amount'].replace('$',''))
                    if('Electric' in line['charge_description']):
                        dstAmount = line['charge_amount'].replace('$','')
                        if(line['charge_description'].endswith('-')):
                            dstAmount = '-' + dstAmount
                        dstSum += float(dstAmount.replace(',','')) 
                        pseg_error_dst(invoice, csv, buildingCode, '5500-5000',date, dstAmount)
                    elif(('gas' in line['charge_description']) | ('Gas' in line['charge_description'])):
                        dstAmount = line['charge_amount'].replace('$','')
                        if(line['charge_description'].endswith('-')):
                            dstAmount = '-' + dstAmount
                        dstSum += float(dstAmount.replace(',','')) 
                        pseg_error_dst(invoice, csv, buildingCode, '5500-6000',date, dstAmount)
                    elif(('unmetered' in line['charge_description']) | ('Unmetered' in line['charge_description'])):
                        dstAmount = line['charge_amount'].replace('$','')
                        if(line['charge_description'].endswith('-')):
                            dstAmount = '-' + dstAmount
                        dstSum += float(dstAmount.replace(',','')) 
                        pseg_error_dst(invoice, csv, buildingCode, '5500-6000',date, dstAmount)
                    elif('month' in line['charge_description']):
                        print('expected total')
                    else:
                        dstAmount = line['charge_amount'].replace('$','')
                        if(line['charge_description'].endswith('-')):
                            dstAmount = '-' + dstAmount
                        dstSum += float(dstAmount.replace(',','')) 
                        print("FOUNDD THE NEGATIVE CHARGE " + dstAmount)
                        pseg_error_dst(invoice, csv, buildingCode, '5500-5000',date, dstAmount)
            
            
            add_to_total_expense(round(float(str(dstSum).replace(',','')),2))
            rename(invoice, filename, accountNumber, buildingCode, invoice.issuer, invAmount, date)
            successfullyWroteCsv = True
                    
    else:
        failedInvoices.append(filename)
    
    return successfullyWroteCsv
                

def pseg_error_dst(invoice, csv, buildingCode, chargeCode, date, dstAmount):
    meterAmount = ""
    if(chargeCode == '5500-6000'):
        if(hasattr(invoice, 'therms')):
            meterAmount = str(invoice.therms) + " therms" 
            meterAmount = meterAmount.replace(',','')
    else:
        if(hasattr(invoice, 'kws')):
            meterAmount = str(invoice.kws) + " kws" 
            meterAmount = meterAmount.replace(',','')
    if(float(dstAmount.replace(",",'')) < 0):
        meterAmount = ''
    

    dstAmount = str(dstAmount).replace(',','')
    csv.write("%s,%s,%s,%s,%s\n"%("DIST",buildingCode,chargeCode,
        meterAmount, dstAmount))

def get_charge_amount(invoice,charge):
    chargeAmount = invoice.__getattribute__(charge)
    chargeAmount = str(chargeAmount).replace(',','')

    return chargeAmount

def check_pseg_info(inv):
    if(hasattr(inv, 'gas_charge') | hasattr(inv, 'amount_total_electric')):
        if(hasattr(inv, 'gas_charge') & hasattr(inv, 'amount_total_electric')):
            if(float(inv.gas_charge) + float(inv.amount_total_electric) != float(inv.amount)):
                return 3.0
            else:
                return 2.0
        elif(hasattr(inv, 'gas_charge')):
            return 1.1
        elif(hasattr(inv, 'amount_total_electric')):
            return 1.2
        else:
            return -1.0
    else: 
        return -1.0

def get_account_number(invoice):
    accNumber = invoice.account_number
    if(isinstance(accNumber, list)):
        return accNumber[0]
    return accNumber

def get_meter_amount(inv, charge):
    if(charge == 'gas_charge'):
        return str(inv.therms).replace(',','') + ' therms'
    if(charge == "amount_total_electric"):
        if(hasattr(inv, 'kws')):
            if(isinstance(inv.kws, list)):
                kws = 0
                for numb in inv.kws:
                    kws += float(numb.replace(',',''))
                return str(kws).replace(',','') + ' kws'
            else:
                return str(inv.kws).replace(',','') + ' kws'
        else:
            return "0 kws"
    if(inv.issuer == "American Water"):
        if(hasattr(inv, 'total_gallons')):
            gls = inv.total_gallons
            if(isinstance(gls, list)):
                gls = str(str(gls[0]).replace(" ","")).replace(',','') 
        
            gallons = str(gls) + ' gallons'
            return gallons.replace(',','')
    else: 
        return ''


def get_charge_code(inv):
    # print(inv)
    if(hasattr(inv, 'issuer')):
        if(inv.issuer == 'Atlantic City Electric'):
            return '5500-5000'
        elif(inv.issuer == 'Republic Service'):
            return '5500-5000'
        elif(inv.issuer == 'Comcast'):
            return '6000-3300'
        elif(inv.issuer == 'American Water'):
            return '5500-7000'
        elif(inv.issuer == 'Verizon'):
            return '6000-3300'
    else: 
        if(inv == 'gas_charge'):
            return "5500-6000"
        if(inv == "amount_total_electric"):
            return "5500-5000"
        else:
            return ''


def get_issuer_code(inv):
    if(inv.issuer == 'PSE&G'):
        return 'PSEG'
    elif(inv.issuer == 'Atlantic City Electric'):
        return 'ACELE'
    elif(inv.issuer == 'Republic Service'):
        return 'REPSE'
    elif(inv.issuer == 'Comcast'):
        return 'COMCA'
    elif(inv.issuer == 'American Water'):
        return 'NJAW'
    elif(inv.issuer == 'Verizon'):
        return 'VERIZ'



def add_to_total_expense(invAmount): 
           
    #Add to total expenses 
    global totalInvoiceExpense
    totalInvoiceExpense += invAmount
    #add to running invoice count
    global numberOfInvoices 
    numberOfInvoices += 1


#Grab Building Code 
def building_code(inv):

    #remove blank space from account number 
    acc_number = get_account_number(inv)
    if(str(acc_number).endswith(' ')):
        acc_number = str(acc_number)[:-1]
    else:
        acc_number = str(acc_number)

    #Verizon building codess are liked to the phone number 
    if(inv.issuer == 'Verizon'):
        if(hasattr(inv, 'primary_phone')):
            # print(inv.primary_phone)
            phone = inv.primary_phone
            if(isinstance(phone, list)):
                phone = inv.primary_phone[0] 
                acc_number = str(phone).replace(" ","")
        else: 
            return "PDF couldn't parse inv phone number"
    njAccNumb = ''
    if(inv.issuer == "American Water"):
        # print(inv.account_number)
        acc_number = 0
        if(isinstance(inv.account_number, list)):
            for acc in inv.account_number:
                # print(acc)
                if(acc.find('-') & len(acc) > 5):
                    acc_number = (str(acc).split("-"))[1]
        else:
            acc = str(inv.account_number)
            acc_number = (acc.split("-"))[1]
        
        
    print(acc_number)
    #open reference doc with building codes
    g = open('property_codes.csv', 'r')
    reader = csv.reader(g)
    for row in reader:
        if(row[1] == acc_number):
            return row[0]
    g.close()
    return "No Property Code matches this account number"

def return_total_expense():
    global totalInvoiceExpense
    global numberOfInvoices 
    totalExpenseArr = [numberOfInvoices, totalInvoiceExpense]
    return totalExpenseArr

def rename(invoice, filename, accountNumber, buildingCode, issuer, invAmount, date):

    newName = ""
    newName = str(buildingCode) + " " + issuer + " " + str(accountNumber) + " " + "$" + str(invAmount) + " " + date.replace('/',"-") + ".pdf"

    

    thisFolder = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(thisFolder, os.path.join(folder_with_pdfs, filename))
    dst = folder_for_renamed_pdfs + "/" + newName


    print("Renaming")
    os.rename(src, dst)

def write_vendor_usage(csv, filename, tryBool):
    if(tryBool):
        csv.write("%s,%s,%s,%s,%s,%s,%s,%s\n"%(usage__buildingCode,usage__issuerAbbriviation, usage__accountNumber ,usage__charge,
                usage__meterNumber, usage__date, usage__usageAmount, usage__usageType))
    # else: 
    #     csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%('ERROR', filename,','MANUALLY WRITE DST FOR THIS INVOCIE','',
    #         '',"",'', '','',"",'ERROR '))













######################### OLD WAY OF WRITING TO CSV #############            
#       if(invoice.issuer == 'PSE&G'): 
#             invAmount = invoice.amount
#             if(hasattr(invoice, 'credit_bool')): #this is basically a boolean to see if the invoice is a credit invoice
#                 invAmount = 0 - invAmount
            
#             gasBool = True
#             tempDate = (str(invoice.date).split(' ')[0]).split('-')
#             adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
#             csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,,%s%s"%('INVH',invoice.invoice_number,adjDate,invAmount,
#                 accountNumber,"U",'PSEG', adjDate,adjDate,"1",",filenameYES\r"))
#             #DST Gas 
#             if(hasattr(invoice, 'gas_charge')):
#                 tempString = invoice.therms + " " + "Therms"
#                 csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-6000",
#                 tempString, invoice.gas_charge))
            
#             #DST Electric
#             if(hasattr(invoice, 'amount_total_electric') | hasattr(invoice, 'total_electric')):
#                 electric_charge = 0
#                 if(hasattr(invoice, "amount_total_electric")):
#                     electric_charge = invoice.amount_total_electric
#                 if(hasattr(invoice, "total_electric")):
#                     electric_charge = invoice.total_electric
#                     print(invoice.total_electric)
#                 electric_charge = str(electric_charge).replace(",","")
#                 #Parsing and reformatting
#                 kws = "".join(str(invoice.kws).split(','))
#                 meter = invoice.meter_date

#                 adjDate = str(meter.month) + "/" + str(meter.day) + "/" + str(meter.year)

#                 tempString =  " " + kws + " " + "KWHS"
#                 csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
#                 tempString, electric_charge))

#             #Other credits and Charges 
#             if(hasattr(invoice, 'other_charges')):
#                 adjDate = str(meter.month) + "/" + str(meter.day) + "/" + str(meter.year)

#                 otherCharge = "-" + invoice.other_charges
#                 otherCharge = otherCharge.replace(',','')
#                 print(otherCharge)
#                 tempString =  " " + kws + " " + "KWHS"
#                 csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
#                 "", otherCharge))
#             if(hasattr(invoice, 'electric_supply_name') & ~hasattr(invoice, 'electric_supply')):
#                 csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
#                 "", "Electric Supply Charge not found"))


        
#         #Republic Services CSV
#         if(invoice.issuer == 'Republic Service'):
#             tempDate = (str(invoice.date).split(' ')[0]).split('-')
#             adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
#             csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',invoice.invoice_number,adjDate,invoice.amount,
#                 accountNumber,"U",'REPSE', adjDate,adjDate,"1","YES\n"))
#             #DST Line 
#             csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
#                 "", invoice.amount))

            
            
#         #AC Electric
#         if(invoice.issuer == 'Atlantic City Electric'):
#             tempDate = (str(invoice.date).split(' ')[0]).split('-')
#             adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
#             csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',invoice.invoice_number,adjDate,invoice.amount,
#                 accountNumber,"U",'ACELE', adjDate,adjDate,"1","YES\n"))

#             #DST Line 
#             csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
#                 "", invoice.amount))


#         #American Water NJ 
#         if(invoice.issuer == 'American Water'):
#             tempDate = (str(invoice.date).split(' ')[0]).split('-')
#             adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
#             csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',invoice.invoice_number, adjDate,invoice.amount,
#                 njAccNumb,"U","NJAW", adjDate,adjDate,"1","YES\n"))
#             #DIST 5500-7000
#             csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-7000",
#                 "", invoice.amount))

        
#         #Comcast 
#         if(invoice.issuer == 'Comcast'):
#             tempDate = (str(invoice.date).split(' ')[0]).split('-')
#             adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
#             csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',accountNumber + adjDate,adjDate,invoice.amount,
#                 accountNumber,"U","COMCA", adjDate,adjDate,"1","YES\n"))
#             #DST Line Cable 
#             csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"6000-3300",
#                 "", invoice.amount))

#         #Verizon 
#         if(invoice.issuer == 'Verizon'):
            
            
#             if(isinstance(invoice.account_number, list)):
#                 accountNumber = str(invoice.account_number[0]).replace(" ","")

#             tempDate = (str(invoice.date).split(' ')[0]).split('-')
#             adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
#             csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH', accountNumber + adjDate,adjDate,invoice.amount,
#                 accountNumber,"U","VERIZ", adjDate,adjDate,"1","YES\n"))
#             #DST Line Cable
#             csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"6000-3300",
#                 "", invoice.amount))
        