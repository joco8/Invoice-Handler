#invoice_manipulation 

from invoice2data import extract_data
from invoice2data.extract.loader import read_templates
import csv
import os
from datetime import datetime
import pandas as pd 


class invoice: 
    def __init__(self, invDirectory, filename):
        templates = read_templates('tplf')
        pdfFile = invDirectory + '/' + filename
        result = extract_data(pdfFile, templates=templates)
        print(result)
        print(filename)
        if(result): 
            for item in result.keys():
                self.__setattr__(item, result[item]) 
        else:
            print()
            print()
            print()
            self.__setattr__("issuer", "null")
            self.__setattr__("filename", filename)
        # if(hasattr(self, "amount_total_electric")):
        #     if(hasattr(self, "total_electric")):
        #         print("yeeeeeeeee e e e e e e e t"+ self.total_electric)
        #     else:
        #         print("Got  aaaa    a a a a a a a  a a a a a  a    a a a a a a problem?")
           
#print(invoice('PSEG_invoices', 'ech 2.pdf').issuer)
