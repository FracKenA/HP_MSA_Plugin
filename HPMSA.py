#!/usr/bin/env python3

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
object_basetype = ""
debug = ""
ignore = ""

def getAPIKey ():
    concatted = username+"_"+password
    m = hashlib.md5()
    m.update(concatted.encode('utf-8'))
    hashedcreds = m.hexdigest()

    host = re.findall('//(.*?)/', url)


    if "https" in url:
        requests.packages.urllib3.disable_warnings()
        response = requests.get("https://" + host[0] + "/api/login/" + hashedcreds, verify=False).content.decode(encoding='UTF-8',
                                                                                                  errors='strict')
    else:
        response = requests.get("http://" + host[0] + "/api/login/" + hashedcreds).content.decode(encoding='UTF-8',
                                                                                                   errors='strict')
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
    requests.packages.urllib3.disable_warnings()
    xpathresponse = requests.get(url, cookies=cookies, verify=False).content.decode(
        encoding='UTF-8', errors='strict')

    return xpathresponse

def removeChars (inputString):
        for char in inputString:
            if not char.isdigit() and not char.__contains__("."):
                inputString = inputString.replace(char, "")
        return inputString

def thresholdCheck (metricname,devices, metric, warning, critical):
    metric = float(removeChars(metric))
    warning = float(warning)
    critical = float(critical)
    setmetrics(metricname,devices, metric)

    if metric >= critical:
        result = ("CRITICAL: " + devices + " "+metricname+ " is above threshold: " + str(critical) + "(" + str(metric) + ") ")
    elif metric >= warning:
        result = ("WARNING: " + devices + " "+metricname+ " is above threshold: " + str(warning) + " (" + str(metric) + ") ")
    elif metric < critical or metric < warning:
        result = ""
    else:
        result = ("UNKNOWN: " + devices + " "+metricname+ " threshold: " + str(warning) + " (" +  str(metric) + ") ")
    return result

def thresholdCheckString (metricname, devices, metric, verificationstring):
    setmetrics(metricname,devices, metric)

    if metric != verificationstring and metric != ignore:
        result = ("CRITICAL: "+devices+ " "+metricname+" " + metric + " is NOT " + verificationstring +" ")
    else:
        result =""
    return result

def setmetrics (metricname,devices, metric):
    global pipe
    pipe += devices + "."+metricname+ "=" + str(metric) + " "

def countSnapshots (warning, critical):
    amount = evalXpath('.//OBJECT[@name="snapshot"]')
    snapshots = len(amount)
    if snapshots <= int(critical):
        result = ("CRITICAL! The amount of snapshots: " + str(snapshots) +" is below critical threshold: " + critical)
    elif snapshots <= int(warning):
        result = ("WARNING! The amount of snapshots: " + str(snapshots) +" is below warning threshold: " + warning)
    else:
        result = "OK! The amount of snapshots: " + str(snapshots) + ". Applied thresholds are: critical: " + str(critical) + " warning: " +str(warning)

    print(result + " | amountofsnapshots=" + str(snapshots))

    if "CRITICAL" in result:
        exit(2)
    elif "WARNING" in result:
        exit(1)
    else:
        exit(0)


def calculateDifference (warning, critical):
    allocated_size = removeChars(evalXpath(".//OBJECT/PROPERTY[@name=\"allocated-size\"]")[0].text)
    available_size = removeChars(evalXpath(".//OBJECT/PROPERTY[@name=\"available-size\"]")[0].text)

    allocated_size = float(allocated_size)

    available_size = float(available_size)

    #print("allocated: " + str(allocated_size))
    #print("available: " + str(available_size))

    allocatedSizeInGb = allocated_size * 1000

    usedGb = allocatedSizeInGb - available_size
    poolUsage = usedGb / allocatedSizeInGb *100

    poolUsage = "{0:.1f}".format(poolUsage)

    if float(poolUsage) >= float(critical):
        result = ("CRITICAL! Pool usage is: " + str(poolUsage) + " Critical threshold: " + str(critical))
    elif float(poolUsage) >= float(warning):
        result = ("WARNING! Pool usage is: " + str(poolUsage) + " Warning threshold: " + str(warning))
    else:
        result = "OK! Pool usage is: " + str(poolUsage)

    print(result + " | poolUsage="+str(poolUsage))

    if "CRITICAL" in result:
        exit(2)
    elif "WARNING" in result:
        exit(1)
    else:
        exit(0)

