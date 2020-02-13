import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time 
import datetime
import os 
import zipfile
import requests
from bs4 import BeautifulSoup
import json
import platform 
import numpy as np
import random
import csv
time_and_url = [""]
if os.path.isfile("raw-xbrl/2020-01-29-2714.html") == True:
	with open ("raw-xbrl/2020-01-29-2714.html", "r") as f:
		html = BeautifulSoup(f.read(),  "html.parser")
	title = html.find("ix:nonnumeric", {"name":"tse-ed-t:DocumentName"}).parent.text
	print (title)
	companyname = html.find("ix:nonnumeric", {"name":"tse-ed-t:CompanyName"}).text
	pure = html.find_all("ix:nonfraction", {"name":"tse-ed-t:NetIncomePerShare"}) # Earnings per share 
	modified = html.find_all("ix:nonfraction" ,{"name":"tse-ed-t:DilutedNetIncomePerShare"}) # adjusted to the number after issuing more stocks if there was any
	dividend = html.find_all("ix:nonfraction" ,{"name":"tse-ed-t:DividendPerShare"}) # adjusted to the number after issuing more stocks if there was any
	newinfo = html.find("ix:nonnumeric" ,{"name":"tse-ed-t:CorrectionOfConsolidatedFinancialForecastInThisQuarter"})
	divi_newinfo = html.find("ix:nonnumeric" ,{"name":"tse-ed-t:CorrectionOfDividendForecastInThisQuarter"})