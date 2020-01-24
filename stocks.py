#import quandl
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



#quandl.ApiConfig.api_key = "UKv2WEbL4aEsPygasKfq"
#data = quandl.get('TSE/6758')
#data [:5]

code = 1301
year = 2019


"""
def kessan(code, year):
	ke3dic = {}
	path = "20191231f.xls"
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
	print (url)
	title = html.find("ix:nonnumeric", {"name":"tse-ed-t:DocumentName"}).parent.text
	code = html.find("ix:nonnumeric", {"name":"tse-ed-t:SecuritiesCode"}).text
	code = code[:-1]
	companyname = html.find("ix:nonnumeric", {"name":"tse-ed-t:CompanyName"}).text
	pure = html.find_all("ix:nonfraction", {"name":"tse-ed-t:NetIncomePerShare"}) # Earnings per share 
	modified = html.find_all("ix:nonfraction" ,{"name":"tse-ed-t:DilutedNetIncomePerShare"}) # adjusted to the number after issuing more stocks if there was any

	# they will have two elements, this year and last year 
	
	print (modified)
	for year in pure:
		if year == pure[0]:
			if year.parent.name == "td":
				this_pure_eps = year.parent.text
			elif year.parent.parent.name == "td": 
				this_pure_eps = year.parent.parent.text
			elif year.parent.parent.parent.name == "td":
				this_pure_eps = year.parent.parent.parent.text
		
		elif year == pure[1]:
			if year.parent.name == "td":
				last_pure_eps = year.parent.text
			elif year.parent.parent.name == "td": 
				last_pure_eps = year.parent.parent.text
			elif year.parent.parent.parent.name == "td":
				last_pure_eps = year.parent.parent.parent.text

	for year in modified:
		if year == modified[0]:
			if year.parent.name == "td":
				this_mod_eps = year.parent.text
			elif year.parent.parent.name == "td":
				this_mod_eps = year.parent.parent.text
			elif year.parent.parent.parent.name == "td":
				this_mod_eps = year.parent.parent.parent.text
		elif year == modified[1]:
			if year.parent.name == "td":
				last_mod_eps = year.parent.text
			elif year.parent.parent.name == "td":
				last_mod_eps = year.parent.parent.text
			elif year.parent.parent.parent.name == "td":
				last_mod_eps = year.parent.parent.parent.text

	if last_pure_eps == "－" or last_pure_eps == "-" or last_pure_eps == "―": # without last year's data, this stock is out of consideration
		this_year = 0 
		last_year = 0
		return title, code, companyname, this_year, last_year

	if this_mod_eps == "―" or this_mod_eps == "－" or this_mod_eps == "-":
		print("if   this_pure_eps  >>> ", this_pure_eps)
		this_year = float(this_pure_eps.replace("△", "-").replace(" ", "").replace("－", "-"))
	else:
		print("else   this_mod_eps  >>> ", this_mod_eps)
		this_year = float(this_mod_eps.replace("△", "-").replace(" ", "").replace("－", "-"))

	if last_mod_eps == "―" or last_mod_eps == "－" or last_mod_eps == "-":
		print("if   last_pure_eps  >>> ", last_pure_eps)
		last_year = float(last_pure_eps.replace("△", "-").replace(" ", "").replace("－", "-"))
	else:
		print("else   last_mod_eps  >>> ", last_mod_eps)
		last_year = float(last_mod_eps.replace("△", "-").replace(" ", "").replace("－", "-"))

	return title, code, companyname, this_year, last_year

def sorter(data, upto):
	buylist = []
	upto = upto-1
	temp_list_eps = []
	print (data)
	for report in data:
		print (data[report]["this_year"], data[report]["last_year"])
		data[report]["rate"] = data[report]["this_year"]-data[report]["last_year"]
		temp_list_eps.append(data[report]["rate"])

	newlist = sorted(list(set(temp_list_eps)) ,reverse=True)
	print(len(newlist))
	cutline = newlist[upto]
	
	for report in data:
		if data[report]["rate"] < 0:
			continue
		if report == cutline:
			buylist.append(data[report])

	return buylist
		
def price2 (code, date, this, last, rate):
	if "Linux" in platform.system():
		driver_path = "./drivers/linux/chromedriver"
	elif "Mac" in platform.system():
		driver_path = "./drivers/mac/chromedriver"

	mon = date.split("-")[1]
	day = date.split("-")[2] #"2019-12-13" for example
	
	if os.path.isfile("./data/stockdaily/T20{}{}.zip".format(mon, day)) == True:
		pass
	else:
		url = "http://mujinzou.com/2020_day_calendar.htm"
		options = webdriver.ChromeOptions()
		options.add_experimental_option("prefs", {
			"download.default_directory": os.getcwd()+"/data/stockdaily/",
			 "download.directory_upgrade": True,
			 'download.prompt_for_download': False})
		driver = webdriver.Chrome(driver_path, options=options)
		driver.get(url)


		fileurl = 'd_data/2020d/20_{}d/T20{}{}.zip'.format(mon,mon,day)
		try:
			WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[@href="{}"]'.format(fileurl))))
		except TimeoutException:
			driver.quit()
			return
		driver.find_element_by_xpath('//a[@href="{}"]'.format(fileurl)).click()
		time.sleep(10)
		driver.quit()

		with zipfile.ZipFile('./data/stockdaily/T20{}{}.zip'.format(mon, day)) as existing_zip:
			existing_zip.extractall('./data/stockdaily/')

		os.remove('./data/stockdaily/T20{}{}.zip'.format(mon, day))
		if os.path.isfile("./data/stockdaily/T20{}{}.csv".format(mon, day)) == False:
			print ("downlaod unsuccessful, exiting")
			exit()
	

	for goback in range(1,4):
		if os.path.isfile("./data/stockdaily/T20{}{}.csv".format(mon, int(day-goback))) == False:
			pass
		else:
			yesterday = "./data/stockdaily/T20{}{}.csv".format(mon, int(day-goback))
				


def price(code, date, this, last, rate, company):
	if "Linux" in platform.system():
		driver_path = "./drivers/linux/chromedriver"
	elif "Mac" in platform.system():
		driver_path = "./drivers/mac/chromedriver"

	year = date.split("-")[0]
	if os.path.isfile("./data/stockprice/{}_{}.csv".format(code, year)) == True:
		pass
	else:
		url = "https://kabuoji3.com/stock/" # https://kabuoji3.com/stock/6758/ >>> Sony(6758)
		options = webdriver.ChromeOptions()
		options.add_experimental_option("prefs", {
			"download.default_directory": os.getcwd()+"/data/stockdaily/",
			 "download.directory_upgrade": True,
			 'download.prompt_for_download': False})

		driver = webdriver.Chrome(driver_path, options=options)
		driver.get("{}{}/{}/".format(url, str(code), str(year)))
		WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="base_box"]/div/div[3]/form/button')))
		driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div/div[1]/section/div/div/div[3]/form/button').click()
		WebDriverWait(driver, 30).until(EC.url_matches("https://kabuoji3.com/stock/download.php"))
		if driver.current_url == "https://kabuoji3.com/stock/download.php":
			driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div/div[1]/section/div/div/div[3]/form/button').click()
		print (driver.current_url)
		time.sleep(30)
		driver.quit()

		if os.path.isfile("./data/stockprice/{}_{}.csv".format(code, year)) == False:
			print ("downlaod unsuccessful, exiting")
			exit()

	

	pricedf = pd.read_csv("./data/stockprice/{}_{}.csv".format(code, year), encoding="SHIFT-JIS")
	today = list(pricedf.index.values).index(date)
	before = pricedf.index.values[today-1]
	next = pricedf.index.values[today+1]
	next2 = pricedf.index.values[today- 1]

	#print (before, next, next2)
	on_starting = pricedf.at[date,"Unnamed: 1"] #始値
	on_ending = pricedf.at[date,"Unnamed: 4"] #終値

	before_starting = pricedf.at[before, "Unnamed: 1"] #始値
	before_ending = pricedf.at[before,"Unnamed: 4"] #終値

	next_starting = pricedf.at[next, "Unnamed: 1"] #始値
	next_ending = pricedf.at[next, "Unnamed: 4"] #終値

	next2_starting = pricedf.at[next2, "Unnamed: 1"] #始値
	next2_ending = pricedf.at[next2, "Unnamed: 4"] #終値

	"""
	print ({"on_starting": int(on_starting), "on_ending": int(on_ending), 
		"before_starting": int(before_starting), "before_ending": int(before_ending),
		"next_starting" : int(next_starting), "next_ending" : int(next_ending),
		"next2_starting": int(next2_starting), "next2_ending": int(next2_ending),

		# calcurated values # how do you spell calcurated
		"oneday_gain": int(on_ending)-int(on_starting),
		"daybefore_gain": int(before_ending)-int(before_starting),
		"twoday_gain": int(next_ending) - int(on_starting), 
		"threeday_gain": int(next2_ending) - int(on_starting)})
	"""

	return {"code": code,
		"this_year": this,
		"last_year": last,
		"rate": rate,
		"company": company,

		"on_starting": int(on_starting), "on_ending": int(on_ending), 
		"before_starting": int(before_starting), "before_ending": int(before_ending),
		"next_starting" : int(next_starting), "next_ending" : int(next_ending),
		"next2_starting": int(next2_starting), "next2_ending": int(next2_ending),
		
		"oneday_gain": int(on_ending)-int(on_starting),
		"daybefore_gain": int(before_ending)-int(before_starting),
		"twoday_gain": int(next_ending) - int(on_starting), 
		"threeday_gain": int(next2_ending) - int(on_starting)}
	


def main ():
	##price ("8925", "2019-12-13")
	##exit()

	
	upto = 10
	data = {}
	pricelist = []
	time = "2019-12-13"


	"""
	pages = ufo(time) #def ufo (time="now"): time example >>> 2020-01-10
	print (len(pages))
	for page in pages: 
		title, code, companyname, this_year, last_year = epsget(page) #	return title, code, companyname, this_year, last_year
		data[title] = {"code":code,"company": companyname, "this_year": this_year,"last_year": last_year}
	
	if len(data) < upto:
		print ("not enough data>>>", len(data))
		exit()
	buylist = sorter(data, 10)
	print (buylist)

	for a in buylist:
		try:
			results = price(a["code"], time, this=a["this_year"], last=a["last_year"], rate=a["rate"] company=a["company"])
			pricelist.append(results)
			print (results)
			print ("yessssssssssssssssssssssssssssssssssssssssssssssssss")
		except:
			pass
	

	with open ("results/{}.json".format(time), "w") as f:
		json.dump(pricelist, fp=f, indent=2)
	"""
	
	with open ("results/{}.json".format(time), "r") as f:
		X = []
		Y = []
		for a in json.load(f):
			print ("this >>>>", a["this_year"])
			print ("daybefore_gain >>> ", a["daybefore_gain"])
			print ("rate >>>", a["rate"])
			print ("1 day >>>", a["oneday_gain"])
			print ("2 day >>>", a["twoday_gain"])
			print ("====================================")
			if a["rate"] == 0:
				continue

			X.append (a["rate"])
			Y.append(a["oneday_gain"])
		#print (np.corrcoef (X, Y)[0][1])


	
	"""
	for a in range (9, 30):
		if len(str(a)) == 1:
			a = "0"+a
		date = "2020-01-{}".format(a)
		price2 ("4634", date, this=0, last=0, rate=0)
	"""
	


if __name__ == "__main__":
	main()






	
















