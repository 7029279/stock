import pandas as pd

import time 
import datetime
import os 
import json
import platform 
import numpy as np


def buysell (one_purchase, report):
	buyhowmany = int(one_purchase/report["buy_values"][0])
	otsuri = one_purchase-buyhowmany*report["buy_values"][0]
	soldprice = buyhowmany*report["buy_values"][1]

	return int(soldprice+otsuri)

def logic_a(data, budget, howmany=1, cutline=0,  price_level=[1, 100000], 
daynight="all", sort_by ="rate"): # by expectation_change_rate, by 
	potential_buylist = []
	one_purchase = int(budget/howmany)

	for a in data:
		if 0 in [a["buy_values"][0], a["buy_values"][1], a["new"], a["old"]]:
			continue
		elif int(a["buy_values"][0]) > one_purchase:
			continue
		elif int(a["buy_values"][0]) > price_level[1]:
			continue

		if daynight == "day":
			if int(a["updated_at"].split(":")[0]) >= 15: # selecting only during the day
				continue
		elif daynight == "night":
			if int(a["updated_at"].split(":")[0]) < 15:
				continue
		elif daynight == "all":
			pass

		if float(a["rate"]) > 0 and float(a["mew"]) >= cutline:
			potential_buylist.append(a)
		
	if len(potential_buylist) > howmany:
		sorted_data = sorted(potential_buylist, key = lambda i: i[sort_by], reverse=True) 
		sorted_data = sorted_data[:howmany]	
	else:
		sorted_data = potential_buylist

	for a in sorted_data:
		sold = buysell(one_purchase, a)
		budget = budget-one_purchase+sold
	return {"new_budget": budget, "sorted_data": sorted_data}



def logic_b(data, budget, howmany=1, cutline=30, price_level=[1, 100000]): # by expectation_change_rate, by number
	potential_buylist = []
	one_purchase = int(budget/howmany)
	for a in data:
		if 0 in [a["buy_values"][0], a["buy_values"][1], a["new"], a["old"]]:
			continue
		elif int(a["buy_values"][0]) > one_purchase:
			continue
		elif int(a["buy_values"][0]) > price_level[1]:
			continue
		if float(a["rate"]) > 0 and float(a["new"]) > cutline:
			potential_buylist.append(a)

		
	if len(potential_buylist) > howmany:
		sorted_data = sorted(potential_buylist, key = lambda i: i['rate'], reverse=True) 
		sorted_data = sorted_data[:howmany]	
	else:
		sorted_data = potential_buylist

	for a in sorted_data:
		sold = buysell(one_purchase, a)
		budget = budget-one_purchase+sold
	return {"new_budget": budget, "sorted_data": sorted_data}



def logic_c(data, budget, howmany=1, cutline=30, 
exclude_market=[], exclude_ind = [], exclude_scale=[]): # by expectation_change_rate, by number
	potential_buylist = []
	one_purchase = int(budget/howmany)
	for a in data:
		if 0 in [a["buy_values"][0], a["buy_values"][1], a["new"], a["old"]]:
			continue
		elif int(a["buy_values"][0]) > one_purchase:
			continue
		elif a["market"] in exclude_market:
			continue
		elif a["industry"] in exclude_ind:
			continue
		elif a["scale"] in exclude_scale:
			continue
		
		if float(a["rate"]) > 0 and float(a["new"]) > cutline:
			potential_buylist.append(a)

		
	if len(potential_buylist) > howmany:
		sorted_data = sorted(potential_buylist, key = lambda i: i['rate'], reverse=True) 
		sorted_data = sorted_data[:howmany]	
	else:
		sorted_data = potential_buylist

	for a in sorted_data:
		sold = buysell(one_purchase, a)
		budget = budget-one_purchase+sold
	return {"new_budget": budget, "sorted_data": sorted_data}


