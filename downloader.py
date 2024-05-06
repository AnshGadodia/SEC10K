from sec_edgar_downloader import Downloader
# from openai import OpenAI
import openai
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

openai.api_key = ""




tickers = ["GOOGL", "DIS", "GS"]

start_date = "1995-01-01"
end_date = "2024-04-01"

d1 = Downloader("Test", "ansh.gadodia@gmail.com")



for ticker in tickers: #downloads files from each ticker

    d1.get("10-K", ticker, after=start_date, before=end_date)

def riskProcess(text, company):
    
    #defined expressions for start and end of document
    docStartPattern = re.compile(r'<DOCUMENT>')
    docEndPattern = re.compile(r'</DOCUMENT')
    typePattern = re.compile(r'<TYPE>[^\n]+')

    #indices for start and end
    docStart = [x.end() for x in docStartPattern.finditer(text)]
    docEnd = [x.start() for x in docEndPattern.finditer(text)]
    docTypes = [x[len('<TYPE>'):] for x in typePattern.findall(text)]

    #get actual 10-K text
    doc = {}
    for docType, docS, docE in zip(docTypes, docStart, docEnd):
        if docType == '10-K':
            doc[docType] = text[docS:docE]

    #the section headers are normally formatted like this
    regex = re.compile(r'(>Item(\s|&#160;|&nbsp;)(1A|1B)\.{0,1})|(ITEM\s(1A|1B))')

    matches = regex.finditer(doc['10-K'])
    
    #make a data frame
    testDF = pd.DataFrame([(x.group(), x.start(), x.end()) for x in matches])
    testDF.columns = ['item', 'start', 'end']
    testDF['item'] = testDF.item.str.lower()

    #clean the frame
    testDF.replace('&#160;',' ',regex=True,inplace=True)
    testDF.replace('&nbsp;',' ',regex=True,inplace=True)
    testDF.replace(' ','',regex=True,inplace=True)
    testDF.replace('\.','',regex=True,inplace=True)
    testDF.replace('>','',regex=True,inplace=True)


    #sort the values, get the last one (there will be 2, and the first one is the link at the beginning)
    posDat = testDF.sort_values('start', ascending=True).drop_duplicates(subset=['item'], keep='last')

    posDat.set_index('item', inplace=True)

    #get raw text
    if 'item1a' in posDat.index:
        item1aRaw = doc['10-K'][posDat['start'].loc['item1a']:posDat['start'].loc['item1b']]
    else:
        return ""


    item1aContent = BeautifulSoup(item1aRaw, 'lxml')

    #get bolded content from this section, and get the actual text (no tags)
    boldTexts = item1aContent.find_all(style=lambda value: value and 'font-weight:bold' in value)
    boldContent = [text1.get_text("\n") for text1 in boldTexts]
    boldCombined = "\n\n".join(str(text2) for text2 in boldContent)

    # print(item1aContent.prettify()[:1000])
    # temp = item1aContent.get_text("\n\n")[:1500]
    # temp = item1aContent.get_text("\n\n")
    # print(boldCombined)
    # print(item1aContent.get_text("\n\n")[:1500])


    #summarize the content
    test_prompt = "These are Risk Factors that the company " + company + " predicts. Summarize the most important factors in 2 concise sentences: " + boldCombined
    test_message = {
        "role": "user",
        "content": test_prompt
    }

    messages = [test_message]

    testResponse = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    ret = testResponse.choices[0].message.content
    


    return ret


def stockProcess(text, company):

    #same cleaning as earlier method

    docStartPattern = re.compile(r'<DOCUMENT>')
    docEndPattern = re.compile(r'</DOCUMENT')
    typePattern = re.compile(r'<TYPE>[^\n]+')

    docStart = [x.end() for x in docStartPattern.finditer(text)]
    docEnd = [x.start() for x in docEndPattern.finditer(text)]
    docTypes = [x[len('<TYPE>'):] for x in typePattern.findall(text)]

    doc = {}
    for docType, docS, docE in zip(docTypes, docStart, docEnd):
        if docType == '10-K':
            doc[docType] = text[docS:docE]


    regex = re.compile(r'(>Item(\s|&#160;|&nbsp;)(5|6)\.{0,1})|(ITEM\s(5|6))')

    matches = regex.finditer(doc['10-K'])
    
    testDF = pd.DataFrame([(x.group(), x.start(), x.end()) for x in matches])
    testDF.columns = ['item', 'start', 'end']
    testDF['item'] = testDF.item.str.lower()

    testDF.replace('&#160;',' ',regex=True,inplace=True)
    testDF.replace('&nbsp;',' ',regex=True,inplace=True)
    testDF.replace(' ','',regex=True,inplace=True)
    testDF.replace('\.','',regex=True,inplace=True)
    testDF.replace('>','',regex=True,inplace=True)

    posDat = testDF.sort_values('start', ascending=True).drop_duplicates(subset=['item'], keep='last')

    posDat.set_index('item', inplace=True)

    if 'item5' in posDat.index and 'item6' in posDat.index:
        item5Raw = doc['10-K'][posDat['start'].loc['item5']:posDat['start'].loc['item6']]
    else:
        return ""

    item5Content = BeautifulSoup(item5Raw, 'lxml')
    temp = item5Content.get_text("\n\n")[:2000]

    # print(item1aContent.prettify()[:1000])
    # temp = item1aContent.get_text("\n\n")[:1500]
    # temp = item1aContent.get_text("\n\n")
    # print(boldCombined)
    # print(item1aContent.get_text("\n\n")[:1500])

    test_prompt = "This is stockholder information that the company " + company + " reports. Summarize the most important information that stockholders would care about in 2 concise sentences: " + temp
    test_message = {
        "role": "user",
        "content": test_prompt
    }

    messages = [test_message]

    testResponse = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    ret = testResponse.choices[0].message.content
    


    return ret

