#这是注释
#coding=utf-8

import urllib
from urllib.request import Request, urlopen,ProxyHandler,install_opener,build_opener,urlretrieve
from urllib.error import URLError, HTTPError
import os
import re
import mysql.connector
import time
import random
import threading

class GZHDog:

	"""公号狗，采集热门微信公众号及文章"""
	def __init__(self):		
		self.proxies = [None];	
		self.tables = {
			'gzh':'wx_gzh',
			'category':'wx_category',
			'rank':'wx_rank',
			'articles':'wx_articles',
			'links':'wx_links'
		}	
		self.db = mysql.connector.connect(host='localhost', user='root',passwd='',db='ghdog')
		self.headers = {
			'Cookie':"CXID=6CEE5629E1BF55D2E40EE2D9C0C4A1D2; SUV=00D63EB5DEBCB88056D6965198B0C521; SMYUV=1456970125498784; IPLOC=CN3204; GOTO=; wuid=AAFrS3U6EAAAAAqIIKs7qg0AGwY=; ssuid=1407717706; sgsa_id=sogou.com|1459218739482250; pgv_pvi=5612616704; ABTEST=0|1472541927|v1; weixinIndexVisited=1; cd=1474188456&d1a01043ec36613207024d3042dee719; ld=kyllllllll2guhgelllllVKkfM1llllltmnCSyllllwlllllVllll5@@@@@@@@@@; SUIR=4B4B22BDC5C1F8D784C9098AC5F52B6D; SNUID=C1781588F2F7CF7511616A93F28CAF7A; ad=glllllllll2g03Y7qdiU$VKr2yOgTOvoNFMiMZlllxklllll4Vxlw@@@@@@@@@@@; SUID=DAD474B44D6C860A56D3BB1E00054204; JSESSIONID=aaawo7LJ1zLvLchdn5IAv; sct=54; LSTMV=772%2C76; LCLKINT=5222",
			'User-Agent':"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.89 Safari/537.36"
		}
		self.__wzs_headers = {'cookie':'PHPSESSID=jaani4j1gfqm8qahle9tbok9t1; u=eE9UTXpVZ3hORGN6TVRReE5qWTQ%3D; Hm_lvt_f4e1e6802d0e71229503ea0d06d0fd16=1473141532; Hm_lpvt_f4e1e6802d0e71229503ea0d06d0fd16=1473213003'}
		self.__createTables()
		# proxy_support = ProxyHandler({'http':'http://112.81.100.102:8888'})
		# opener = build_opener(proxy_support)
		# opener.addheaders = [('User-Agent','Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.89 Safari/537.36')]
		# install_opener(opener)

	#创建数据表
	def __createTables(self):
		db = self.db
		cursor = db.cursor()
		sql = '''
				CREATE TABLE IF NOT EXISTS wx_gzh (
				wx_id varchar(32) NOT NULL,
				name varchar(32) NOT NULL,
				ori_avatar varchar(128) NOT NULL,
				avatar varchar(128) NOT NULL,
				profile varchar(256) NOT NULL,
				auth varchar(32) NOT NULL,
				qrcode varchar(128) NOT NULL,
				timestamp datetime NOT NULL,
				PRIMARY KEY (wx_id)
				);

				CREATE TABLE IF NOT EXISTS wx_articles (
				id int(11) NOT NULL AUTO_INCREMENT,
				wx_id varchar(32) NOT NULL,
				ori_url varchar(128) NOT NULL,				
				article_title text NOT NULL,	
				article_author varchar(64) NOT NULL,			
				article_excerpt text NOT NULL,	
				article_content text NOT NULL,			
				article_copyright int(1) DEFAULT 0,
				article_date datetime NOT NULL,
				PRIMARY KEY (id)
				);

				CREATE TABLE IF NOT EXISTS wx_category (
				id int(11) NOT NULL,
				name varchar(32) NOT NULL,
				PRIMARY KEY (id)
				) ;

				CREATE TABLE IF NOT EXISTS wx_rank (
				id int(11) NOT NULL AUTO_INCREMENT,
				wx_id varchar(32) NOT NULL,
				cat_id int(5) NOT NULL,
				rank int(5) NOT NULL,
				PRIMARY KEY (id)
				);

				CREATE TABLE IF NOT EXISTS wx_links (
				id int(11) NOT NULL AUTO_INCREMENT,
				link_id varchar(15) NOT NULL,
				link_status int(2) DEFAULT 0 NOT NULL,
				link_date datetime NOT NULL,
				PRIMARY KEY (id)
				);
				-- ALTER TABLE wx_links ADD UNIQUE link_id (link_id);
			'''		
		# 一次性创建所有表	
		for s in cursor.execute(sql, multi=True): pass
		cursor.close()				

	def __requestPage(self,url,headers=None):
		if(url):			
			req = Request(url,headers=headers)
			try:
				response = urlopen(req,timeout=1000)			
			except HTTPError as e:
				print(e)
			except URLError as e:
				print(e)				
			else:
				content=response.read().decode("utf8")
				return content

	#获取微信公众号分类
	def fetchWeixinCategory(self):
		db = self.db
		cursor = db.cursor()
		url = "http://www.weizhishu.com/hotlist/account"
		headers = self.__wzs_headers;
		content = self.__requestPage(url,headers);
		if content:
			pattern=re.compile('<li >\s*<a href="\?gid=(.*?)">\s*<!--\s*<img src="/img/d-xh.png" alt=""/>\s*-->\s*(.*?)\s*</a>\s*</li>',re.S)
			items = re.findall(pattern,content)			
			sql = 'insert into wx_category(id,name) values(%s,%s)'
			if len(items):
				try :
					cursor.executemany(sql,items)
					db.commit()					
					cursor.close()
				except:
					db.rollback()

	#获取微信公众号分类排行榜
	def fetchWeixinRank(self):
		db = self.db;
		headers = self.__wzs_headers;
		tables = self.tables
		cursor = db.cursor()		
		sql = 'select id from '+tables['category'];
		cursor.execute(sql)
		results = cursor.fetchall()
		if(len(results)):
			for i in results:
				gid = str(i[0])
				url = 'http://www.weizhishu.com/hotlist/account?gid='+gid;				
				content = self.__requestPage(url,headers)
				if content:
					pattern=re.compile('<em>([\d]{1,3})</em>.*?<div class="name"><a.*?>.*?<span>(.*?)</span></a></div>',re.S)
					items = re.findall(pattern,content)
					if(len(items)):
						sql = "insert into "+tables['rank']+'(rank,wx_id,cat_id) values(%s,%s,'+gid+')'			
						try:
							cursor.executemany(sql,items)
							db.commit()
						except:
							db.rollback()
				else:
					continue
		cursor.close()


	#查找热门微信公众号
	#@param {int} pageCount 最多获取多少页的微信公众号
	#@return {list} 返回微信号列表[(ranking,id),(ranking,id)]
	def getHotWeixinhao(self,pageCount):
		pageIndex = 0
		wList = []
		while pageIndex<pageCount:			
			url = "http://www.weizhishu.com/hotlist/account?gid=0&p="+str(pageIndex+1)
			headers = {'cookie':'PHPSESSID=jaani4j1gfqm8qahle9tbok9t1; u=eE9UTXpVZ3hORGN6TVRReE5qWTQ%3D; Hm_lvt_f4e1e6802d0e71229503ea0d06d0fd16=1473141532; Hm_lpvt_f4e1e6802d0e71229503ea0d06d0fd16=1473213003'}
			req = Request(url,headers=headers)			
			try:
				response = urlopen(req,timeout=1000)	
				urlopen			
			except HTTPError as e:
				print('HTTP错误')
			except URLError as e:
				print('We failed to reach a server.'+e.reason)				
			else:
				content=response.read().decode("utf8")
				pattern=re.compile('<em>([\d]{1,3})</em>.*?<div class="name"><a.*?>.*?<span>(.*?)</span></a></div>',re.S)
				items = re.findall(pattern,content)
				wList.extend(items);
				pageIndex+=1
		return wList
	
	#查询信息不足的微信号
	def __getEmptyGongzhonghao(self):
		cursor = self.db.cursor()
		sql = "select id from gongzhonghao where name='' and isNull(profile)"
		try:
			cursor.execute(sql)
			results = cursor.fetchall()
			cursor.close()	
			return results
		except:
			print("查询出错")
			return None		

	#根据rank表去抓取所需的公众号信息
	def fetchRankGongzhonghao(self):		
		cursor = self.db.cursor()
		#查找出所有的公众号ID
		sql = "select wx_id from "+self.tables['gzh'];		
		try:
			cursor.execute(sql)
			results = cursor.fetchall()
			tup_wx_id = ()
			for v in results:
				tup_wx_id+=v
			sql = 'select wx_id from '+self.tables['rank']+' where wx_id not in '+str(tup_wx_id)
			cursor.execute(sql)
			wxList = cursor.fetchall()
		except:
			print("查询出错")		
		for wx in wxList:
			data = self.findGongzhonghao(wx[0])
			if(data):			
				self.__addGongzhonghao(data)
				print(data[1]+"采集成功")


	"""
	获取微信公众号文章地址列表
	@param {string} wx_id 公众号ID {int} page 从第几页开始采集 {int} end_page 采集到第几页结束
	"""
	def __fetchArticleLinks(self,wx_id,page = 0,end_page=5):
		page = page
		db = self.db
		cursor = db.cursor()		
		url = 'http://chuansong.me/account/%s?start=%s' % (wx_id,12*page)
		# 休息3秒开始采集			
		time.sleep(3)
		content = self.__requestPage(url,{'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.89 Safari/537.36'})
		if(content):
			pattern = re.compile('<a class="question_link" href="/n/(.*?)" target="_blank">.*?</a>.*?<span class="timestamp" style="color: #999">(.*?)</span>',re.S)	
			items = re.findall(pattern,content)
			if(len(items) and page<end_page):
				page = page+1
				print('%s:开始采集第%s页文章链接' % (wx_id,page))
				print(items)
				try:
					sql = 'insert into '+self.tables['links']+'(link_id,link_date) values(%s,%s)'
					cursor.executemany(sql,items)
					db.commit()
					cursor.close()					
					print('第%s页采集完成' % page)
					self.__fetchArticleLinks(wx_id,page)
				except Exception as e:
					db.rollback()
					print(e)
					self.__fetchArticleLinks(wx_id,page)


	"""
	根据公众号去传送门采集文章
	@param {string} link_id 文章链接ID
	"""
	def __fetchArticle(self,link_id):
		#睡眠3秒后再采集文章
		time.sleep(3)
		url = 'http://chuansong.me/n/%s' % link_id;
		content = self.__requestPage(url,{'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.89 Safari/537.36'})
		pattern = re.compile('<h2 class="rich_media_title" id="activity-name">\s+(.*?)\s*</h2>\s+<div class="rich_media_meta_list">[\s\S]*?<em class="rich_media_meta rich_media_meta_text" id="post-date">(.*?)<\/em>\s<em class="rich_media_meta rich_media_meta_text">(.*?)<\/em>\s+<a class="rich_media_meta rich_media_meta_link rich_media_meta_nickname" href="/account/(.*?)" id="post-user">.*?</a>[\s\S]*?<div class="rich_media_content " id="js_content">\s+([\s\S]*?)<\/div>\s')			
		pattern_b = re.compile('<h2 class="rich_media_title" id="activity-name">\s+(.*?)\s*</h2>\s+<div class="rich_media_meta_list">[\s\S]*?<em class="rich_media_meta rich_media_meta_text" id="post-date">(.*?)<\/em>\s+()<a class="rich_media_meta rich_media_meta_link rich_media_meta_nickname" href="/account/(.*?)" id="post-user">.*?</a>[\s\S]*?<div class="rich_media_content " id="js_content">\s+([\s\S]*?)<\/div>\s')			
		tag_pattern = re.compile('<span class="rich_media_meta meta_original_tag" id="copyright_logo">.*?</span>');
		if(content):
			match = pattern.search(content)	
			if(match is None):
				match = pattern_b.search(content)	
			if(match):
				'''
					t = match.groups(); title = t[0] date = t[1] author = t[2] wx_id = t[3] cont = t[4]					
				'''
				article = match.groups()
				tm = tag_pattern.search(content)
				if(tm):
					#(1,)表示原创文章
					article +=(1,link_id)
				else:
					article +=(0,link_id)
				return article
			else:
				print('%s:无法匹配文章'%link_id)
				return None
		else:
			print('%s:无法获取网页内容'%link_id)
			return None

	'''
	保存文章
	@param {tuple} article
	'''
	def __saveArticle(self,article):
		db = self.db
		tables = self.tables
		cursor = db.cursor()
		if(article):			
			title = article[0].replace('"','\\"')
			date  = article[1]
			author = article[2]
			wx_id = article[3]
			content = article[4].replace('"','\\"')
			copyright = article[5]
			ori_url = article[6]			
			#检查文章是否已经插入 
			sql = 'select count(*) from '+self.tables['articles']+' where article_title="%s" and wx_id="%s"' % (title,wx_id)			
			cursor.execute(sql)
			results = cursor.fetchall()

			#返回的数据格式[(0,)]
			if(results[0][0]==0):
				try:
					sql = 'insert into '+self.tables['articles']+'(ori_url,article_title,article_date,article_author,wx_id,article_content,article_copyright) values("%s","%s","%s","%s","%s","%s","%s")' % (ori_url,title,date,author,wx_id,content,copyright)
					cursor.execute(sql)
					db.commit()
					print('文章已经保存:%s' % title)
				except Exception as e:
					print(e)
					db.rollback()
			else:
				print('文章已存在:%s'%title)
		else:
			print('文章不存在')
		cursor.close()

	"""
	更新link_status
	"""
	def __updateLinkStatus(self,link_id,status=1):
		db = self.db
		cursor = db.cursor()
		#将link_status修改为1，表示文章已经采集过
		sql = 'update '+self.tables['links']+' set link_status=%d where link_id=%s' % (status,link_id)
		try:
			cursor.execute(sql)
			db.commit()
		except Exception as e:
			print(e)
			db.rollback()
		cursor.close()
	"""
	通过搜狗查询公众号详细信息
	@param {string} wid 公众号ID
	"""
	def findGongzhonghao(self,wid):
		url = 'http://weixin.sogou.com/weixin?type=1&query='+wid+'&ie=utf8&_sug_=n&_sug_type_='
		headers = self.headers
		req = Request(url,None,headers)
		try:
			response = urlopen(req)
		except HTTPError as e:
			print('The server couldn\'t fulfill the request.')
			print('Error code: ', e.code)
			return None
		except URLError as e:
			print('We failed to reach a server.')
			print('Reason: ', e.reason)
		else:
			content=response.read().decode("utf8")
			pattern=re.compile('<div class="img-box">.*?<img.*? src="(.*?)".*?>.*?<h3>(.*?)</h3>.*?<label name="em_weixinhao">(.*?)</label>(.*?<span class="sp-tit">功能介绍：</span><span class="sp-txt">(.*?)</span>[\s]+</p>|)([\s]+<p class="s-p3">[\s]+<span class="sp-tit"><script>.*?</script>认证：</span><span class="sp-txt">(.*?)</span>|)',re.S)			
			match = re.search(pattern,content)				
			if match:
				return match.groups()
			else:
				return None			
	
	#添加新的公众号
	def __addGongzhonghao(self,data):
		if(data and len(data)):
			ori_avatar = data[0]
			name = data[1]
			wx_id = data[2]
			profile = data[4]or""
			auth = data[6]or""
			db = self.db
			cursor = db.cursor();
			sql = "insert into "+self.tables["gzh"]+" set wx_id='%s', name='%s', ori_avatar='%s',profile='%s',auth='%s',timestamp='%s' "%(wx_id,name,ori_avatar,profile,auth,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()));
			try:
			   # 执行SQL语句
			   cursor.execute(sql)
			   # 提交到数据库执行
			   db.commit()
			except:
			   # 发生错误时回滚
			   db.rollback()
	
	#更新公众号头像
	def __updateAvatar(self,wx_id,img_url):
		if(wx_id and img_url):
			db = self.db
			cursor = db.cursor();			
			sql = "update "+self.tables['gzh']+" set avatar ='%s' where wx_id='%s'" % (img_url,wx_id)
			try:
				cursor.execute(sql)
				db.commit()
				cursor.close()
			except :
				db.rollback


	#更新公众号信息
	def __updateGongzhonghao(self,data):
		if(data and len(data)):
			ori_avatar = data[0]
			name = data[1]
			wid = data[2]
			profile = data[4]or""
			auth = data[6]or""
			db = self.db
			cursor = db.cursor();
			sql = "update "+self.tables['gzh']+" set name='%s', ori_avatar='%s',profile='%s',auth='%s',timestamp='%s' where id='%s'"%(name,ori_avatar,profile,auth,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),wid);
			try:
			   # 执行SQL语句
			   cursor.execute(sql)
			   # 提交到数据库执行
			   db.commit()
			except:
			   # 发生错误时回滚
			   db.rollback()

	def get_proxy(self):	    
		proxies = self.proxies
		headers = self.headers
		try:
			req = Request('http://www.xicidaili.com/',None,headers)
		except:
			print('无法获取代理信息!')
			return
		response = urlopen(req)
		html = response.read().decode('utf-8')
		p = re.compile(r'''<tr\sclass[^>]*>\s+
			<td\sclass[^>]*>.+</td>\s+
			<td>(.*)?</td>\s+
			<td>(.*)?</td>\s+
			<td>(.*)?</td>\s+
			<td\sclass[^>]*>(.*)?</td>\s+
			<td>(.*)?</td>\s+
			<td>(.*)?</td>\s+
			<td>(.*)?</td>\s+
			</tr>''',re.X)
		proxy_list = p.findall(html)
		for each_proxy in proxy_list[1:]:
			if each_proxy[4] == 'HTTP':
				proxies.append(each_proxy[0]+':'+each_proxy[1])	
							
	def change_proxy(self):
	    # 随机从序列中取出一个元素
	    proxies = self.proxies
	    headers = self.headers
	    proxy = random.choice(proxies)
	    # 判断元素是否合理
	    if proxy == None:
	        proxy_support = ProxyHandler({})
	    else:
	        proxy_support = ProxyHandler({'http':proxy})
	    opener = build_opener(proxy_support)
	    opener.addheaders = [('User-Agent',headers['User-Agent'])]
	    install_opener(opener)
	    print('智能切换代理：%s' % ('本机' if proxy==None else proxy))
	


	#显示文件下载进度  
	def __schedule(self,a,b,c):  
		''' 
		a:已经下载的数据块 
		b:数据块的大小 
		c:远程文件的大小 
		'''  
		per = 100.0 * a * b / c  
		if per > 100 :  
		    per = 100  
		print ('%.2f%%' % per )


	"""
		下载图片到本地
	"""
	def __downloadImg(self,url): 
		'''
		图片url格式"http://img01.sogoucdn.com/app/a/100520090/oIWsFtw53Ls8D6DZ6mvxn0UaAoPU"
		直接拿地址最后一段oIWsFtw53Ls8D6DZ6mvxn0UaAoPU作为图片名称
		'''
		if url:
			pic_name = url.split('/')[-1]

			#定义文件夹的名字  
			t = time.localtime(time.time())  		 
			picpath = 'E:\\workspace\\gongzhonghao\\public\\static\\avatar' #下载到的本地目录  
			  
			if not os.path.exists(picpath):   #路径不存在时创建一个  
			    os.makedirs(picpath)      
			path = picpath+'\\%s.jpg' %  pic_name	
			rel_path = "/static/avatar/%s.jpg" % pic_name	
			image = urlretrieve(url, path, self.__schedule) 		
			return rel_path; 


	def startFetchArticleLinks(self):
		db = self.db
		cursor = db.cursor()
		sql = 'select wx_id from %s ' % self.tables['gzh']
		cursor.execute(sql)		
		result = cursor.fetchall()		
		if(len(result)):
			for item in result:
				wx_id = item[0]
				self.__fetchArticleLinks(wx_id)	

	def startFetchArticles(self):
		#print(self.__fetchArticle('570062448370'))
		db = self.db
		cursor = db.cursor()
		sql = 'select link_id from '+self.tables['links']+' where link_status=0'
		cursor.execute(sql)
		result = cursor.fetchall()		
		if(len(result)):
			for item in result:					
				link_id = item[0]	
				article = self.__fetchArticle(link_id)
				if(article):					
					self.__saveArticle(article)
					self.__updateLinkStatus(link_id)
				else:
					#link_status=2表示该链接无效
					self.__updateLinkStatus(link_id,2)












				
