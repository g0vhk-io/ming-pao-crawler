import sys
import requests
import execjs
import json
import multiprocessing
import functools


def fetch(item, d, e):
    url = item['link']
    path_last = url.split("/")[-1]
    js_url = "http://news.mingpao.com/dat/pns/pns_web_tc/article1/%s%s/todaycontent_%s.js" % (d, e, path_last)
    r = requests.get(js_url)
    r.encoding = "utf-8"
    try:
        j = r.json()
        item['text'] = j['DESCRIPTION']
        return item
    except Exception as e:
        print("Something wrong at " + js_url + " " + url)
        print(j.text)
        raise e

if __name__ == '__main__':
    issue_list = requests.get('http://news.mingpao.com/dat/pns/issuelist.js').json()
    d = sys.argv[1]
    e = issue_list['PNS_WEB_TC']['1 ' + d]['E'].lower()
    url = "http://news.mingpao.com/dat/pns/pns_web_tc/feed1/%s%s/content.js" % (d, e)
    js = requests.get(url).text
    line = "function foo(){ \n" + js.split('\n')[2][0:-2].replace("feed2['content_%s%s']=" % (d, e), 'return ') +"}"
    ctx = execjs.compile(line)
    items = []  
    output = ctx.call("foo")
    for k in output.keys():
        for item in output[k]['rss']['channel']['item']:
            if item['LINK'].find('s00018') != -1 or item['LINK'].find('s00021') != -1:
                continue

            media_group = item.get('media:group', None)
            image = None
            if media_group is not None:
                media_content = next((x for x in media_group if 'media:content' in x), None)
                if media_content is not None:
                    image_element = media_content['media:content'][-1]
                    image = "http://fs.mingpao.com/" + image_element['ATTRIBUTES']["URL"]
            author = item['AUTHOR']
            title = item['TITLE']
            link = "http://news.mingpao.com" + item['LINK']
            description = item['DESCRIPTION']
            if title not in [u'要聞',u'港聞',u'社評‧筆陣',u'論壇',u'中國',u'國際',u'經濟',u'體育',u'影視',u'副刊',u'英文']:
                #print("%s,%s,%s,%s" % (author, title, link, description))
                items.append({'author': author, 'title': title, 'link': link, 'description': description, 'image': image, 'date': d})
    print(items) 
    pool = multiprocessing.Pool()
    items = pool.map_async(functools.partial(fetch, d=d, e=e), items).get()
    with open(sys.argv[2], 'w') as f:
        f.write(json.dumps(items, indent=4))