def logic_d(data, budget, howmany=1, cutline=30, daynight="all", report_type="all", sort_by ="rate"):
	potential_buylist = []
	one_purchase = int(budget/howmany)
	for a in data:
		if 0 in [a["buy_values"][0], a["buy_values"][1], a["new"], a["old"]]:
			continue
		elif int(a["buy_values"][0]) > one_purchase:
			continue
		elif int(a["new"]) < cutline:
			continue
		elif float(a["rate"]) > 0 and float(a["new"]) > cutline:
			if report_type== "all":
				potential_buylist.append(a)
			elif a["report_type"] == report_type:
				potential_buylist.append(a)
			
	if len(potential_buylist) > howmany:
		sorted_data = sorted(potential_buylist, key = lambda i: i[sort_by], reverse=True) 
		sorted_data = sorted_data[:howmany]	
	else:
		sorted_data = potential_buylist

	for a in sorted_data:
		sold = buysell(one_purchase, a)
		budget = budget-one_purchase+sold
	return {"new_budget": budget, "sorted_data": sorted_data}
	

def simulate (cutline, howmany, logic="b", price_level=[1, 100000], 
			budget=5000, daynight="all", sort_by="rate", 
			exclude_ind=[], exclude_market=[], exclude_scale=[], report_type="all"):
	change_list = []
	simudata = []
	start_str = "2019-11-01"
	start_day = datetime.date(year=int(start_str.split("-")[0]), month=int(start_str.split("-")[1]), day=int(start_str.split("-")[2]))

	end_str ="2020-01-23"
	end_day = datetime.date(year=int(end_str.split("-")[0]), month=int(end_str.split("-")[1]), day=int(end_str.split("-")[2]))
	
	oneday = start_day-datetime.timedelta(days=1)

	while True:
		for goforth in range(1, 15):
			oneday = oneday+datetime.timedelta(days=goforth)
			year = oneday.year
			mon = oneday.month
			day = oneday.day  
			if os.path.isfile("./results3/{}-{:02d}-{:02d}.json".format(year, mon, day)) == True:
				with open("./results3/{}-{:02d}-{:02d}.json".format(year, mon, day), "r") as f:
					data = json.load(f)
				if logic=="a":
					result = logic_a(data, budget, daynight=daynight, sort_by=sort_by, price_level=price_level)
				elif logic == "b":
					result = logic_b(data, budget, howmany ,cutline, price_level=price_level)
				elif logic == "c":
					result = logic_c(data, budget, howmany ,cutline, exclude_ind=exclude_ind, exclude_market=exclude_market)
				elif logic == "d":
					result = logic_d(data, budget, howmany ,cutline, daynight=daynight, report_type=report_type)
				simudata.append(result)
				change = result["new_budget"]-budget
				result["change"] = change

				if len(result["sorted_data"]) == 0:
					print (oneday, "  final cash in your hand >>>>", budget, "   change>>", 
				str(change/budget)[:6], "|", change,   "no transaction today")
				elif change < 0:
					print (oneday, "  final cash in your hand >>>>", budget, "   change>>", 
				str(change/budget)[:6], "|", change,   ">>>>>>", result["sorted_data"][0]["buy_values"][0], "<<<<<<")
				else:
						print (oneday, "  final cash in your hand >>>>", budget, "   change>>", 
				str(change/budget)[:6], "|", change,  ">>>>>>", result["sorted_data"][0]["buy_values"][0])
				
				budget = result["new_budget"]
				change_list.append(change/budget)
				if change/budget < -100:
					for a in result["sorted_data"]:
							print (oneday)
							print ("company, code  >>> ", a["company"]," ", a["code"])
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
				if budget == 0: 
					print ("you went bankrupt!!!")
					exit()
				break
			else:
				oneday = oneday-datetime.timedelta(days=goforth)
		if oneday == end_day:
			break
		average = sum(change_list)/len(change_list)
	print ("average change   ", str(average)[:9], "  pricelevel ", price_level, "   howmnay  ", howmany)
	return average

