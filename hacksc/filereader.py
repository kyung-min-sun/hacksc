import os
from PyPDF2 import PdfFileReader
from mechanize import Browser
from bs4 import BeautifulSoup
import requests
import json
import re
import random
import string

# creates a new USCIS account
def setupUSCIS(immInfo):
    br = Browser()
    br.addheaders = [('User-Agent', "Mozilla/5.0 \
    (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko)\
     Chrome/79.0.3945.130 Safari/537.36")]

    # opens to the sign up page
    br.open('https://egov.uscis.gov/casestatus/disclaimer.do')
    br.follow_link(text="ACCEPT")

    # clicks next (nothing on page 1)
    br.select_form("signUpForm")
    br.submit()

    #fills in the signup sheet
    br.select_form("signUpForm")
    br.form["userSubType"] = ["1"]
    br.form["firstName"] = immInfo["firstName"]
    br.form["lastName"] = immInfo["lastName"]
    br.form["country"] = immInfo["country"]
    br.form["city"] = immInfo["city"]
    br.form["state"] = immInfo["state"]
    br.form["zipCode"] = immInfo["zipcode"]
    br.form["email"] =  immInfo["email"]
    br.form["phone"] =  immInfo["phone"]
    br.form["language"] = immInfo["language"]
    br.submit()

    #generates random username and password
    br.select_form("signUpForm")
    br.form["userId"] = immInfo["username"];
    br.form["password"] = immInfo["password"];
    br.form["confirmPassword"] = immInfo["password"];

    #counts each question answered
    counter = 1
    for i in range(1, 13):
        if counter == 5:
            break
        #checks if the answer exists
        if immInfo["answer" + str(i)]:
            br.form["question" + str(counter)] = str(i)
            br.form["answer" + str(counter)] = immInfo["answer" + str(i)]
            counter+=1

    #submits form
    br.submit()


def login(username, password):
    br = Browser()
    br.open('https://egov.uscis.gov/casestatus/displayLogon.do')
    br.select_form("logonForm")
    br.form["username"] = username
    br.form["password"] = password
    br.submit()
    return br


def extractCase(br, receipt_number):
    #follow link + extract the next case's website
    response1 = br.follow_link(text=receipt_number)
    r = requests.get(response1.geturl())
    data = r.text
    j = BeautifulSoup(data, features="lxml")

    #grab the first two setences of the statement
    status = re.findall(r'<h1>([A-Za-z\s]*)</h1>\n.*<p>([^.]+)\.([^.]+)',
    data, re.MULTILINE)

    #return the abbreviated and 2 sentence case status
    short = status[0][0]
    long = status[0][1] + status[0][2]
    return (short, long)


def addCase(br, receipt_number):
    br.select_form("caseStatusForm")
    br.form["appReceiptNum"] = receipt_number
    br.submit()


def updateCases(immInfo):
    br = login(immInfo["username"], immInfo["password"])
    for receipt in immInfo["receipt_number"]:
        if receipt not in immInfo["added_receipts"]:
            addCase(br, receipt)
            immInfo["added_receipts"].append(receipt)
        updates = extractCase(br, receipt)
    return updates


def randomStringDigits(stringLength=10):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def extractPDFinfo(filename, ):
    file = PdfFileReader(filename)
    immInfo = file.getFormTextFields()

    #creates a random user-password generator
    immInfo["username"] = randomStringDigits()
    immInfo["password"] = randomStringDigits()

    #two lists of 1. total receipts and 2. receipts added to website
    immInfo["receipt_number"] = [immInfo["receipt_number"]]
    immInfo["added_receipts"] = []

    return immInfo

def updateInfo(immInfo, element, updated):
    immInfo[element] = updated

def addReceiptNumber(immInfo, receipt_number):
    immInfo["receipt_number"].append(receipt_number)


def main():
    cwd = os.getcwd()
    profiles = {}
    for (dirpath, dirnames, filenames) in os.walk(cwd):
        for filename in filenames:
            if filename.endswith('.pdf'):
                immInfo = extractPDFinfo(filename)
                profiles[immInfo["firstName"] + immInfo["lastName"]] = immInfo

    for immigrant in profiles:
        setupUSCIS(immigrant)
        immInfo["caseStatus"] = updateCases(immigrant)


main()



# Questions to ask
# <option value="10">In what city was your first job?</option>
# <option value="3">In what city were you born?</option>
# <option value="12">What is your father’s middle name?</option>
# <option value="9">What is your favorite animal?</option>
# <option value="5">What is your favorite movie?</option>
# <option value="2">What is your favorite sport?</option>
# <option value="11">What is your mother’s maiden name?</option>
# <option value="8">What is your oldest child’s middle name?</option>
# <option value="7">What was the color of your first car?</option>
# <option value="1">What was the name of your first pet?</option>
# <option value="6">What year did you get married?</option>
# <option value="4">What year did you graduate from high school?</option></select>