#import quandl
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time 
import datetime
import os.path
import requests
from bs4 import BeautifulSoup
import json


#quandl.ApiConfig.api_key = "UKv2WEbL4aEsPygasKfq"
#data = quandl.get('TSE/6758')
#data [:5]

code = 1301
year = 2019


"""
def kessan(code, year):
	ke3dic = {}
	path = "/Users/okamotohikari/scripts/stock/20191231f.xls"
	k3sheet = pd.read_excel(path, sheet_name="Sheet1")
	company = k3sheet.loc[k3sheet["証券コード"] == code]
	for qt in company:
		if str(year) not in qt["情報公開又は更新日"]:
			continue
		
		if not qt["希薄化後一株当り純利益"].isnull:
			eps = qt["希薄化後一株当り純利益"]  #earnings per share
		else:
			eps = qt["一株当り純利益"] 
		ke3dic[str(qt)] = {"eps":eps}

	return ke3dic
"""

def ufo (time="now"):		
	word = "四半期" #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
	searchurl = "https://resource.ufocatch.com/atom/tdnetx/query/{}".format(word)
	print(searchurl)
	response = requests.get(searchurl)
	root = BeautifulSoup(response.content, "xml")

	if time == "now":
		updated = root.find("entry").find("updated").text.split(sep="T")[0]
	else: 
		updated = time
	links = root.findAll("link")
	xbrlpages = []

	for a in links:
		checker = False
		if "ixbrl.htm" in a.get("href") and "Summary" in a.get("href"):
			print(a.parent.find("updated").string)
			if updated in a.parent.find("updated").string:
				checker = True
				xbrlpages.append (a.get("href")) 
			else:
				pass
				if checker == True:
					break 
				# struture of xml 
				# 01/10
				# 01/09 if it has already gone to the targeted date and exits the zone, the loop breaks

	return xbrlpages
	
def epsget (url):
	html = BeautifulSoup(requests.get(url).content, "html.parser")
	print 
	title = html.find(name="tse-ed-t:DocumentName").parent.string
	code = html.find(name="tse-ed-t:SecuritiesCode").string
	companyname = html.find(name="tse-ed-t:CompanyName").string
	pure = html.findall(name="tse-ed-t:NetIncomePerShare").string # Earnings per share 
	modified = html.findall(name="tse-ed-t:DilutedNetIncomePerShare") # adjusted to the number after issuing more stocks if there was any

	# they will have two elements, this year and last year 
	
	for year in pure:
		if year == pure[0]:
			if year.parent.name == "td":
				this_pure_eps = year.parent.text
			elif year.parent.name == "span": # year >> span >> p >> td
				this_pure_eps = year.parent.parent.parent.text
		elif year == pure[1]:
			if year.parent.name == "td":
				last_pure_eps = year.parent.text
			elif year.parent.name == "span": # year >> span >> p >> td
				last_pure_eps = year.parent.parent.parent.text
	
	for year in modified:
		if year == modified[0]:
			if year.parent.name == "td":
				this_mod_eps = year.parent.text
			elif year.parent.name == "span": # year >> span >> p >> td
				this_mod_eps = year.parent.parent.parent.text
		elif year == modified[1]:
			if year.parent.name == "td":
				last_mod_eps = year.parent.text
			elif year.parent.name == "span": # year >> span >> p >> td
				last_mod_eps = year.parent.parent.parent.text

	if this_mod_eps == "-":
		this_year = float(this_pure_eps.replace("△", "-"))
	else:
		this_year = float(this_mod_eps.replace("△", "-"))

	if last_mod_eps == "-":
		last_year = float(last_pure_eps.replace("△", "-"))
	else:
		last_year = float(last_mod_eps.replace("△", "-"))

	return title, code, companyname, this_year, last_year

def sorter(data, upto):
	buylist = []
	upto = upto-1
	temp_list_eps = []
	for report in data:
		report["rate"] = report["this_year"]-data["last_year"]
		temp_list_eps.append(report["rate"])

	newlist = sorted(list(set(temp_list_eps)) ,reverse=True)
	print(len(newlist))
	cutline = newlist[upto]
	
	for report in data:
		if report["rate"] > cutline:
			buylist.append(report)

	return buylist
		