def optimal ():
	stats = []
	
	#for budget in range(3000, 6000, 1000):
	
		#for pricelevel in range (3000, 5000, 500): 
	budget = 5000
	pricelevel = 10000
	cutline = 36
	daynight = "all"
	#for sort in ["expec_change_rate", "expec_change", "new_expec"]:
	for cutline in range(0, 36, 35):
		for daynight in ["all"]: # ["day", "night", "all"]:
		#for indus_exclude in [["化学", "銀行業", "陸運業", "輸送用機器", "医薬品", "卸売業", "不動産業", "精密機器","金属製品"], []]:
			average = simulate (logic="d", howmany=1,
			cutline=cutline, price_level=[0, pricelevel], budget=budget, daynight=daynight, sort_by="rate", report_type="修正")
			if average < 0:
				continue
			stats.append({"average":average, "cutline":cutline, 
			"pricelevel": pricelevel, "daynight":daynight})
		
	stats_sorted = sorted(stats, key = lambda i: i['average'], reverse=True)
	

	"""
	for cutline in range (100):
		for pricelevel in range (200, 5000, 100): 
			average = simulate (logic="b", howmany=howmany, cutline=cutline, price_level=[0, pricelevel])
			stats.append({"average":average, "cutline":cutline, "howmany":howmany, "pricelevel": pricelevel})

	stats_sorted = sorted(stats, key = lambda i: i['average'], reverse=True)
	"""

	
	for a in stats_sorted[:30]:
		a["average"] =str(a['average'])[:7]
		print (stats_sorted[:30].index(a), ">>>", a)



if __name__ == "__main__":
	#simulate (logic="a", howmany = 1, cutline = 0, price_level=[1, 7000], sort_by="expec_change", daynight="day")
	
	#marketsearch()	

	optimal()






["化学", "銀行業", "陸運業", "輸送用機器", "医薬品", "卸売業", "不動産業", "精密機器","金属製品"]

"""
negative 
化学 {'average': -0.005527210884353743, 'negative': 15, 'positive': 0}
銀行業 {'average': -0.000993510541196375, 'negative': 48, 'positive': 12}
陸運業 {'average': -0.00035971223021582724, 'negative': 12, 'positive': 0}
輸送用機器 {'average': -0.026090310916346192, 'negative': 39, 'positive': 1}
医薬品 {'average': -0.03028727556596407, 'negative': 48, 'positive': 2}
卸売業 {'average': -0.02366837498903869, 'negative': 60, 'positive': 0}
不動産業 {'average': -0.00013976240391334733, 'negative': 1, 'positive': 0}
精密機器 {'average': -0.004441391941391942, 'negative': 12, 'positive': 0}
金属製品 {'average': -0.055443802355933984, 'negative': 60, 'positive': 0}



plus 

情報・通信業 {'average': 0.01846843988635096, 'negative': 11, 'positive': 45}
電気機器 {'average': 0.0124635865024881, 'negative': 0, 'positive': 20}
小売業 {'average': 0.013632987590648571, 'negative': 12, 'positive': 40}
機械 {'average': 0.035114717142758184, 'negative': 0, 'positive': 60}
建設業 {'average': 0.020081811607537265, 'negative': 0, 'positive': 60}
サービス業 {'average': 0.022344317246848714, 'negative': 0, 'positive': 54}


=========================-
JASDAQ(グロース・内国株） {'average': -0.035222482435597176, 'negative': 48, 'positive': 0}
JASDAQ(スタンダード・内国株） {'average': -0.03783050571457335, 'negative': 60, 'positive': 0}


市場第一部（内国株） {'average': 0.012510698703910915, 'negative': 0, 'positive': 60}
市場第二部（内国株） {'average': 0.02020511051432267, 'negative': 10, 'positive': 50}
マザーズ（内国株） {'average': 0.006047846605264431, 'negative': 0, 'positive': 16}

"""










