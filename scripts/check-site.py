#!/usr/bin/env python3
"""Dependency-free static checks; optionally verify the same files on a live host."""
import argparse, hashlib, json, re, sys, urllib.request, urllib.error
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://gynus.fit'
# Baseline: main at 40b3a0d, including the concurrently shipped import handoff.
PROTECTED = {
 'import-plan/index.html': 'd3adcad6ff2c0867b31378d225fa94f4ef25f48b9d687a77d14e69f1d8a15708',
 '404.html': '38fa7e74c3838ea7284c54ba960a6d2f3663fae73823fd31eb24e3aa7dcb623b',
 '.well-known/apple-app-site-association': '812a804b9979c67db0a16f59f831574cf9224e9915587218d83521a620a6b477',
 '.well-known/assetlinks.json': 'dc53122b02a1179e67b395e644f58015a5bcc201e4497ef733b10c9b289dbbce',
 'CNAME': 'e01b9445105e5a34511945204a5253132e33f44c9ae4d2cf7222c365ef373a4f',
 '.nojekyll': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
}
class Page(HTMLParser):
 def __init__(self,text):
  super().__init__(); self.tags=[]; self.feed(text)
 def handle_starttag(self,tag,attrs): self.tags.append((tag,dict(attrs)))
 def find(self,tag,**attrs): return [a for t,a in self.tags if t==tag and all(a.get(k)==v for k,v in attrs.items())]

def file_for(path):
 p=ROOT/unquote(path).lstrip('/'); return p/'index.html' if p.is_dir() or path.endswith('/') else p

def check():
 for f,digest in PROTECTED.items(): assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest, f'Protected file changed: {f}'
 assert not (ROOT/'join-group').exists(), 'Do not shadow the deep-link fallback'
 urls=[n.text for n in ET.parse(ROOT/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
 assert len(urls)==len(set(urls))
 for f in ROOT.rglob('*.html'):
  if '.git' in f.parts: continue
  page=Page(f.read_text())
  if any('noindex' in a.get('content','') for a in page.find('meta',name='robots')): continue
  path='/' + f.relative_to(ROOT).as_posix()
  if path.endswith('/index.html'): path=path[:-10]
  assert BASE+path in urls, f'Indexable page missing from sitemap: {f}'
 titles=set(); descriptions=set()
 for url in urls:
  assert url.startswith(BASE+'/') and not urlsplit(url).query
  path=urlsplit(url).path
  assert not any(x in path for x in ['404','join-group','import-plan','.well-known'])
  f=file_for(path); text=f.read_text(); page=Page(text)
  assert page.find('link',rel='canonical')==[{'rel':'canonical','href':url}],f'{path}: canonical'
  assert not any('noindex' in a.get('content','') for a in page.find('meta',name='robots'))
  title=re.search(r'<title>(.*?)</title>',text,re.S).group(1)
  desc=page.find('meta',name='description')[0]['content']
  assert title not in titles and desc not in descriptions, f'{path}: duplicate metadata'
  titles.add(title); descriptions.add(desc)
  for prop in ['og:title','og:description','og:url','og:image']:
   assert len(page.find('meta',property=prop))==1,f'{path}: {prop}'
  assert page.find('meta',property='og:url')[0]['content']==url
  for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S):
   data=json.loads(block); assert data['@context']=='https://schema.org'
  if path in ['/','/pt-br/','/es/']:
   expected={'en':BASE+'/','pt-BR':BASE+'/pt-br/','es':BASE+'/es/','x-default':BASE+'/'}
   assert {a['hreflang']:a['href'] for a in page.find('link',rel='alternate')}==expected
  if path.endswith('/'):
   assert len(page.find('h1'))==1
   assert not re.search(r'<script(?! type="application/ld\+json")',text)
   assert 'navigator.language' not in text and 'data-i18n' not in text
   expected='pt-BR' if path.startswith('/pt-br/') else 'es' if path=='/es/' else 'en'
   assert page.find('html')[0]['lang']==expected
   assert all(a.get('alt') and a.get('width') and a.get('height') for a in page.find('img'))
  for tag,attrs in page.tags:
   for attr in ['href','src']:
    href=attrs.get(attr,''); resolved=urlsplit(urljoin(url,href))
    if not href or resolved.netloc not in ['', 'gynus.fit'] or resolved.scheme not in ['','http','https']: continue
    target=file_for(resolved.path); assert target.is_file(), f'{path}: missing {href}'
    if resolved.fragment and target.suffix=='.html':
     assert any(a.get('id')==resolved.fragment for _,a in Page(target.read_text()).tags),f'{path}: missing fragment {href}'
 robots=(ROOT/'robots.txt').read_text()
 assert 'User-agent: OAI-SearchBot' in robots and 'User-agent: *' in robots
 assert f'Sitemap: {BASE}/sitemap.xml' in robots
 policy=RobotFileParser(); policy.parse(robots.splitlines())
 for agent in ['OAI-SearchBot','GPTBot','Googlebot','bingbot','Claude-SearchBot','PerplexityBot']:
  assert all(policy.can_fetch(agent,url) for url in urls), f'Crawler blocked: {agent}'
  assert not policy.can_fetch(agent,BASE+'/docs/launch-kit.md'), f'Internal docs unexpectedly crawlable: {agent}'
 for handoff in ['404.html','import-plan/index.html']:
  assert any('noindex' in a.get('content','') for a in Page((ROOT/handoff).read_text()).find('meta',name='robots'))
 print(f'PASS: {len(urls)} pages; metadata, language, links, structured data, sitemap, and protected files')
 return urls

def live(host,urls):
 paths=[urlsplit(u).path for u in urls]+['/index.html','/?ref=seo-check','/pt-br/index.html','/es/index.html','/import-plan/','/robots.txt','/sitemap.xml','/.well-known/apple-app-site-association','/.well-known/assetlinks.json']
 tests=[(p,200) for p in paths]+[(p,404) for p in ['/join-group/ABCDEFGHIJ','/join-group/'+'A'*32+'/?source=check','/join-group/short','/not-a-real-page-seo-check']]
 for path,status in tests:
  try: response=urllib.request.urlopen(host.rstrip('/')+path,timeout=25)
  except urllib.error.HTTPError as exc: response=exc
  assert response.status==status, f'{path}: expected {status}, got {response.status}'
  body=response.read()
  target=ROOT/'404.html' if status==404 else file_for(urlsplit(path).path)
  assert body==target.read_bytes(), f'{path}: served body differs from local file'
  if path=='/robots.txt': assert 'text/plain' in response.headers['Content-Type']
  if path=='/sitemap.xml': assert 'xml' in response.headers['Content-Type']
 print(f'PASS: {len(tests)} live responses on {host}; bodies and deep-link 404s match')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--live',help='Base URL, e.g. https://gynus.fit');args=parser.parse_args()
 urls=check()
 if args.live: live(args.live,urls)
