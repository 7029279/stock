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
import random
import csv

infodf = pd.read_excel("./data/data_j.xls", encoding="SHIFT-JS")


def ufo2(when="now"):
	word ="業績予想"
	searchurl = "https://resource.ufocatch.com/atom/tdnetx/query/{}".format(word)
	print(searchurl)

	response = requests.get(searchurl)
	root = BeautifulSoup(response.content, "xml")
	if when == "now":
		updated = root.find("entry").find("updated").text.split(sep="T")[0]
	else: 
		updated = when
	links = root.findAll("link")
	xbrlpages = []

	for a in links:
		checker = False
		if "ixbrl.htm" in a.get("href"):
			if "IFRS" in a.parent.find("title").string or "ＩＦＲＳ" in a.parent.find("title").string: 
				continue
			print(a.parent.find("updated").string)
			if updated in a.parent.find("updated").string:
				checker = True
				xbrlpages.append ({"update": a.parent.find("updated").string, "href": a.get("href")}) 
			else:
				pass
				if checker == True:
					break 

	return xbrlpages


def epsget2 (time_and_url):
	html = BeautifulSoup(requests.get(time_and_url["href"]).content, "html.parser")
	print (time_and_url["href"])
	title = html.find("ix:nonnumeric", {"name":"tse-ed-t:DocumentName"}).parent.text
	code = html.find("ix:nonnumeric", {"name":"tse-ed-t:SecuritiesCode"}).text
	if len(str(code)) == 5:
		code = code[:-1]
	companyname = html.find("ix:nonnumeric", {"name":"tse-ed-t:CompanyName"}).text
	
	eps = html.find_all("ix:nonfraction", {"name":"tse-ed-t:NetIncomePerShare"}) # Earnings per share 
	dividend = html.find_all("ix:nonfraction" ,{"name":"tse-ed-t:DividendPerShare"}) # adjusted to the number after issuing more stocks if there was any

	# they will have two elements, this year and last year 

	for row in eps:
		if "_ConsolidatedMember_PreviousMember_ForecastMember" in row["contextref"]:
			old_expec = row.parent.text    ## 連結のほうがいいらしい
		if "_ConsolidatedMember_CurrentMember_ForecastMember" in row["contextref"]:
			new_expec = row.parent.text		
		
	if "old_expec" not in vars() or "new_expec" not in vars():  ##　個別
		for row in eps:
			if "_NonConsolidatedMember_PreviousMember_ForecastMember" in row["contextref"]:
				old_expec = row.parent.text
			elif "_NonConsolidatedMember_CurrentMember_ForecastMember" in row["contextref"]:
				new_expec = row.parent.text
	
	if len(eps) == 0:
		old_expec = "0"
		new_expec = "0"
		expec_change = 0


	for row in dividend:
		if "_NonConsolidatedMember_PreviousMember_ForecastMember" in row["contextref"]:
			old_divi = row.parent.text
		elif "_NonConsolidatedMember_CurrentMember_ForecastMember" in row["contextref"]:
			new_divi = row.parent.text
	
	
	if len(dividend) == 0:
		old_divi = "0"
		new_divi = "0"
		divi_change = 0

	#print ("eps list   ", eps)
	#print ("divi list  ", dividend)
	
	if old_expec == "－" or old_expec == "-" or old_expec == "―" or "～" in str(old_expec): # without last year's data, this stock is out of consideration
		old_expec = 0 
		new_expec = 0
	if new_expec == "－" or new_expec == "-" or new_expec == "―" or "～" in str(new_expec): # without last year's data, this stock is out of consideration
		old_expec = 0 
		new_expec = 0
	if old_divi == "－" or old_divi == "-" or old_divi == "―" or "～" in str(old_divi): # without last year's data, this stock is out of consideration
		old_divi = 0 
		new_divi = 0
	if new_divi == "－" or new_divi == "-" or new_divi == "―" or "～" in str(new_divi): # without last year's data, this stock is out of consideration
		old_divi = 0 
		new_divi = 0
	
	old_expec = str(old_expec).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-")
	new_expec =  str(new_expec).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-")

	old_divi = str(old_divi).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-")
	new_divi = str(new_divi).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-")
	
	new_expec = float(new_expec)
	old_expec = float(old_expec)
	new_divi = float(new_divi)
	old_divi = float(old_divi)

	expec_change = new_expec-old_expec
	divi_change = new_divi-old_divi

	if old_expec == 0:
		expec_change_rate = 0
	else:
		expec_change_rate = abs(expec_change/old_expec)
		if expec_change < 0:
			expec_change*-1
		else:
			expec_change_rate = float(expec_change_rate)

	return title, time_and_url["update"], code, companyname, old_expec, new_expec, expec_change, old_divi, new_divi, divi_change, expec_change_rate


