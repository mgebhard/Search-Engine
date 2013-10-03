import webapp2
import jinja2
import logging
import os
from google.appengine.api import urlfetch
import HTMLParser
import re
from google.appengine.ext import ndb


jinja_environment = jinja2.Environment(loader=
    jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Link(ndb.Model):
    url = ndb.StringProperty(required=True)
    html = ndb.TextProperty()
    links = ndb.StringProperty()
    # words = ndb.StringProperty()
    # title = ndb.StringProperty()
    # times_visted = ndb.IntegerProperty()

def RenderTemplate(template, template_values):
    template = jinja_environment.get_template(template)
    return template.render(template_values)


def FetchHtml(url):
    if not url.startswith('http'):
        url = 'http://' + url
    result = urlfetch.fetch(url)
    return result.content


class HomeHandler(webapp2.RequestHandler):
    def get(self):
        html = RenderTemplate('home.html', {})
        self.response.out.write(html)

class SearchHandler(webapp2.RequestHandler):
    def get(self):
        url = self.request.get('url')
        if url: 
            self.Fetch(url)    
        else:
            html = RenderTemplate('results.html', {})
            self.response.out.write(html)




    def Fetch(self, url):
        html = FetchHtml(url)
        links = self.GetLinks(html)
        title = self.GetTitle(html)
        # for link in links:
        #     self.Fetch(link)

        self.response.out.write(
            RenderTemplate('results.html', 
            {'characters': len(html),
             'words': len(html.split()),
             'links': links,
             'title': title,
             'link_number': len(links)}))

    def GetLinks(self, html):
        parser = LinksParser()
        parser.feed(html)
        return parser.urls        

    def GetTitle(self, html):
        match = re.search(r'\<title[^>]*\>(.*)\<\/title\>', html)
        if match: 
            return match.group(1)


class LinksParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.recording = 0
        self.urls = []

    def handle_starttag(self, tag, attributes):
        if tag =='a':
            for name, value in attributes:
                if name == 'href':
                    if value[0:4] == 'http' or value[0:2]=='//':
                        if value not in self.urls:
                            self.urls.append(value)
                            logging.info(value)

        if self.recording:
            self.recording += 1
            return
        
        self.recording = 1

    def handle_endtag(self, tag):
        if tag == 'a' and self.recording:
            self.recording -= 1



class ResultsHandler(webapp2.RequestHandler):
    def get(self):
        url = str(self.request.get('url'))
        html = FetchHtml(url)
        logging.info(url)
        link = Link.query().filter(Link.url == url).get()
        logging.info(link)
        if not link:
            link = Link(url=url, html=html)
            link.put()

        self.response.out.write(self.redirect(url))



routes = [
    ('/results', SearchHandler),
    ('/home', HomeHandler),
    ('/content', ResultsHandler)
]

app = webapp2.WSGIApplication(routes, debug=True)

