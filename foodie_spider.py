import re
import scrapy
from scrapy.http import Request

class FoodieSpider(scrapy.Spider):
    name = 'foodie'

    def start_requests(self):
        start_urls = ['https://www.evernote.com/shard/s52/sh/5f447ac8-7b82-4cf4-8395-9daa558178aa/c48e93d480fbe734?content=']
        requests = []
        for item in start_urls:
            requests.append(Request(url=item, headers={
                'Referer': 'https://www.evernote.com/shard/s52/sh/5f447ac8-7b82-4cf4-8395-9daa558178aa/c48e93d480fbe734'
            }))
        return requests
    

    def parse(self, response):
        for resto in response.css('#note-frame-body > div > div > div'):
            contents = resto.css("::text").extract()
            checked  = resto.css("input::attr(checked)").extract_first() 
            contstr  = re.sub('\xa0', ' ', ''.join(contents)) # replace &nbsp;-equivs

            try:
                sind = contstr.index('(')
                (venue, comment) = (contstr[0:sind].strip(), contstr[sind:].strip())
            except:
                try:
                    sind = contstr.index(' - ')
                    (venue, comment) = (contstr[0:sind].strip(), contstr[(sind + 3):].strip())
                except:
                    (venue, comment) = (contstr, '')

            visited  = True if checked == 'true' else False

            yield {
                'visited' : visited,
                'venue'   : venue,
                'comment' : comment
            }
