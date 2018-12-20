#!/usr/bin/env python

import xml.etree.ElementTree as ET
import requests
import hashlib
import argparse
import re

pipe = ""
username = ""
password = ""
xpathresponse = None
object_basetype = ""
debug = ""


def getAPIKey (url):
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


def evalXpath (url,xpath, type):
    global  xpathresponse
    if type is not None:
        element = ET.fromstring(xpathresponse)

    else:
        element = ET.fromstring(makeGetRequest(url))

    e = element.findall(xpath)
    return e

def makeGetRequest (url):
    global xpathresponse
    cookies = {
            'wbisessionkey': getAPIKey(url),
        }

    xpathresponse = requests.get(url, cookies=cookies).content.decode(
        encoding='UTF-8', errors='strict')
    return xpathresponse

def removeChars (inputString):
        for char in inputString:
            if not char.isdigit() and not char.__contains__("."):
                inputString = inputString.replace(char, "")
        return inputString

def thresholdCheck (urls,metricname,devices, metric, warning, critical):
    metric = float(removeChars(metric))
    warning = float(warning)
    critical = float(critical)
    host = re.findall('//(.*?)/', urls)
    setmetrics(host[0],metricname,devices, metric)
    if metric > warning and metric <= critical:
        result = ("WARNING: " + devices + " "+metricname+ ":"+host[0]+ " is above threshold: " + str(warning) + " (" + str(metric) + ") ")
    elif metric > critical:
        result = ("CRITICAL: " + devices + " "+metricname+":"+host[0]+  " is above threshold: " + str(critical) + "(" + str(metric) + ") ")
    elif metric < critical or metric < warning:
        result = ""
    else:
        result = ("UNKNOWN: " + devices + " "+metricname+":"+host[0]+  " threshold: " + str(warning) + " (" +  str(metric) + ") ")
    return result

def thresholdCheckString (urls,metricname, devices, metric, verificationstring):
    host = re.findall('//(.*?)/', urls)
    setmetrics(host[0],metricname,devices, metric)
    if metric != verificationstring:
        result = ("CRITICAL: "+devices+ " "+metricname+":"+host[0]+ " " + metric + " is NOT " + verificationstring +" ")
    else:
        result =""
    return result

def setmetrics (urls,metricname,devices, metric):
    global pipe
    pipe += urls+":"+devices + "."+metricname+ "=" + str(metric) + " "


def getList (HA, HB, metricname, devices, warning, critical, devicename):


    urls = list()
    urls.append(HA)
    if HB is not None:
       urls.append(HB)

    result = ""

    for j in range(0, len(urls)):
        if object_basetype is None:
            devicename_id = evalXpath(urls[j],".//OBJECT/PROPERTY[@name=\"" + devicename + "\"]", None)
            metric = evalXpath(urls[j],".//OBJECT/PROPERTY[@name=\"" + metricname + "\"]", "metric")

        else:
            devicename_id = evalXpath(urls[j],".//OBJECT[@name=\"" + object_basetype + "\"]/PROPERTY[@name=\"" + devicename + "\"]", None)
            metric = evalXpath(urls[j],".//OBJECT[@name=\"" + object_basetype + "\"]/PROPERTY[@name=\"" + metricname + "\"]", "metric")


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
            for i in range(0, len(devicename_id)):
                for devices_single in devices_array:
                    if devicename_id[i].text == devices_single:
                        index = i;
                        if metric[index].text.isdigit() or str(metric[index].text)[0].isdigit():
                            result += (thresholdCheck(urls[j],metricname, str(devicename_id[index].text).replace(" ", ""),
                                                      metric[index].text, warning, critical))
                        else:
                            result += thresholdCheckString(urls[j],metricname, str(devicename_id[index].text).replace(" ", ""),
                                                           metric[index].text, critical)
        else:
            for i in range(0, len(devicename_id)):
                if metric[i].text.isdigit() or str(metric[i].text)[0].isdigit():
                    result += (thresholdCheck(urls[j], metricname, str(devicename_id[i].text).replace(" ", ""),metric[i].text, warning, critical))
                else:
                    result += thresholdCheckString(urls[j],metricname, str(devicename_id[i].text).replace(" ", ""),metric[i].text, critical)



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

     parser.add_argument("--HA", help="API Url 1")
     parser.add_argument("--HB", help="API Url 2")
     parser.add_argument("--username", help="API username")
     parser.add_argument("--password", help="API password")
     parser.add_argument("--object_basetype", help="(Optional) Specify an object basetype in the XML. There are some cases where you have an object under another object.")
     parser.add_argument("--devicename", help="Identificator/Name of the object. For example; system name, durable-id, controller name etc.")
     parser.add_argument("--metric", help="The metric to retrieve from the API. For example iops.")
     parser.add_argument("--devices", help="You can either specify one, multiple (comma separated), or all (fan1, fan2, fan3 or \"all\" fans).")
     parser.add_argument("--warning", help="Warning Threshold (not needed for string verifications. E.g verify on \"OK\")")
     parser.add_argument("--critical", help="Critical Threshold")
     parser.add_argument("--debug", help="(Optional) Prints the response from the XML API")



     args = parser.parse_args()

     if not args.HA or not args.username or not args.password or not args.devicename or not args.metric or not args.devices or not args.critical:
         print("Arguments HA, username, password, devicename, metric, devices and critical are mandatory")
         exit(1)

     debug = args.debug
     object_basetype = args.object_basetype
     username = args.username
     HA = args.HA
     HB = args.HB
     password = args.password
     app =getList(args.HA, args.HB, args.metric,args.devices, args.warning,args.critical, args.devicename)
