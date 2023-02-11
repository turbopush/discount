from bs4 import BeautifulSoup as bs
import asyncio
import requests
import logging
import json

import aiogram
from aiogram import Bot, Dispatcher, executor, types
from config import *
from set_db import * 
from bot_phrases import *

import random

import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

driver = webdriver.Chrome(service=Service('/usr/bin/chromedriver'))

async def parse():
	polling_task = asyncio.create_task(dp.start_polling())
	with open('/Discount_Bot/keywords.txt', 'r', encoding='UTF-8') as csvfile:
		file = csvfile.readlines()
	while True:
		for row in file:
			limiter = 0
			link = f"https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=https://www.ozon.ru/search/?deny_category_prediction=true&from_global=true&text={row}"
			driver.get(link)
			await asyncio.sleep(1)
			src = driver.page_source
			soup = bs(src, "lxml")
			try:
				src = driver.page_source
				soup = bs(src, "lxml")
				json_source = json.loads(soup.find("pre").get_text())
				widgets = json_source['widgetStates']
				for widget_name, widget_value in widgets.items():
					if 'searchResultsV2' in widget_name:
						for i in range(36):
							product = {}
							try:
								discount = int(json.loads(widget_value)['items'][i]['tileImage']['leftBottomBadge']['text'].split('−')[1][:-1])
								if discount >= 50:
									try:
										product = {}
										product['name'] = json.loads(widget_value)['items'][i]['mainState'][1]['atom']['textAtom']['text']
										product['price'] = json.loads(widget_value)['items'][i]['mainState'][0]['atom']['price']['price'].replace(u'\u2009', '')
										product['discount'] = discount
										product['original_price'] = json.loads(widget_value)['items'][i]['mainState'][0]['atom']['price']['originalPrice'].replace(u'\u2009', '')
										product['url'] = 'https://www.ozon.ru' + json.loads(widget_value)['items'][i]['action']['link']
										product['img_url'] = json.loads(widget_value)['items'][i]['tileImage']['items'][0]['image']['link']
										product['rating'] = json.loads(widget_value)['items'][i]['mainState'][2]['atom']['labelList']['items'][0]['title']
										product['reviews'] = json.loads(widget_value)['items'][i]['mainState'][2]['atom']['labelList']['items'][1]['title'].replace(' ·', '')
										product['brand'] = json.loads(widget_value)['items'][i]['multiButton']['ozonSubtitle']['textAtomWithIcon']['text'].split("</b><font color='#707F8D'>")[1].split("</font>")[0]
									except:
										continue
							except:
								pass
							send_goods = None
							try:
								with open('previously.txt', 'r', encoding='UTF-8') as sessions_read:
									if f"{product['name']} {product['price']}" not in sessions_read.read():
										send_goods = True

								if send_goods is True:
									with open('previously.txt', 'a+', encoding='UTF-8') as sessions:
										sessions.write(f"\n{product['name']} {product['price']}")
									try:
										caption = await dispatch_text(discount_price=product['price'], deleted_price=product['original_price'], 
																	  goods_name=product['name'], brand_name=product['brand'], 
																	  sale=product['discount'], stars=product['rating'],
																	  feedbacks=product['reviews'], goods_link=product['url'])
									except Exception as e:
										break
									users = await check_ozonsub_users()
									for user_id in users:
										try:
											img = requests.get(product['img_url'])
											with open('goods.jpg', 'wb') as img_option:
												img_option.write(img.content)
											goods_photo = open('goods.jpg', 'rb')
											await bot.send_photo(chat_id=user_id[0], photo=goods_photo, caption=caption, parse_mode="HTML")
											goods_photo.close()
										except aiogram.utils.exceptions.BotBlocked:
											pass
									limiter += 1
									if limiter == 2:
										await asyncio.sleep(600)
										break
									os.remove('goods.jpg')
							except Exception:
								pass
			except AttributeError:
				pass


loop = asyncio.get_event_loop()
if __name__ == '__main__':
	loop.run_until_complete(parse())
	loop.close()