def businessProcess(text, company):

    #same cleaning as earlier method

    docStartPattern = re.compile(r'<DOCUMENT>')
    docEndPattern = re.compile(r'</DOCUMENT')
    typePattern = re.compile(r'<TYPE>[^\n]+')

    docStart = [x.end() for x in docStartPattern.finditer(text)]
    docEnd = [x.start() for x in docEndPattern.finditer(text)]
    docTypes = [x[len('<TYPE>'):] for x in typePattern.findall(text)]

    doc = {}
    for docType, docS, docE in zip(docTypes, docStart, docEnd):
        if docType == '10-K':
            doc[docType] = text[docS:docE]


    regex = re.compile(r'(>Item(\s|&#160;|&nbsp;)(1|1A|7|8)\.{0,1})|(ITEM\s(1|1A|7|8))')

    matches = regex.finditer(doc['10-K'])
    
    testDF = pd.DataFrame([(x.group(), x.start(), x.end()) for x in matches])
    testDF.columns = ['item', 'start', 'end']
    testDF['item'] = testDF.item.str.lower()

    testDF.replace('&#160;',' ',regex=True,inplace=True)
    testDF.replace('&nbsp;',' ',regex=True,inplace=True)
    testDF.replace(' ','',regex=True,inplace=True)
    testDF.replace('\.','',regex=True,inplace=True)
    testDF.replace('>','',regex=True,inplace=True)

    posDat = testDF.sort_values('start', ascending=True).drop_duplicates(subset=['item'], keep='last')

    posDat.set_index('item', inplace=True)

    if 'item1' in posDat.index and 'item1a' in posDat.index:
        item1Raw = doc['10-K'][posDat['start'].loc['item1']:posDat['start'].loc['item1a']]
    else:
        return ""
    # item7Raw = doc['10-K'][posDat['start'].loc['item7']:posDat['start'].loc['item7a']]
    # item7aRaw = doc['10-K'][posDat['start'].loc['item7a']:posDat['start'].loc['item8']]

    item1Content = BeautifulSoup(item1Raw, 'lxml')
    boldTexts = item1Content.find_all(style=lambda value: value and 'font-weight:bold' in value)
    boldContent = [text1.get_text("\n") for text1 in boldTexts]
    boldCombined = "\n\n".join(str(text2) for text2 in boldContent)

    temp = item1Content.get_text("\n\n")[:1500]
    temp += boldCombined

    # print(item1aContent.prettify()[:1000])
    # temp = item1aContent.get_text("\n\n")[:1500]
    # temp = item1aContent.get_text("\n\n")
    # print(boldCombined)
    # print(item1aContent.get_text("\n\n")[:1500])

    test_prompt = "These are general business operations about the company " + company + ". Summarize the most important data in 2 concise sentences: " + temp
    test_message = {
        "role": "user",
        "content": test_prompt
    }

    messages = [test_message]

    testResponse = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    ret = testResponse.choices[0].message.content
    


    return ret

#loop through each file, add the LLM summary output to the dictionary
company_risks = {}
for company_dir in os.listdir("sec-edgar-filings"):
    if not company_dir.startswith('.'):
        company_risks[company_dir] = ""
        #now company_risks contains mapping from company name to text
        for fdir in os.listdir(os.path.join("sec-edgar-filings", company_dir, "10-K")):
            if not fdir.startswith('.'):
                for filename in os.listdir(os.path.join("sec-edgar-filings", company_dir, "10-K", fdir)):
                    with open(os.path.join("sec-edgar-filings", company_dir, "10-K", fdir, filename), 'r', encoding='utf-8') as file:
                        # print("filename " + os.path.join("sec-edgar-filings", company_dir, "10-K", fdir, filename))
                        company_risks[company_dir] += riskProcess(file.read(), company_dir)
                        # exit()

