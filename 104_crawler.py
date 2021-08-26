# 第一部分為前置作業設定
from bs4 import BeautifulSoup
import requests
import time
import json
import csv
import re
import pandas as pd

# 宣告list並將使用到的list清空以免重複執行資料不正確
link = []
temp_url = []
word_list = []
url = []
init = []
key = []
info = []
update = []

# 讀取使用者設定
with open('./config.txt', 'r', encoding='utf-8') as f:
    conf = f.read().split("\n")
for i in range(len(conf)):
    init.append(conf[i].split('：')[1])
# print(init)

with open('./dict.txt', 'r', encoding='utf-8') as f:
    skill_dict = f.read().split('\n')

# 同義字的字典
# 功能 -> 遇到'人工智慧'時，想要用key,value的特性轉成'AI'
with open('./synonym.txt', 'r', encoding='utf-8') as f:
    syn = f.read().split('\n')
synonym_data = {}
for i in range(len(syn)):
    synonym_data.setdefault((syn[i].split(':')[0]), syn[i].split(':')[1])

# 將ro(是否只找全職工作)、keyword(關鍵字)、page(頁數)帶入網址，並存在新的list內
for page in range(1, int(init[1]) + 1):
    url.append(
        'https://www.104.com.tw/jobs/search/?ro={}&keyword={}&order=1&page={}&jobsource=2018indexpoc&'.format(init[2],
                                                                                                              init[0],
                                                                                                              page))

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    }

sync = ['Python', 'java', 'SQL', 'AI', 'data mining', 'Linux', 'ML', 'DL']
columns = ['area', 'company', 'job_title', 'content', 'experience', 'education', 'language ability', 'pay', 'welfare',
           'update', 'URL',
           'Python', 'java', 'SQL', 'AI', 'data mining', 'Linux', 'ML', 'DL']
df = pd.DataFrame(columns=columns)


# 工作內容、薪資、福利透過工作連結取得
def get_job_info(sub_soup):
    try:  # 擷取工作地點
        area = sub_soup.select('title')[0].text.split('｜')[2].split('－')[0]
    except:
        area = 'Area Error'
    try:  # 擷取公司名稱
        company = sub_soup.select('title')[0].text.split('｜')[1]
    except:
        company = 'Company Error'
    try:  # 擷取職稱
        title = sub_soup.select('title')[0].text.split('｜')[0]
    except:
        title = 'Title Error'
    try:  # 擷取工作經歷
        experience = sub_soup.find_all("table", class_="column2 condition")[0].text.split('工作經歷：\n')[1].split('\n\n')[0]
    except:
        Experience = 'Experience Error'
    try:  # 擷取學歷
        education = sub_soup.find_all("table", class_="column2 condition")[0].text.split('學歷要求：\n')[1].split('\n\n')[0]
    except:
        education = 'Education Error'
    try:  # 擷取語言能力
        language = sub_soup.find_all("table", class_="column2 condition")[0].text.split('語文條件：\n\n')[1].split('\n\n')[0]
    except:
        language = '不拘'
    try:  # 擷取薪資
        pay = sub_soup.select('div.content')[2].text.split('工作待遇：\n\n')[1].split('\n')[0]
    except:
        pay = 'Pay Error'
    try:  # 擷取福利
        welfare = sub_soup.select('div.content')[3].text
    except:
        welfare = 'welfare Error'
    try:  # 擷取工作內容
        content = sub_soup.select('div.content')[1].text
    except:
        content = 'Content Error'
    try:  # 擷取擅長工具，不一定有東西
        skill = sub_soup.find_all("table", class_="column2 condition")[0].text.split('擅長工具：\n')[1].split('\n\n')[0]
    except:
        skill = ' '
    try:  # 擷取其他條件，不一定有東西
        addition = sub_soup.find_all("table", class_="column2 condition")[0].text.split('其他條件：\n\n\n')[1]
    except:
        addition = ' '

    # return只會傳str，需要將上面取得之內容放進list內整個回傳， 否則會只回傳第一個字元
    tmp_list = [area, company, title, experience, education, re.sub(' ', '', language), re.sub(' ', '', pay),
                re.sub('[\n\t\r]', '', welfare), content, skill, re.sub('[\n\t\r]', '', addition)]
    return tmp_list[0], tmp_list[1], tmp_list[2], tmp_list[3], tmp_list[4], tmp_list[5], tmp_list[6], tmp_list[7], \
           tmp_list[8], tmp_list[9], tmp_list[10]


