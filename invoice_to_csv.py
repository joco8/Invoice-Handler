#invoice_to_csv

from invoice2data import extract_data
from invoice2data.extract.loader import read_templates
import csv
import os
from datetime import datetime
import pandas as pd 

numberOfInvoices = 0
totalInvoiceExpense = 0

#Takes a single invoice adds info to an existing CSV file (csv) 
def write_to_csv(invoice, csv, filename):
    try:

        if(invoice.issuer == "null"):
            csv.write("%s,%s\n"%("Could not parse pdf", invoice.filename))
            return

        #remove blank space from account number 
        accountNumber = ''
        if(str(invoice.account_number).endswith(' ')):
            accountNumber = str(invoice.account_number)[:-1]
        else:
            accountNumber = str(invoice.account_number)
        
        #grab building code 

        buidlingCode = building_code(accountNumber)
        if(invoice.issuer == 'Verizon'):
            print(invoice.primary_phone)
            phone = invoice.primary_phone
            if(isinstance(phone, list)):
                phone = invoice.primary_phone[0] 
            buidlingCode = building_code(str(phone).replace(" ",""))
        if(invoice.issuer == "American Water"):
            accNumber = (invoice.account_number.split("-"))[1]
            buidlingCode = building_code(str(accNumber))
            

        ## PSEG CSV ##
        gasBool = False
        if(invoice.issuer == 'PSE&G'): 
            invAmount = invoice.amount
            if(hasattr(invoice, 'credit_bool')): #this is basically a boolean to see if the invoice is a credit invoice
                invAmount = 0 - invAmount
            
            gasBool = True
            tempDate = (str(invoice.date).split(' ')[0]).split('-')
            adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',invoice.invoice_number,adjDate,invAmount,
                accountNumber,"U",'PSEG', adjDate,adjDate,"1","YES\n"))
            #DST Gas 
            if(hasattr(invoice, 'gas_charge')):
                tempString = adjDate + " " + invoice.therms + " " + "Therms"
                csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-6000",
                tempString, invoice.gas_charge))
            
            #DST Electric
            if(hasattr(invoice, 'amount_total_electric') | hasattr(invoice, 'total_electric')):
                electric_charge = 0
                if(hasattr(invoice, "amount_total_electric")):
                    electric_charge = invoice.amount_total_electric
                if(hasattr(invoice, "total_electric")):
                    electric_charge = invoice.total_electric
                    print(invoice.total_electric)
                electric_charge = str(electric_charge).replace(",","")
                #Parsing and reformatting
                kws = "".join(str(invoice.kws).split(','))
                meter = invoice.meter_date

                adjDate = str(meter.month) + "/" + str(meter.day) + "/" + str(meter.year)

                tempString =  " " + kws + " " + "KWHS"
                csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
                tempString, electric_charge))

            #Other credits and Charges 
            if(hasattr(invoice, 'other_charges')):
                adjDate = str(meter.month) + "/" + str(meter.day) + "/" + str(meter.year)

                otherCharge = "-" + invoice.other_charges
                otherCharge = otherCharge.replace(',','')
                print(otherCharge)
                tempString =  " " + kws + " " + "KWHS"
                csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
                "", otherCharge))
            if(hasattr(invoice, 'electric_supply_name') & ~hasattr(invoice, 'electric_supply')):
                csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
                "", "Electric Supply Charge not found"))


        
        #Republic Services CSV
        if(invoice.issuer == 'Republic Service'):
            tempDate = (str(invoice.date).split(' ')[0]).split('-')
            adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',invoice.invoice_number,adjDate,invoice.amount,
                accountNumber,"U",'REPSE', adjDate,adjDate,"1","YES\n"))
            #DST Line 
            csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
                "", invoice.amount))

            
            
        #AC Electric
        if(invoice.issuer == 'Atlantic City Electric'):
            tempDate = (str(invoice.date).split(' ')[0]).split('-')
            adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',invoice.invoice_number,adjDate,invoice.amount,
                accountNumber,"U",'ACELE', adjDate,adjDate,"1","YES\n"))

            #DST Line 
            csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-5000",
                "", invoice.amount))


        #American Water NJ 
        if(invoice.issuer == 'American Water'):
            tempDate = (str(invoice.date).split(' ')[0]).split('-')
            adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',invoice.invoice_number,adjDate,invoice.amount,
                accountNumber,"U","NJAW", adjDate,adjDate,"1","YES\n"))
            #DIST 5500-7000
            csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"5500-7000",
                "", invoice.amount))

        
        #Comcast 
        if(invoice.issuer == 'Comcast'):
            tempDate = (str(invoice.date).split(' ')[0]).split('-')
            adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH',accountNumber + adjDate,adjDate,invoice.amount,
                accountNumber,"U","COMCA", adjDate,adjDate,"1","YES\n"))
            #DST Line Cable 
            csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"6000-3300",
                "", invoice.amount))

        #Verizon 
        if(invoice.issuer == 'Verizon'):
            
            
            if(isinstance(invoice.account_number, list)):
                accountNumber = str(invoice.account_number[0]).replace(" ","")

            tempDate = (str(invoice.date).split(' ')[0]).split('-')
            adjDate = tempDate[1] + "/" + tempDate[2] + "/" + tempDate[0]
            csv.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%('INVH', accountNumber + adjDate,adjDate,invoice.amount,
                accountNumber,"U","VERIZ", adjDate,adjDate,"1","YES\n"))
            #DST Line Cable
            csv.write("%s,%s,%s,%s,%s\n"%("DIST",buidlingCode,"6000-3300",
                "", invoice.amount))
    except:
        accNumber = invoice.account_number
        csv.write("%s,%s,%s,%s,%s\n"%('Error in File', filename, invoice.issuer, accNumber, "Please manually fill in the info for this file"))
        pass


    #Add to total expenses 
    global totalInvoiceExpense
    totalInvoiceExpense += invoice.amount
    #add to running invoice count
    global numberOfInvoices 
    numberOfInvoices += 1


#Grab Building Code 
def building_code(acc_number):
    
    #open reference doc with building codes
    g = open('property_codes.csv', 'r')
    reader = csv.reader(g)
    for row in reader:
        if(row[1] == acc_number):
            return row[0]
    g.close()
    return "No Property Code matches this account number"
            