def indusmarket(cutline=0, rate=0):
	market_list=['JASDAQ(グロース・内国株）','市場第二部（内国株）','マザーズ（内国株）','JASDAQ(スタンダード・内国株）','市場第一部（内国株）']
	
	market_dict = {}
	industry_list=['証券、商品先物取引業', '石油・石炭製品', '水産・農林業', '-','空運業', '電気機器', '海運業', 'その他金融業', '化学', 
	'情報・通信業', '銀行業', '繊維製品','陸運業', '輸送用機器', '医薬品', '機械', '鉄鋼', '小売業', 'その他製品', '卸売業', 
	'ゴム製品', '保険業', '不動産業', '精密機器', '金属製品', '食料品', '非鉄金属', 'ガラス・土石製品', '電気・ガス業', 
	'建設業', 'サービス業','パルプ・紙', '倉庫・運輸関連業', '鉱業']
	industry_dict = {}

	start_str = "2019-11-01"
	start_day = datetime.date(year=int(start_str.split("-")[0]), month=int(start_str.split("-")[1]), day=int(start_str.split("-")[2]))

	end_str ="2020-01-23"
	end_day = datetime.date(year=int(end_str.split("-")[0]), month=int(end_str.split("-")[1]), day=int(end_str.split("-")[2]))
	
	oneday = start_day-datetime.timedelta(days=1)

	for a in industry_list:
		industry_dict[a] = [[], {"average": 0}] 
	for a in market_list:
		market_dict[a] = [[], {"average": 0}] 

	while True:
		for goforth in range(1, 15):
			oneday = oneday+datetime.timedelta(days=goforth)
			year = oneday.year
			mon = oneday.month
			day = oneday.day  
			if os.path.isfile("./results2/{}-{:02d}-{:02d}-lv2.json".format(year, mon, day)) == True:
				with open("./results2/{}-{:02d}-{:02d}-lv2.json".format(year, mon, day), "r") as f:
					data = json.load(f)
				for a in data:
					if a["market"] == "null" or a["industry"] == "null":
						pass
					elif a["trade_return"] == 0:
						pass
					elif float(a["rate"]) < rate*0.1:
						pass
					elif float(a["new"]) < cutline:
						pass
					else:
						industry_dict[a["industry"]][0].append(a["trade_return"])
						market_dict[a["market"]][0].append(a["trade_return"])

			else:
				oneday = oneday-datetime.timedelta(days=goforth)
		if oneday == end_day:
			break
	
	for a in industry_dict:
		if len(industry_dict[a][0]) == 0: 
			industry_dict[a][1]["average"] = 0
		else:
			industry_dict[a][1]["average"] = sum(industry_dict[a][0])/len(industry_dict[a][0])

	for a in market_dict:
		if len(market_dict[a][0]) == 0:
			market_dict[a][1]["average"]  = 0
		else:
			market_dict[a][1]["average"] = sum(market_dict[a][0])/len(market_dict[a][0])

	
	return industry_dict, market_dict
	
	
def marketsearch():
	industry = ['証券、商品先物取引業', '石油・石炭製品', '水産・農林業', '-','空運業', '電気機器', '海運業', 'その他金融業', '化学', 
	'情報・通信業', '銀行業', '繊維製品','陸運業', '輸送用機器', '医薬品', '機械', '鉄鋼', '小売業', 'その他製品', '卸売業', 
	'ゴム製品', '保険業', '不動産業', '精密機器', '金属製品', '食料品', '非鉄金属', 'ガラス・土石製品', '電気・ガス業', 
	'建設業', 'サービス業','パルプ・紙', '倉庫・運輸関連業', '鉱業']

	market=['JASDAQ(グロース・内国株）','市場第二部（内国株）','マザーズ（内国株）','JASDAQ(スタンダード・内国株）','市場第一部（内国株）']

	market_score = {} 
	indus_score = {}

	for a in industry:
		indus_score[a] = []
	for a in market:
		market_score[a] = []

	for cutline in range(0, 50, 5):
		for rate in range (0, 5, 1):
			industry_dict, market_dict = indusmarket (cutline=cutline, rate=rate)
			
			for	a in industry_dict:
				indus_score[a].append(industry_dict[a][1]["average"])
			
			for a in market_dict:
				market_score[a].append(market_dict[a][1]["average"])

	for a in market_score:
		market_neg = 0
		market_pos = 0
		for b in market_score[a]:
			if b <0:
				market_neg = market_neg+1
			elif b >0:
				market_pos = market_pos+1
		market_score[a] = {"average": sum(market_score[a])/len(market_score[a]), "negative":market_neg, "positive": market_pos}


	for a in indus_score:
		indus_neg = 0
		indus_pos = 0
		for b in indus_score[a]:
			if b <0:
				indus_neg = indus_neg+1
			elif b >0:
				indus_pos =indus_pos+1
		indus_score[a] = {"average": sum(indus_score[a])/len(indus_score[a]), "negative":indus_neg, "positive": indus_pos}

	with open ("industry.json","w") as f:
		json.dump (indus_score, f, indent=2, ensure_ascii=False)
	
	with open ("market.json","w") as f:
		json.dump (market_score, f, indent=2, ensure_ascii=False)

	for a in indus_score:
		if indus_score[a]["average"] == 0:
			pass
		else:
			print (a, indus_score[a])
	
	print ("=========================-")
	for a in market_score:
		print (a, market_score[a])