def price(code, date):
	year = date.split("-")[0]
	if os.path.isfile("/Users/okamotohikari/scripts/stock/data/stockprice/{}_{}.csv".format(code, year)) == True:
		pass
	else:
		url = "https://kabuoji3.com/stock/" # https://kabuoji3.com/stock/6758/ >>> Sony(6758)
		driver_path = "/Users/okamotohikari/scripts/stock/chromedriver"
		driver = webdriver.Chrome(driver_path)
		options = webdriver.ChromeOptions()
		options.add_experimental_option("prefs", {
			"download.default_directory": "/Users/okamotohikari/scripts/stock/data/stockprice/",
			"plugins.always_open_pdf_externally": True})

		driver.get("{}{}/{}/".format(url, str(code), str(year)))
		WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="base_box"]/div/div[3]/form/button')))
		driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div/div[1]/section/div/div/div[3]/form/button').click()
		WebDriverWait(driver, 10).until(EC.url_matches("https://kabuoji3.com/stock/download.php"))
		if driver.current_url == "https://kabuoji3.com/stock/download.php":
			driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div/div[1]/section/div/div/div[3]/form/button').click()
		print (driver.current_url)
		time.sleep(5)
		driver.quit()

		if os.path.isfile("/Users/okamotohikari/scripts/stock/data/stockprice/{}_{}.csv".format(code, year)) == False:
			print ("downlaod unsuccessful, exiting")
			exit()

	pricedf = pd.read_csv("/Users/okamotohikari/scripts/stock/data/stockprice/{}_{}.csv".format(code, year))
	before = pricedf.at[pricedf[date].shift(1).values]
	next = pricedf.at[pricedf[date].shift(-1).values]
	next2 = next = pricedf.at[pricedf[date].shift(-2).values]

	on_starting = pricedf.at[date, "始値"]
	on_ending = pricedf.at[date, "終値"]

	before_starting = pricedf.at[before, "始値"]
	before_ending = pricedf.at[before, "終値"]

	next_starting = pricedf.at[next, "始値"]
	next_ending = pricedf.at[next, "終値"]

	next2_starting = pricedf.at[next2, "始値"]
	next2_ending = pricedf.at[next2, "終値"]

	return {code: 
		{"on_starting": on_starting, "on_ending": on_ending, 
		"before_starting": before_starting, "before_ending": before_ending,
		"next_starting" : next_starting, "next_ending" : next_ending,
		"next2_starting": next2_starting, "next2_ending": next2_ending,

		# calcurated values # how do you spell calcurated?
		"oneday_gain": on_ending-on_starting,
		"daybefore_gain": before_ending-before_starting,
		"twoday_gain": next_ending - on_starting, 
		"threeday_gain": next2_ending - on_starting,
			}
	}


def main ():
	data = {}
	pricelist = []
	time = "2020-01-07"
	pages = ufo(time) #def ufo (time="now"): time example >>> 2020-01-10
	print (len(pages))
	for page in pages: 
		title, code, companyname, this_year, last_year = epsget(page) #	return title, code, companyname, this_year, last_year
		data[title]["code"] = code
		data[title]["company"] = companyname
		data[title]["this_year"] = this_year
		data[title]["last_year"] = last_year
	
	buylist = sorter(data, 5)
	print (buylist)

	for a in buylist:
		results = price(a, time)
		pricelist.append(results)
		print (results)
		print ("yessssssssssssssssssssssssssssssssssssssssssssssssss")

	for one in pricelist:
		print (one["oneday_gain"])
		print (one["before_gain"])
		print (one["twoday_gain"])
		print (one["threeday_gain"])

	with open ("/Users/okamotohikari/scripts/stock/results/{}.json".format(time), "w") as f:
		json.dump(pricelist, fp=f, indent=2)

	
if __name__ == "__main__":
	main()






	
