def pricefromcsv(code, day):
	pricedf = pd.read_csv(day,  encoding="SHIFT-JIS")
	#print (df.columns.values) # date, code, market? code&market?, 始値 高値 安値 終値

	try:
		starting = (pricedf[pricedf[pricedf.columns.values[1]] == int(code)].iat[0,4])
		ending = (pricedf[pricedf[pricedf.columns.values[1]] == int(code)].iat[0,7])
	except IndexError:
		starting = 0
		ending = 0
		high = 0
		market = "null"
		industry = "null"
		industry17 = "null"
		scale = "null"
		
		return starting, high, ending, market, industry, industry17,scale


	starting = (pricedf[pricedf[pricedf.columns.values[1]] ==int(code)].iat[0,4])
	#print (pricedf[pricedf[pricedf.columns.values[1]] == int(code)].iat[0,4])
	#print (pricedf[pricedf[pricedf.columns.values[1]] == int(code)])
	#print (list(df[df[df.columns.values[1]] == code]))
	high = (pricedf[pricedf[pricedf.columns.values[1]] ==int(code)].iat[0,5])
	ending = (pricedf[pricedf[pricedf.columns.values[1]] == int(code)].iat[0,7])

	print (code)
	print (infodf[infodf["コード"]==int(code)])

	if infodf[infodf["コード"]==int(code)].empty:
		market = "null"
		industry = "null"
		industry17 = "null"
		scale = "null"
	else:
		market = infodf[infodf["コード"]==int(code)].iat[0, 3]
		industry = infodf[infodf["コード"]==int(code)].iat[0, 5]
		industry17 = infodf[infodf["コード"]==int(code)].iat[0, 7]
		scale = infodf[infodf["コード"]==int(code)].iat[0, 9]

	return starting, high, ending, market, industry, industry17,scale

def download (date):
	print ("downloading ", date)
	if "Linux" in platform.system():
		driver_path = "./drivers/linux/chromedriver"
	elif "Mac" in platform.system():
		driver_path = "./drivers/mac/chromedriver"
	
	year = date.split("-")[0]
	mon = date.split("-")[1]
	day = date.split("-")[2] #"2019-12-13" for example
	
	shortyear = year[-2:] #2019 > 19


	if os.path.isfile("./data/stockdaily/T{}{}{}.csv".format(shortyear, mon, day)) == True:
		pass
	else:
		url = "http://mujinzou.com/{}_day_calendar.htm".format(year)
		options = webdriver.ChromeOptions()
		options.add_experimental_option("prefs", {
			"download.default_directory": os.getcwd()+"/data/stockdaily/",
			 "download.directory_upgrade": True,
			 'download.prompt_for_download': False})
		driver = webdriver.Chrome(driver_path, options=options)
		driver.get(url)

		time.sleep(int(random.randint(10, 30)))

		fileurl = 'd_data/{}d/{}_{}d/T{}{}{}.zip'.format(year,shortyear,mon, shortyear, mon,day)
		try: 
			WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[@href="{}"]'.format(fileurl))))
		except TimeoutException:
			driver.quit()
			with open ("./syukujitsu.json", "r") as f:
				holijson = json.load(f)
			if date in holijson:
				with open("./data/stockdaily/T{}{}{}-holiday.csv".format(shortyear, mon, day), 'w') as f:
					writer = csv.writer(f)
					writer.writerow(["empty"])	
			return
		time.sleep(int(random.randint(10, 30)))
		driver.find_element_by_xpath('//a[@href="{}"]'.format(fileurl)).click()

		time.sleep(10)
		driver.quit()

		with zipfile.ZipFile('./data/stockdaily/T{}{}{}.zip'.format(shortyear, mon, day)) as existing_zip:
			existing_zip.extractall('./data/stockdaily/')
		time.sleep(10)
		os.remove('./data/stockdaily/T{}{}{}.zip'.format(shortyear, mon, day))
		if os.path.isfile("./data/stockdaily/T{}{}{}.csv".format(shortyear, mon, day)) == False:
			print ("downlaod unsuccessful, exiting")
			exit()