# 將同義詞的key值全轉成大寫後儲存新的字典以用來和同義詞做比對，value不變
new_dict = {}
for i, j in synonym_data.items():
    new_dict[i.upper()] = j
# print(new_dict)

# ========================透過session get訪問並透過html取得所需要的資訊 =========================
ss = requests.session()
for now_page in range(0, len(url)):
    print('開始第{}頁爬蟲'.format(now_page + 1))
    res = ss.get(url=url[now_page], headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    # 帶關鍵字送出request後會進到工作列表，此時可以透過article的class屬性擷取更新日期、進入工作頁面的連結
    soup2 = soup.find('div', {'id': 'js-job-content'}).findAll('article',
                                                               {
                                                                   'class': 'b-block--top-bord job-list-item b-clearfix js-job-item'})
    for job in soup2:
        update_date = job.find('span', {'class': 'b-tit__date'}).text
        update.append(re.sub('\r|\n| ', '', update_date))
        temp_url.append(
            job.find('a', {'class': 'js-job-link'})['href'].replace("//", "https://").split("?jobsource=")[0])  # 連結

    # =================================透過工作連結進入子頁面爬蟲============================================
    # 前面取到的網址改用使用手機板網址進行訪問(www改成m即可)
    # 將轉換過的html(sub_soup_main)帶入get_job_info的function中
    print('此頁面共找到{}筆資料'.format(len(temp_url)))
    for u in range(0, len(temp_url)):
        if (u % 5 == 0):
            print('休息5秒')
            time.sleep(5)
        print('進入職缺頁面{}取得更多資料'.format(u + 1))
        time.sleep(1)
        sub_res = ss.get(url=temp_url[u].replace("www", "m"), headers=headers)
        sub_soup_main = BeautifulSoup(sub_res.text, 'html.parser')
        area_tmp, company_tmp, title_tmp, exp_tmp, edu_tmp, language_tmp, pay_tmp, welfare_tmp, content_tmp, skill_tmp, addition_tmp = get_job_info(
            sub_soup_main)

        # "工作內容"直接存進輸出的列表中
        # 另外準備一個key_word_content將"工作內容"加上"擅長工具"、"其他條件"作為要篩選關鍵字的字串集合
        word_clean = (re.sub(r'[-:_0-9、【】：)(，.&+]', '', content_tmp)).replace('\n', '').replace('\r', ' ')
        key_word_content = word_clean + skill_tmp + addition_tmp

        link.append(temp_url[u])
        info.append([area_tmp, company_tmp, title_tmp, word_clean, exp_tmp, edu_tmp, language_tmp, pay_tmp, welfare_tmp,
                     update[u], temp_url[u]])

        # =================================關鍵字比對============================================

        # tmp用來暫存這個工作的找到的所有關鍵字，每次都要先清空
        tmp = []
        # 第一個判斷式將關鍵字的字串與工作內容比對，第二個判斷式再比對該字串是否出現在同義詞中，若有則將value存進tmp中，
        for b in range(len(skill_dict)):
            if skill_dict[b].upper() in key_word_content.upper():
                #                 print(skill_dict[b])
                if skill_dict[b].upper() in new_dict.keys():
                    tmp.append(new_dict[skill_dict[b].upper()])
                else:
                    tmp.append(skill_dict[b])
        # set作為資料結構，在設計上保證內部元素都是唯一的，會自動過濾重複資料，只要先轉換成set再轉回list就可以把重複的刪除
        word_list.append(list(set(tmp)))
    temp_url = []
# print('info=', info)

# =================================儲存關鍵字比對結果並存成list============================================
# 預設所有關鍵字為0，並加入到二維list中
for t in range(len(link)):
    key_tmp = []  # 每次都將list清空否則會不斷疊加
    for p in range(len(sync)):
        key_tmp.insert(p, 0)
    key.append(key_tmp)

    # 若符合list中的字串，則該位置將設成1，最後會得到一個關鍵字的二維表
    for k in word_list[t]:
        if k in sync:
            key[t][sync.index(k)] = 1
# print(key)

# 寫入dataframe
for u in range(0, len(link)):
     df.loc[u] = [info[u][0], info[u][1], info[u][2], info[u][3], info[u][4], info[u][5],
                  info[u][6], info[u][7], info[u][8], info[u][9], info[u][10],
                  key[u][0], key[u][1], key[u][2], key[u][3],
                  key[u][4], key[u][5], key[u][6], key[u][7]
                  ]
# 寫入CSV檔
df.to_excel("./104ETL_result.xlsx", encoding='utf-8', index=False)