def getList (metricname, devices, warning, critical, devicename):

    if object_basetype is None:
        devicename_id = evalXpath(".//OBJECT/PROPERTY[@name=\"" + devicename + "\"]")
        metric = evalXpath(".//OBJECT/PROPERTY[@name=\"" + metricname + "\"]")

    else:
        devicename_id = evalXpath(".//OBJECT[@name=\""+object_basetype+"\"]/PROPERTY[@name=\"" + devicename + "\"]")
        metric = evalXpath(".//OBJECT[@name=\""+object_basetype+"\"]/PROPERTY[@name=\"" + metricname + "\"]")

    result =""
    devices_array = devices.split(",")

    if debug is not None:
        print(xpathresponse)

    if len(devicename_id) < 1:
        print("Cound not find device(s) " + devicename)
        exit(1)
    if len(metric) < 1:
        print("Cound not find metric " + metricname)
        exit(1)

    if not devices == "all":
        index = 0
        for i in range (0, len(devicename_id)):
            for devices_single in devices_array:
             if devicename_id[i].text == devices_single:
                index = i;
                if metric[index].text.isdigit() or str(metric[index].text)[0].isdigit():
                  result += (thresholdCheck(metricname,str(devicename_id[index].text).replace(" ", ""), metric[index].text, warning, critical))
                else:
                  result += thresholdCheckString(metricname,str(devicename_id[index].text).replace(" ", ""), metric[index].text, critical)
    else:
        for i in range (0, len(devicename_id)):
            if metric[i].text.isdigit() or str(metric[i].text)[0].isdigit():
               result += (thresholdCheck(metricname,str(devicename_id[i].text).replace(" ", ""), metric[i].text, warning, critical))
            else:
               result+= thresholdCheckString(metricname,str(devicename_id[i].text).replace(" ", ""), metric[i].text, critical)

    if (len(result) < 1):
        result = "No problems - OK  "

    print(result + "| " + pipe)


    if "UNKNOWN" in result:
        exit(3)
    elif "CRITICAL" in result:
        exit(2)
    elif "WARNING" in result:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
     parser = argparse.ArgumentParser(description='This is an HP MSA Plugin that uses the XML API to retrieve metrics')

     parser.add_argument("--url", help="API Url")
     parser.add_argument("--username", help="API username")
     parser.add_argument("--password", help="API password")
     parser.add_argument("--object_basetype", help="(Optional) Specify an object basetype in the XML. There are some cases where you have an object under another object.")
     parser.add_argument("--devicename", help="Identificator/Name of the object. For example; system name, durable-id, controller name etc.")
     parser.add_argument("--metric", help="The metric to retrieve from the API. For example iops.")
     parser.add_argument("--devices", help="You can either specify one, multiple (comma separated), or all (fan1, fan2, fan3 or \"all\" fans).")
     parser.add_argument("--warning", help="Warning Threshold (not needed for string verifications. E.g verify on \"OK\")")
     parser.add_argument("--critical", help="Critical Threshold")
     parser.add_argument("--ignore", help="(Optional) Ignore a certain keyword in string verifications.")
     parser.add_argument("--debug", help="(Optional) Prints the response from the XML API")

     args = parser.parse_args()


     if not args.url or not args.username or not args.password or not args.devicename or not args.metric or not args.devices or not args.critical:
         if "count" not in args.metric and "difference" not in args.metric:
             print("Arguments URL, username, password, devicename, metric, devices and critical are mandatory")
             exit(1)

     if args.ignore is not None:
         ignore = args.ignore
     debug = args.debug
     object_basetype = args.object_basetype
     username = args.username
     url = args.url
     password = args.password

     if "count" in args.metric:
         countSnapshots(args.warning,args.critical)

     if "difference" in args.metric:
         calculateDifference(args.warning, args.critical)


     app =getList(args.metric,args.devices, args.warning,args.critical, args.devicename)