def price2 (code, updated_at, title, date, company, 
old_expec, new_expec, expec_change, old_divi, new_divi, divi_change, expec_change_rate):
	
	year = date.split("-")[0]
	mon = date.split("-")[1]
	day = date.split("-")[2] #"2019-12-13" for example
	shortyear = year[-2:] #2019 > 19

	if os.path.isfile("./data/stockdaily/T{}{}{}.csv".format(shortyear, mon, day)) == True:
		today = "./data/stockdaily/T{}{}{}.csv".format(shortyear, mon, day)
	else:
		download(date)		
		today = "./data/stockdaily/T{}{}{}.csv".format(shortyear, mon, day)
	
	if os.path.isfile ("./data/stockdaily/T{}{}{}-holiday.csv".format(shortyear, mon, day)) == True:
		print ("this is holiday")
		return

	for gobackforth in range(1,20):			
		yest = datetime.date(year=int(year), month=int(mon), day=int(day))-datetime.timedelta(days=gobackforth)
		if yest.weekday() == 6 or yest.weekday() == 5:
			continue #skipping saturday and sundays
		elif os.path.isfile("./data/stockdaily/T{}{:02d}{:02d}-holiday.csv".format(str(yest.year)[-2:], yest.month, yest.day)) == True:
			continue
		if os.path.isfile("./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(yest.year)[-2:], yest.month, yest.day)) == True:
			#print ("./data/stockdaily/T{}{:02d}{:02d}.csv".format(shortyear, yest.month, yest.day))
			yesterday = "./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(yest.year)[-2:], yest.month, yest.day)
			break
		else:
			download ("{}-{:02d}-{:02d}".format(yest.year, yest.month, yest.day))
			if os.path.isfile("./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(yest.year)[-2:], yest.month, yest.day)) == True:
				yesterday = "./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(yest.year)[-2:], yest.month, yest.day)
				break
	
	for gobackforth in range(1,15):
		tomo = datetime.date(year=int(year), month=int(mon), day=int(day))+datetime.timedelta(days=gobackforth)
		if tomo.weekday() == 6 or tomo.weekday() == 5:
			continue #skipping saturday and sundays
		elif os.path.isfile ("./data/stockdaily/T{}{:02d}{:02d}-holiday.csv".format(str(tomo.year)[-2:], tomo.month, tomo.day)) == True:
			continue
		if os.path.isfile("./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(tomo.year)[-2:], tomo.month, tomo.day)) == True:
			#print ("./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(tomo.year)[-2:], tomo.month, tomo.day))
			tommorow = "./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(tomo.year)[-2:], tomo.month, tomo.day)
			break
		else:
			download ("{}-{:02d}-{:02d}".format(tomo.year, tomo.month, tomo.day))
			if os.path.isfile("./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(tomo.year)[-2:], tomo.month, tomo.day)) == True:
				tommorow = "./data/stockdaily/T{}{:02d}{:02d}.csv".format(str(tomo.year)[-2:], tomo.month, tomo.day)
				break

	
	before_starting, before_high, before_ending, market, industry, industry17,scale = pricefromcsv(code, yesterday)
	on_starting, on_high,  on_ending, market, industry, industry17,scale = pricefromcsv(code, today)
	next_starting, next_high,  next_ending, market, industry, industry17,scale = pricefromcsv(code, tommorow) #starting, high, ending, market, industry

	
	if on_starting ==0:
		on_return =0
		twoday_return = 0
	else:
		on_return = (int(on_ending)-int(on_starting))/ int(on_starting)
		twoday_return = (int(next_ending) - int(on_starting))/ int(on_starting)

	if on_return < twoday_return:
		max_return = twoday_return 
	elif on_return > twoday_return:
		max_return = on_return
	elif on_return == twoday_return:
		max_return = on_return


	updated_at = updated_at.split("T")[1].replace("+09:00", "")
	if int(updated_at.split(":")[0]) < 15: # duing the day
		trade_return = on_return
		buy_values = [on_starting, on_ending]
	elif  int(updated_at.split(":")[0])  >= 15: # next day
		buy_values = [next_starting, next_ending]
		if int (next_starting) == 0:
			trade_return = 0
		else:
			trade_return = (int(next_ending)-int(next_starting))/ int(next_starting)

	if int (next_starting) == 0:
		next_return = 0
	else:
		next_return = int((int(next_ending) - int (next_starting)) / int (next_starting))
	

	return {"code": code,
		"company": company,
		"updated_at":updated_at,
		"title": title,
		"market": market,  
		"industry": industry,
		"industry17": industry17,
		"scale": scale,

		"old": old_expec, "new":new_expec, "change":expec_change, 
		"old_divi": float(old_divi), "new_divi":float(new_divi), "divi_change":float(divi_change), 
		"rate": expec_change_rate,

		"on_starting": int(on_starting), "on_ending": int(on_ending), 
		"on_high": on_high, "before_high": before_high, "next_high":next_high,
		"before_starting": int(before_starting), "before_ending": int(before_ending),
		"next_starting" : int(next_starting), "next_ending" : int(next_ending),
		
		"oneday_gain": int(on_ending)-int(on_starting),
		"oneday_return": on_return,
		"trade_return": trade_return,
		"buy_values":buy_values,
		"daybefore_gain": int(before_ending)-int(before_starting),
		"twoday_gain": int(next_ending) - int(on_starting),
		"next_gain": int(next_ending) - int (next_starting),
		"next_return": next_return,
		"twoday_return": twoday_return, "max_return": max_return}
	
	
def price(code, date, this, last, rate, company): #not using
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
			"download.default_directory": os.getcwd()+"/data/stockprice/",
			 "download.directory_upgrade": True,
			 'download.prompt_for_download': False})

		driver = webdriver.Chrome(driver_path, options=options)
		driver.get("{}{}/{}/".format(url, str(code), str(year)))
		WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="base_box"]/div/div[3]/form/button')))
		driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div/div[1]/section/div/div/div[3]/form/button').click()
		WebDriverWait(driver, 50).until(EC.url_matches("https://kabuoji3.com/stock/download.php"))
		if driver.current_url == "https://kabuoji3.com/stock/download.php":
			driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div/div[1]/section/div/div/div[3]/form/button').click()
		else:
			WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="base_box"]/div/div[3]/form/button')))
			driver.find_element_by_xpath('/html/body/div/div[2]/div[1]/div/div[1]/section/div/div/div[3]/form/button').click()
			WebDriverWait(driver, 50).until(EC.url_matches("https://kabuoji3.com/stock/download.php"))
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
	next2 = pricedf.index.values[today-1]

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