#further summarize the output
for company_dir in os.listdir("sec-edgar-filings"):
    if not company_dir.startswith('.'):
        test_prompt = "These are summaries of Risk Factors that the company " + company_dir + " predicts each year. Summarize these factors in 2 concise sentences: " + company_risks[company_dir]
        test_message = {
            "role": "user",
            "content": test_prompt
        }

        messages = [test_message]

        testResponse = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        company_risks[company_dir] = testResponse.choices[0].message.content
        print(company_dir + " risk factors: " + company_risks[company_dir])

#loop through each file, add the LLM summary output to the dictionary
stockInfo = {}
for company_dir in os.listdir("sec-edgar-filings"):
    if not company_dir.startswith('.'):
        stockInfo[company_dir] = ""
        #now company_risks contains mapping from company name to text
        for fdir in os.listdir(os.path.join("sec-edgar-filings", company_dir, "10-K")):
            if not fdir.startswith('.'):
                for filename in os.listdir(os.path.join("sec-edgar-filings", company_dir, "10-K", fdir)):
                    with open(os.path.join("sec-edgar-filings", company_dir, "10-K", fdir, filename), 'r', encoding='utf-8') as file:
                        # print("filename " + os.path.join("sec-edgar-filings", company_dir, "10-K", fdir, filename))
                        stockInfo[company_dir] += stockProcess(file.read(), company_dir)
                        # exit()

#further summarize the output
for company_dir in os.listdir("sec-edgar-filings"):
    if not company_dir.startswith('.'):
        test_prompt = "These are summaries of stockholder information that the company " + company_dir + " reports each year. Summarize these in 2 concise sentences (for statistics, like number of common stock holders for example, use the most recent numbers): " + stockInfo[company_dir]
        test_message = {
            "role": "user",
            "content": test_prompt
        }

        messages = [test_message]

        testResponse = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        stockInfo[company_dir] = testResponse.choices[0].message.content
        print(company_dir + " stockholder information: " + stockInfo[company_dir])

#loop through each file, add the LLM summary output to the dictionary
businessInfo = {}
for company_dir in os.listdir("sec-edgar-filings"):
    if not company_dir.startswith('.'):
        businessInfo[company_dir] = ""
        #now company_risks contains mapping from company name to text
        for fdir in os.listdir(os.path.join("sec-edgar-filings", company_dir, "10-K")):
            if not fdir.startswith('.'):
                for filename in os.listdir(os.path.join("sec-edgar-filings", company_dir, "10-K", fdir)):
                    with open(os.path.join("sec-edgar-filings", company_dir, "10-K", fdir, filename), 'r', encoding='utf-8') as file:
                        # print("filename " + os.path.join("sec-edgar-filings", company_dir, "10-K", fdir, filename))
                        businessInfo[company_dir] += businessProcess(file.read(), company_dir)
                        # exit()

#further summarize the output
for company_dir in os.listdir("sec-edgar-filings"):
    if not company_dir.startswith('.'):
        test_prompt = "These are summaries of general business operations that the company " + company_dir + " reports each year. Summarize these in 2 concise sentences: " + businessInfo[company_dir]
        test_message = {
            "role": "user",
            "content": test_prompt
        }

        messages = [test_message]

        testResponse = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        businessInfo[company_dir] = testResponse.choices[0].message.content
        print(company_dir + " general business information: " + businessInfo[company_dir])


app = Flask(__name__)
# CORS(app)
# @app.route('/get_riskdata', methods = ['GET'])
# def get_riskdata():
#     ticker = request.args.get('ticker')
#     if ticker in company_risks:
#         response = jsonify(company_risks[ticker])
#         response.headers.add("Access-Control-Allow-Origin", "*")
#         return response
#     else:
#         return jsonify({"error": "Company not found"}), 404

# @app.route('/get_stockdata', methods = ['GET'])
# def get_stockdata():
#     ticker = request.args.get('ticker')
#     if ticker in stockInfo:
#         response = jsonify(stockInfo[ticker])
#         response.headers.add("Access-Control-Allow-Origin", "*")
#         return response
#     else:
#         return jsonify({"error": "Company not found"}), 404

# @app.route('/get_businessdata', methods = ['GET'])
# def get_businessdata():
#     ticker = request.args.get('ticker')
#     if ticker in businessInfo:
#         response = jsonify(businessInfo[ticker])
#         response.headers.add("Access-Control-Allow-Origin", "*")
#         return response
#     else:
#         return jsonify({"error": "Company not found"}), 404
@app.route('/')
def index():
    return render_template('visualization.html', company_risks=company_risks, stockInfo=stockInfo, businessInfo=businessInfo)

if __name__ == '__main__':
    app.run(debug=True)
