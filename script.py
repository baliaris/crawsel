'''
2017-04-17
bug report: 
1. firefox profile setting 
   For now, download popup window is invoked though profile set up.
2. End page issue
   End page value is set before page is loaded.
3. make Class for file specific processing in a excel
   parseXlsFromComment and so on

2017-04-18
1. data wrangling
   month, year multi-indexing by datetime
2. use getdummy
   binomial data
3. Add logging logic
4. Add init function

2017-04-19
1. Extract Extra information from gumi library
2. Code Refactorying to covert class
3. Add JSON configuration 

2017-04-20
1. code Refactorying by JSON
   login/out & lending history

2017-05-02
1. 지난 번 마지막 작업까지 기억해서, 데이터를 생성하여 csv로 저장. 하지만 csv와 기존 파일과 merge하는 부분은 아직 구현 안됨
2. 추상화 작업 보완 필요. page를 따라 데이터를 추출하는 과정이 추상화 작업을 진행해야 한다. 
   도서관에서나 혹은 다른 부분에서도 가장 기본적인 flow이기 때문이다.
3. login 부분 검증해야 한다. notice부분은 1차 검증 완료. 
'''

#from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
#from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.common.exceptions import TimeoutException
#from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
from bs4 import BeautifulSoup
import re
import datetime
import pdb
import sys
sys.path.insert(0, 'D:\\business\\utility\\selenuim\\project\\utils')
from utils import ProgUtils
from seleniumWrapper import seleniumWrapper

def find_elm_login(sel):
	selwrapper.log.debug('login page')
	
	eid = selwrapper.wait_explicit(sel.get("bvId"), sel.get("btId"))
	epw = selwrapper.wait_explicit(sel.get("bvPw"), sel.get("btPw"), wait=True)
	
	return eid, epw

def find_elm_logout(sel):
	selwrapper.log.debug('logout')
	
	logout = selwrapper.wait_explicit(sel.get("bvLogout"), sel.get("btLogout"), wait=True)
	
	return logout

def download_files(bdown, sel):
	selwrapper.log.debug("")

	if not bdown: return
	df = selwrapper.get_data()
	if df is None: df = selwrapper.init_data()

	index = len(df.index) - 1
	dlist = selwrapper.find_elm_by_xpath(sel.get("downloadXpath"), count="multi")

	for i, l in enumerate(dlist):
		df.loc[index, "download{0}".format(i)] = \
					selwrapper.find_elm_by_tag(sel.get("downloadTagName"), l, gettype="text")

		l.click()
		selwrapper.wait_implicit()
	return

def transfer_web_to_internal(dsel, elm=None):
	selwrapper.log.debug("")

	df = selwrapper.get_data()
	if df is None: df = selwrapper.init_data()

	index = len(df.index)
	for key, value in dsel.items():
		try:
			df.loc[index, key] = selwrapper.find_elm_by_xpath(value, elm, gettype="text")
		except:
			selwrapper.log.error("key: %s" % key)
			selwrapper.log.error("value: %s" % value)
			selwrapper.log.error(df)

def is_detail_notice(sel):
	selwrapper.log.debug("")
	ret = True

	if selwrapper.wait_explicit(sel.get("detailPage").get("bvTitle")) is None:
		selwrapper.log.debug("No element is found")
		ret = False

	return ret

def cb_parse_lists(attr, sel, **kwargs):
	selwrapper.log.debug("")

	if is_detail_notice(sel) == False: return

	transfer_web_to_internal(sel.get("detailNotice"))
	download_files(attr.get('downEnable'), sel.get("detailPage"))

	return

def cb_parse_pages(attr, sel, **kwargs):
	selwrapper.log.debug("")

	df = selwrapper.get_data()
	if df is None: df = selwrapper.init_data()

	rows = selwrapper.driver.find_elements_by_xpath(sel.get("page").get("startPoint"))
	for row in rows[2:]:
		transfrer_web_to_internal(sel.get("notice"), row)

def cb_get_next_page(number, sel):
	selwrapper.log.debug("")

	if number is None:
		number = selwrapper.wait_explicit(sel.get("page").get("pageCurrent")).text

	if number == "맨끝":
		value = sel.get("page").get("pageCurrent")
		number = str(int(selwrapper.wait_explicit(value).text) + 1)

	if number == "1":
		value = sel.get("page").get("pageCurrent").format(number)
	elif number.isdigit():
		value = sel.get("page").get("pageNumber").format(number)
	else:
		value = sel.get("page").get("pageString").format(number)

	elm = selwrapper.wait_explicit(value)

	func = elm.click
	try:
		follow = selwrapper.find_elm_by_xpath(sel.get("page").get("pageNeighbor"), elm, gettype="text")
	except:
		follow = None
	
	selwrapper.log.debug("next page number:%s" % follow)

	return follow, func

def cb_get_next_list(number, sel):
	selwrapper.log.debug("")

	if number is None:
		t = selwrapper.find_elm_by_xpath(sel.get("detailPage").get("listNumXpath"), count="multi")[2]
	else:
		s = selwrapper.find_elm_by_xpath(sel.get("detailPage").get("listNumXpath2").format(number))
		t = selwrapper.find_elm_by_xpath(sel.get('detailPage').get("listParent"), s)

	elm = selwrapper.find_elm_by_xpath(sel.get("detailPage").get("listLinkXpath"), t)

	func = elm.click
	try:
		follow = selwrapper.find_elm_by_xpath(sel.get("detailPage").get("listNeighbor"), elm, gettype="text")
	except:
		follow = None
	
	selwrapper.log.debug("next list number:%s" % follow)

	return follow, func

