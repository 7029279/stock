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
				# struture of xml 
				# 01/10
				# 01/09 if it has already gone to the targeted date and exits the zone, the loop breaks

	return xbrlpages
	

def epsget (time_and_url):
	if os.path.isfile("raw-xbrl1/{}-{}".format(time_and_url["update"].split("T")[0], time_and_url["href"].split("/")[-1])):
		with open ("raw-xbrl1/{}-{}".format(time_and_url["update"].split("T")[0], 
		time_and_url["href"].split("/")[-1]), "r") as f:
			html = BeautifulSoup(f.read(),  "html.parser")
	else:
		html = BeautifulSoup(requests.get(time_and_url["href"]).content, "html.parser")
		with open ("raw-xbrl1/{}-{}.htm".format(time_and_url["update"].split("T")[0],  
		time_and_url["href"].split("/")[-1]), "w") as f:
			f.write(html)

	print (time_and_url["href"])
	title = html.find("ix:nonnumeric", {"name":"tse-ed-t:DocumentName"}).parent.text
	code = html.find("ix:nonnumeric", {"name":"tse-ed-t:SecuritiesCode"}).text
	code = code[:-1]

	companyname = html.find("ix:nonnumeric", {"name":"tse-ed-t:CompanyName"}).text
	pure = html.find_all("ix:nonfraction", {"name":"tse-ed-t:NetIncomePerShare"}) # Earnings per share 
	modified = html.find_all("ix:nonfraction" ,{"name":"tse-ed-t:DilutedNetIncomePerShare"}) # adjusted to the number after issuing more stocks if there was any

	dividend = html.find_all("ix:nonfraction" ,{"name":"tse-ed-t:DividendPerShare"}) # adjusted to the number after issuing more stocks if there was any
	newinfo = html.find("ix:nonnumeric" ,{"name":"tse-ed-t:CorrectionOfConsolidatedFinancialForecastInThisQuarter"})
	divi_newinfo = html.find("ix:nonnumeric" ,{"name":"tse-ed-t:CorrectionOfDividendForecastInThisQuarter"})

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
	
	if len(modified) == 0:
		this_mod_eps = this_pure_eps
		last_mod_eps = last_pure_eps

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

	for row in dividend:
		if "PriorYearDuration_AnnualMember_NonConsolidatedMember_ResultMember" in row["contextref"]:
			if row.parent.name == "td":
				old_divi = row.parent.text
			elif row.parent.parent.name == "td":
				old_divi = row.parent.parent.text
			elif row.parent.parent.parent.name == "td":
				old_divi = row.parent.parent.parent.text
				
		elif "CurrentYearDuration_AnnualMember_NonConsolidatedMember_ForecastMember" in row["contextref"]:
			if row.parent.name == "td":
				new_divi = row.parent.text			
			elif row.parent.parent.name == "td":
				new_divi = row.parent.parent.text
			elif row.parent.parent.parent.name == "td":
				new_divi = row.parent.parent.parent.text
			
	if divi_newinfo.parent.name == "span":
		divi_newinfo = divi_newinfo.replace("（注）直近に公表されている配当予想からの修正の有無：", "").replace(" ", "")

	if newinfo == "span":
		newinfo = newinfo.replace("（注）直近に公表されている業績予想からの修正の有無：", "").replace(" ", "")

	if last_pure_eps == "－" or last_pure_eps == "-" or last_pure_eps == "―": # without last year's data, this stock is out of consideration
		last_pure_eps = 0
		this_year = 0 
		last_year = 0
		change = 0
		rate = 0
	elif this_pure_eps == "－" or this_pure_eps == "-" or this_pure_eps == "―": # without last year's data, this stock is out of consideration
		last_mod_eps = 0
		this_year = 0 
		last_year = 0
		change = 0
		rate = 0
	else:
		if this_mod_eps == "―" or this_mod_eps == "－" or this_mod_eps == "-":
			print("if   this_pure_eps  >>> ", this_pure_eps)
			this_year = float(str(this_pure_eps).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-"))
		else:
			print("else   this_mod_eps  >>> ", this_mod_eps)
			this_year = float(str(this_mod_eps).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-"))

		if last_mod_eps == "―" or last_mod_eps == "－" or last_mod_eps == "-":
			print("if   last_pure_eps  >>> ", last_pure_eps)
			last_year = float(str(last_pure_eps).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-"))
		else:
			print("else   last_mod_eps  >>> ", last_mod_eps)
			last_year = float(str(last_mod_eps).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-"))

		change = this_year-last_year

	if float(last_year) == 0:
		rate = 0
	else:
		rate = abs(change/float(last_year))
		if change < 0:
			rate = rate*-1
		else:
			rate = float(rate)

	if old_divi.replace(" ", "") == "－" or old_divi == "-" or old_divi == "―": # without last year's data, this stock is out of consideration
		old_divi = 0 
		new_divi = 0
		divi_change = 0
	elif new_divi.replace(" ", "") == "－" or new_divi == "-" or new_divi == "―": # without last year's data, this stock is out of consideration
		new_divi = 0 
		old_divi = 0
		divi_change = 0
	else:
		old_divi = float(str(old_divi).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-"))
		new_divi = float(str(new_divi).replace("△", "-").replace(" ", "").replace(",", "").replace("－", "-"))
		divi_change = new_divi - old_divi

	return {"title":title, "update": time_and_url["update"], "code": code, "companyname":companyname,
	"this_year":this_year, "last_year":last_year, "change":change,"rate":rate, "newinfo":newinfo, 
	"old_divi":old_divi, "new_divi":new_divi, "divi_change":divi_change, "divi_newinfo":divi_newinfo}


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

def ordinaryaverage ():
	code = {}
	"""
	for a in ["08", "09","10","14","15","16"]:
		average = []
		day = "T2001"+a
		df = pd.read_csv("./data/stockdaily/{}.csv".format(day),  encoding="SHIFT-JIS")
		df.fillna(0, inplace=True)
		for b in range(len(list(df.index.values))):
			if int(df.iloc[b, 4]) == 0 or int(df.iloc[b, 7]) == 0:
				continue
			print(df.iloc[b])
			code[a].append({"code":int(df.iloc[b, 1]), 
			"starting":int(df.iloc[b, 4]), "ending":int(df.iloc[b, 7]),
			"gain":int(df.iloc[b, 7])-int(df.iloc[b, 4])})


	
	with open ("./averages.json", "w") as f:
		json.dump(code, f, indent=2, ensure_ascii=False)
	"""

	with open ("./averages.json", "r") as f:
		read = json.load(f)
		for a in read:
			average = []
			for b in read[a]:
				average.append(int(b["gain"]))
			print (sum(average)/len(average))
	
def price2 (code, updated_at, title, date, company, 
rate, this, last, change, old_divi, new_divi,divi_change, newinfo):
	
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

		"rate":rate,
		"change":change,
		"new":this, 
		"old":last, 
		"old_divi":old_divi,
		"new_divi": new_divi,
		"divi_change":divi_change,
		"newinfo": newinfo,

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


def main (when= "2020-01-17"):
	##price ("8925", "2019-12-13")
	##exit()
	
	data = []
	pricelist = []
	
	if os.path.isfile("results/{}-lv1.json".format(when)) == True:
		pass
	else:
		pages = ufo(when) #def ufo (time="now"): time example >>> 2020-01-10
		if len(pages) == 0:
			print ("0 report on ", when)
			return
		for page in pages: 
			results= epsget(page) #	return title, code, companyname, this_year, last_year
			data.append({"title": results["title"], "updated_at":results["update"], "code":results["code"],
			"company": results["companyname"], "this_year":results["this_year"],"last_year":results["last_year"], 
			"change":results["change"], "rate": results["rate"], "old_divi": results["old_divi"],"new_divi":results["new_divi"],
			"divi_change": results["divi_change"], "newinfo":results["newinfo"],
			"newinfo":results["newinfo"], "newinfo":results["newinfo"], "divi_newinfo":results["divi_newinfo"]})
		
		with open ("results/{}-lv1.json".format(when), "w") as f:
			json.dump(data, f, indent=2, ensure_ascii=False)

	with open ("results/{}-lv1.json".format(when)) as f:
		data = json.load(f)
		for a in data: #price2 (code, updated_at, title, date, company, rate, this, last):
			results = price2(a["code"], date=when, updated_at=a["updated_at"], company=a["company"],
			title=a["title"],  this=a["this_year"], last=a["last_year"], change=a["change"], rate=a["rate"], 
			old_divi= a["old_divi"],new_divi=a["new_divi"],divi_change=a["divi_change"], newinfo=a["newinfo"])
			pricelist.append(results)
			#print (results)
			print ("yessssssssssssssssssssssssssssssssssssssssssssssssss")
			
		
	with open ("results/{}-lv2.json".format(when), "w") as f:
		json.dump(pricelist, fp=f, indent=2, ensure_ascii=False)
		
	
	with open ("results/{}-lv2.json".format(when), "r") as f:
		X = []
		Y = []
		for a in json.load(f):
			if a["rate"] <= 0:
				continue
			if  a["change"] < 0:
				continue
		

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
			X.append(a["change"])
			Y.append(a["trade_return"])
		if len(X) == 0:
			pass
		else:			
			print (X, Y)
			print ("corre    ", np.corrcoef(X, Y)[0][1])
			print ("average of Y   ", sum(Y)/len(Y))
	
def integrate (when):
	read1 = []
	read2 = []
	data = []
	counter = 0

	if os.path.isfile("results2/{}-lv2.json".format(when)) == True:
		with open ("results2/{}-lv2.json".format(when), "r") as f:
			read2 = json.load(f)

	if os.path.isfile("results/{}-lv2.json".format(when)) == True:
		with open ("results/{}-lv2.json".format(when), "r") as f:
			read1 = json.load(f)
	
	for two in read2:
		for one in read1:
			if two["code"] == one["code"]:
				counter = counter +1
		
	for two in read2:				
		two["report_type"] = "修正"
		two["new"] =float(two["new"])
		two["old"] =float(two["old"])

		data.append(two)

	for one in read1:
		one["report_type"] = "四半期"
		one["new"] =float(one["new"])
		one["old"] =float(one["old"])
		data.append(one)
	
	with open ("results3/{}.json".format(when), "w") as f:
		json.dump (data, f, indent=2, ensure_ascii=False)
	print (when)
			
		
	
if __name__ == "__main__":
	main("2019-12-13")
	exit()
	counter = 0
	counter_ = 0

	for mon in ["2019-11", "2019-12","2020-01"]:
		for a in range (1, 31):
			when = "{}-{:02d}".format(mon, a)
			#if when == "{}{:02d}{:02d}".format(datetime.datetime.now().year, 
			#datetime.datetime.now().month, datetime.datetime.now().day):
			if when == "2020-01-25":
				break
			#time.sleep (random.randint (10, 30))
			#main(when)
			#integrate(when)
			
			"""
			with open ("results3/{}.json".format(when), "r") as f:
				read = json.load(f)
			for a in read:
				if float(0) not in [a["buy_values"][0], a["buy_values"][1], a["new"], a["old"]]:
				#if float(0) not in [float(a["buy_values"][0]), float(a["buy_values"][1]), float(a["new"]), float(a["old"])]:
					print (when, a["code"])
					counter = counter + 1
					print ("0 not in", float(a["buy_values"][0]), float(a["buy_values"][1]), 
					float(a["new"]), float(a["old"]))
				else:
					counter_ = counter_ +1
					print ("0 in", float(a["buy_values"][0]), float(a["buy_values"][1]), 
					float(a["new"]), float(a["old"]))
"""

	print (counter, counter_)






	
















