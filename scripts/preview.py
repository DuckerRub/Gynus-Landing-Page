#!/usr/bin/env python3
"""Preview static files with the GitHub Pages custom 404 behavior."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parent.parent
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
 def send_error(self,code,message=None,explain=None):
  if code!=404:return super().send_error(code,message,explain)
  body=(ROOT/'404.html').read_bytes();self.send_response(404);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers()
  if self.command!='HEAD':self.wfile.write(body)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=3456);args=p.parse_args()
 print(f'Preview: http://127.0.0.1:{args.port}',flush=True)
 ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
