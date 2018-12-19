#!/usr/bin/env python

import xml.etree.ElementTree as ET
import requests
import hashlib
import argparse
import re

pipe = ""
username = ""
password = ""
url = ""
xpathresponse = ""

def getAPIKey ():
    concatted = username+"_"+password
    m = hashlib.md5()
    m.update(concatted.encode('utf-8'))
    hashedcreds = m.hexdigest()

    host = re.findall('//(.*?)/', url)
    response = requests.get("http://"+host[0]+"/api/login/" + hashedcreds).content.decode(encoding='UTF-8',errors='strict')
    element = ET.fromstring(response)
    e = element.findall('.//OBJECT/PROPERTY[@name="response"]')

    sessionkey = e[0].text
    return sessionkey


def evalXpath (xpath):
    global xpathresponse
    if (len(xpathresponse)) < 1:
       element = ET.fromstring(makeGetRequest(url))
    else:
        element = ET.fromstring(xpathresponse)

    e = element.findall(xpath)
    return e

def makeGetRequest (url):
    global xpathresponse

    cookies = {
        'wbisessionkey': getAPIKey(),
    }
    xpathresponse = requests.get(url, cookies=cookies).content.decode(
        encoding='UTF-8', errors='strict')
    return xpathresponse

def removeChars (inputString):
        for char in inputString:
            if not char.isdigit() and not char.__contains__("."):
                inputString = inputString.replace(char, "")
        return inputString

def thresholdCheck (metricname,durableid, metric, warning, critical):
    metric = float(removeChars(metric))
    warning = float(warning)
    critical = float(critical)
    setmetrics(metricname,durableid, metric)
    if metric > warning and metric < critical:
        result = ("WARNING: " + durableid + " is above threshold: " + str(warning) + " (" + str(metric) + ") ")
    elif metric >= critical:
        result = ("CRITICAL: " + durableid + " is above threshold: " + str(critical) + "(" + str(metric) + ") ")
    elif metric < warning:
        result = ""
    else:
        result = ("UNKNOWN: " + durableid + " threshold: " + str(warning) + " (" +  str(metric) + ") ")
    return result

def thresholdCheckString (metricname, durableid, metric, verificationstring):
    setmetrics(metricname,durableid, metric)
    if metric != verificationstring:
        result = ("CRITICAL: "+durableid+" " + metric + " is NOT " + verificationstring +" ")
    else:
        result =""
    return result

def setmetrics (metricname,durableid, metric):
    global pipe
    pipe += durableid + "_"+metricname+ "=" + str(metric) + " "


def getList (metricname, durableid, warning, critical, id):
    durable_id = evalXpath(".//OBJECT/PROPERTY[@name=\""+id+"\"]")
    metric = evalXpath(".//OBJECT/PROPERTY[@name=\""+metricname+"\"]")
    result =""
    durableid_array = durableid.split(",")

    if not durableid == "all":
        index = 0
        for i in range (0, len(durable_id)):
            for durableid_single in durableid_array:
             if durable_id[i].text == durableid_single:
                index = i;
                if metric[index].text.isdigit() or str(metric[index].text)[0].isdigit():
                  result += (thresholdCheck(metricname,durable_id[index].text, metric[index].text, warning, critical))
                else:
                  result += thresholdCheckString(metricname,durable_id[index].text, metric[index].text, critical)
    else:
        for i in range (0, len(durable_id)):
            if metric[i].text.isdigit() or str(metric[i].text)[0].isdigit():
               result += (thresholdCheck(metricname,durable_id[i].text, metric[i].text, warning, critical))
            else:
               result+= thresholdCheckString(metricname,durable_id[i].text, metric[i].text, critical)

    if (len(result) < 1):
        result = "No problems - OK  "

    print(result + "| " + pipe)


    if "WARNING" in result:
        exit(2)
    elif "CRITICAL" in result:
        exit(3)
    elif "UNKNOWN" in result:
        exit(4)
    else:
        exit(1)

if __name__ == "__main__":
     parser = argparse.ArgumentParser(description='This is an HP MSA Plugin that uses the XML API to retrieve metrics')

     parser.add_argument("--url", help="API Url")
     parser.add_argument("--username", help="API username")
     parser.add_argument("--password", help="API password")
     parser.add_argument("--object_id", help="Identificator/Name of the object. For example; system name, durable-id, controller name etc.")
     parser.add_argument("--metric", help="The metric to retrieve from the API. For example iops.")
     parser.add_argument("--objects", help="You can either specify one, multiple (comma separated), or all (controllers, pools, enclosure-id etc.).")
     parser.add_argument("--warning", help="Warning Threshold (not needed for string verifications. E.g verify on \"OK\")")
     parser.add_argument("--critical", help="Critical Threshold")

     args = parser.parse_args()

     if not args.url or not args.username or not args.password or not args.metric or not args.objects or not args.warning:
         print("Arguments are mandatory")
         exit(1)


     username = args.username

     url = args.url

     password = args.password

     app =getList(args.metric,args.objects, args.warning,args.critical, args.object_id)