def cb_iter_crwal_pages(attr, sel, **kwargs):
	selwrapper.log.debug("")
	
	return iter_crwal_by_elm(attr.get("name")+"_page", cb_get_next_page, False, *[attr, sel])

def cb_iter_crwal_lists(attr, sel, **kwargs):
	selwrapper.log.debug("")

	return iter_crwal_by_elm(attr.get("name")+"_list", cb_get_next_list, True, *[attr, sel])

def cb_submit_key(attr, sel, **kwargs):
	keyword = attr.get("keyword", "")
	if keyword == "": return

	selwrapper.log.debug("keyword for searching: %s" % keyword)

	btype = sel.get('page').get("btSearch")
	value = sel.get('page').get("bvSearch")

	selwrapper.wait_explicit(value, btype).send_keys(keyword+Keys.RETURN)
	selwrapper.wait_implicit()

	return

def cb_history_of_books(attr, sel, **kwargs):
	'''
		Get histroy of books out of a library. Click the download button and store automatically.
		@params:
			attr  - Required  : configuration of tasks (Obj)
			sel  - Required  : web identifier such as xss, xpath, or class name (Obj)
	'''
	selwrapper.log.debug("task name: %s" % attr.get("name"))

	selwrapper.wait_explicit(sel.get('history').get("bvDown")).click()

	return True

def cb_history_of_progress(attr, sel, **kwargs):
	selwrapper.log.debug("task name: %s" % attr.get("name"))

	selwrapper.wait_explicit(sel.get('progress').get("bvDown")).click()

def set_task_attr(attr, key, value=None):
	attr[key] = value

def del_task_attr(attr, key="_"):
	garbage = [k for k in attr.keys() if key in k]
	for item in garbage:
		x = attr.pop(item)
		del x

def check_iter_lists():
	selwrapper.log.debug("continue")

def iter_crwal_by_elm(dump, cb, backward, attr, sel):
	selwrapper.log.debug("")
	elm = None
	retcb = check_iter_lists
	curp = getattr(selwrapper, dump, None)

	selwrapper.log.debug("current number: %s" % curp)
	lastdata = attr.get("lastUpdate", 0)
	maxcount = sel.get('default').get("maxEntry")

	if (curp is not None) and backward: selwrapper.move_back()

	if (backward and curp == "end") or selwrapper.is_last_data(maxcount, lastdata):
		delattr(selwrapper, dump)
		return None

	if callable(cb): nxtp, elmclick = cb(curp, *[sel])

	if callable(elmclick): 
		elmclick()
		selwrapper.wait_implicit()

	if nxtp:
		setattr(selwrapper, dump, nxtp)
	else:
		if backward:
			setattr(selwrapper, dump, 'end')
		else:
			retcb = None
			if curp is not None: delattr(selwrapper, dump)		

	return retcb

def is_intime(day):
	retval = False

	week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	today = week[datetime.datetime.today().weekday()]

	selwrapper.log.debug("today is %s, input parmeter is %s" % (today, day))

	if (day == "Always") or (day == today): retval = True

	return retval

def sign_in_web(uin, callback):

	if selwrapper.login: return

	url = uin.get("in").get("url")
	uid = uin.get("user").get("id")
	upw = uin.get("user").get("pw")

	selwrapper.login(url, callback, uid, upw, *[uin.get("in")])

	return

def sign_out_web(uout, callback):
	if not selwrapper.login: return
	
	selwrapper.logout(callback, *[uout])
	
	return

def map_str_to_func(strlist):
	for key in sorted(strlist.keys()):
		if strlist.get(key) is None: continue
		if isinstance(strlist.get(key), dict):
			map_str_to_func(strlist.get(key))
		else:
			try:
				strlist[key] = globals()[strlist[key]]
			except:
				strlist[key] = None

def cb_mainloop(attr, sel):
	selwrapper.log.debug("notice task name is %s" % attr.get("name"))

	cb = attr.get("callback")
	map_str_to_func(cb)
	print(cb)
	selwrapper.recur_pages(cb, *[attr, sel])

	selwrapper.save_data(attr.get("result"))
	pdb.set_trace()
	if attr.get('tmpSave'): attr['lastUpdate'] = dict(selwrapper.get_data(0))
	selwrapper.del_data()

def recur_tasks(tgt, com):
	selwrapper.log.debug("")

	for item in tgt.get("lists"):
		if is_intime(item.get("period")) == False: continue
		if item.get("logon"): 
			sign_in_web(com.get("login"), find_elm_login)

		sel = dict()
		for key in item.get("selector"):
			sel.update({key:tgt.get('selector').get(key)})

		url = item.get("url")
		cb = cb_mainloop
		try:
			kcb = globals()[item.get("keyCallback")]
		except:
			kcb = None

		selwrapper.move_page(url, kcb, cb, *[item, sel])

	if com.get("login").get("out").get('autoLogout'): 
		sign_out_web(com.get("login").get("out"), find_elm_logout)

def main():

	global selwrapper, gbconf

	path = "D:\\business\\utility\\selenuim\\project\\gyeongBukProvGumiLib\\src\\gyeongBukProvGumi.json"

	utils = ProgUtils(path=path, logEnable=True)
	gbconf = utils.conf

	selwrapper = seleniumWrapper(utils.log)
	selwrapper.set_delay(gbconf.get("common").get("wait"))

	if gbconf.get("exec") is None: return

	common = gbconf.get("common")
	tasks = gbconf.get("exec")
	for task in tasks:
		target = gbconf.get(task)
		recur_tasks(target, common)

	utils.write_conf(path, gbconf)
	selwrapper.quit_driver()

	del selwrapper, utils

	return

if __name__ == "__main__":
	main()