def main (when ="2020-01-17"):
	data = []
	pricelist = []
	
	
	if os.path.isfile("results2/{}-lv1.json".format(when)) == True:
		pass
	else:
		pages = ufo2(when) #def ufo (time="now"): time example >>> 2020-01-10
		print ("len pages, in main", len(pages), when)
		if len(pages) == 0:
			print ("0 report on ", when,)
			return
		for page in pages:     
			title, update, code, companyname, old_expec, new_expec, expec_change, old_divi, new_divi, divi_change, expec_change_rate = epsget2(page)
		#return title, time_and_url["update"], code, companyname, old_expec, new_expec, ## epsget2()
		# expec_change, old_divi, new_divi, divi_change, expec_change_rate
			data.append({"title": title, "updated_at":update, "code":code,"company": companyname, 
				"old_expec":old_expec, "new_expec": new_expec, "expec_change":expec_change, "expec_change_rate": expec_change_rate,
				"old_divi":old_divi, "new_divi":new_divi, "divi_change":divi_change})

		with open ("results2/{}-lv1.json".format(when), "w") as f:
			json.dump(data, f, indent=2, ensure_ascii=False)

	with open ("results2/{}-lv1.json".format(when), "r") as f:
		data = json.load(f)

	for a in data:
		results = price2(a["code"], a["updated_at"], a["title"], when, company=a["company"], 
        old_expec=a["old_expec"], new_expec=a["new_expec"], expec_change=a["expec_change"], 
		old_divi=a["old_divi"], new_divi=a["new_divi"], divi_change=a["divi_change"], 
		expec_change_rate=a["expec_change_rate"])

		pricelist.append(results)
		#print (results)
		print ("yessssssssssssssssssssssssssssssssssssssssssssssssss")
		
		

	with open ("results2/{}-lv2.json".format(when), "w") as f:
		json.dump(pricelist, fp=f, indent=2, ensure_ascii=False)
		
	
	with open ("results2/{}-lv2.json".format(when), "r") as f:
		X = []
		Y = []
		for a in json.load(f):
			print (a["rate"])
			if a["change"] <= 0:
				continue
			if  a["rate"] < 0:
				continue
		
			print ("old_expec >>>>     ", a["old"])	
			print ("new_expec >>>>     ", a["new"])
			print ("expec_change >>>   ", a["change"])
			print ("expec_change_rate> ", a["rate"], "****")
			print ("divi_change >>>    ", a["divi_change"])
			print ("updated_at >>>     ", a["updated_at"])
			print ("daybefore_gain >>> ", a["daybefore_gain"])
			print ("start >>>          ", a["on_starting"])
			print ("ending >>>         ", a["on_ending"])
			print ("high >>>           ", a["on_high"])
			print ("1 day >>>          ", a["oneday_gain"])
			print ("2 day >>>          ", a["twoday_gain"])
			print ("next_gain   >>>    ", a["next_gain"])
			print ("trade_return >>>     ", a["trade_return"], "****")
			print ("twoday_return >>   ", a["twoday_return"])
			print ("====================================")
			X.append(a["rate"])
			Y.append(a["max_return"])
		if len(X) == 0:
			pass
		else:			
			print (X, Y)
			print ("corre    ", np.corrcoef(X, Y)[0][1])
			print ("average of Y   ", sum(Y)/len(Y))
	
		
	
	"""
	for a in range (15, 23):
		if len(str(a)) == 1:
			a = "0"+str(a)
		date = "2020-01-{}".format(a)
		price2 (9636, date, this=0, last=0, rate=0, company=0)
	
	
	with open ("results2/{}-lv1.json".format(when), "r") as f:
		read = json.load(f)
	for a in read:
		code = a["code"]
		a["on_starting"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["on_starting"]
		a["on_ending"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["on_ending"]
		a["before_starting"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["before_starting"]
		a["before_ending"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["before_ending"]
		a["next_starting"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["next_starting"]
		a["next_ending"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["next_ending"]
		a["oneday_gain"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["oneday_gain"]
		a["daybefore_gain"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["daybefore_gain"]
		a["twoday_gain"] = price2 (code, time, this=0, last=0, rate=0, company="aaa")["twoday_gain"]

		
	#ordinaryaverage()

	with open ("results2/{}-lv2.json".format(time), "w") as f:
		json.dump(pricelist, fp=f, indent=2, ensure_ascii=False)
	
	
	
	for a in range (1, 30):
		
		when = "2019-12-{:02d}".format(a)
		download(when)
	"""
if __name__ == "__main__":
	#main ()
	
	for mon in ["2019-11", "2019-12", "2020-01"]:
		for a in range (1, 31):
			when = "{}-{:02d}".format(mon, a)
			if when == "{}{:02d}{:02d}".format(datetime.datetime.now().year, 
			datetime.datetime.now().month, datetime.datetime.now().day):
				break
			main(when)
	


		
	
