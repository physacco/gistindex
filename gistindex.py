# encoding: utf-8

import sys
import json
import getopt
import jinja2
import urllib

IndexTmpl = jinja2.Template("""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{user}}'s gists</title>
  <style type="text/css">
h1 {
    margin: 20px;
    text-align: center;
}
table a:link {
	color: #666;
	font-weight: bold;
	text-decoration:none;
}
table a:visited {
	color: #999999;
	font-weight:bold;
	text-decoration:none;
}
table a:active,
table a:hover {
	color: #bd5a35;
	text-decoration:underline;
}
table {
	font-family:Arial, Helvetica, sans-serif;
	color:#666;
	font-size:12px;
	text-shadow: 1px 1px 0px #fff;
	background:#eaebec;
	margin:20px;
	border:#ccc 1px solid;

	-moz-border-radius:3px;
	-webkit-border-radius:3px;
	border-radius:3px;

	-moz-box-shadow: 0 1px 2px #d1d1d1;
	-webkit-box-shadow: 0 1px 2px #d1d1d1;
	box-shadow: 0 1px 2px #d1d1d1;
}
table th {
    padding: 12px;
	border-top:1px solid #fafafa;
	border-bottom:1px solid #e0e0e0;
	border-left:1px solid #d7d7d7;

	background: #ededed;
	background: -webkit-gradient(linear, left top, left bottom, from(#ededed), to(#ebebeb));
	background: -moz-linear-gradient(top,  #ededed,  #ebebeb);
}
table th:first-child {
	text-align: left;
	padding-left:10px;
}
table tr:first-child th:first-child {
	-moz-border-radius-topleft:3px;
	-webkit-border-top-left-radius:3px;
	border-top-left-radius:3px;
}
table tr:first-child th:last-child {
	-moz-border-radius-topright:3px;
	-webkit-border-top-right-radius:3px;
	border-top-right-radius:3px;
}
table tr {
	padding-left:20px;
}
table td:first-child {
	text-align: left;
	padding-left:10px;
	border-left: 0;
}
table td {
	padding:10px;
	border-top: 1px solid #ffffff;
	border-bottom:1px solid #e0e0e0;
	border-left: 1px solid #e0e0e0;
	
	background: #fafafa;
	background: -webkit-gradient(linear, left top, left bottom, from(#fbfbfb), to(#fafafa));
	background: -moz-linear-gradient(top,  #fbfbfb,  #fafafa);
}
table tr.even td {
	background: #f6f6f6;
	background: -webkit-gradient(linear, left top, left bottom, from(#f8f8f8), to(#f6f6f6));
	background: -moz-linear-gradient(top,  #f8f8f8,  #f6f6f6);
}
table tr:last-child td {
	border-bottom:0;
}
table tr:last-child td:first-child {
	-moz-border-radius-bottomleft:3px;
	-webkit-border-bottom-left-radius:3px;
	border-bottom-left-radius:3px;
}
table tr:last-child td:last-child {
	-moz-border-radius-bottomright:3px;
	-webkit-border-bottom-right-radius:3px;
	border-bottom-right-radius:3px;
}
table tr:hover td {
	background: #f2f2f2;
	background: -webkit-gradient(linear, left top, left bottom, from(#f2f2f2), to(#f0f0f0));
	background: -moz-linear-gradient(top,  #f2f2f2,  #f0f0f0);	
}
table td ul {
    margin: 0;
    padding-left: 20px;
}
  </style>
</head>
<body>
  <h1>{{user}}'s gists</h1>
  <table cellspacing='0'>
    <colgroup>
      <col style="width: 80px">
      <col>
      <col>
      <col style="width: 100px">
    </colgroup>
    <thead>
      <tr>
        <th>ID</th>
        <th>Files</th>
        <th>Description</th>
        <th>Date</th>
      </tr>
    </thead>
    <tbody>
      {% for gist in data %}
      <tr class="{{ gist.parity }}">
        <td>
          <a href="{{ gist.url }}" target="_blank">{{ gist.id }}</a>
        </td>
        <td>
          <ul>
          {% for file in gist.files %}
            <li>
              <a href="{{ file.raw_url }}" target="_blank">{{ file.filename }}</a>
            </li>
          {% endfor %}
          </ul>
        </td>
        <td>{{ gist.description }}</td>
        <td>{{ gist.created_at }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
""")

class FetchGistError(Exception):
    pass

def fetch_gists(user):
    """Fetch user's gist index from github.com
    Refer to: http://developer.github.com/v3/gists/
    """
    url = 'https://api.github.com/users/%s/gists' % user
    res = urllib.urlopen(url)
    code = res.getcode()
    if code != 200:
        raise FetchGistError('bad http status (%s)' % code)
    jdata = res.read()
    res.close()
    return json.loads(jdata)

def simplify_gist(gist):
    """Reduce the content of a gist dict"""
    result = {}
    result['id'] = gist['id']
    result['url'] = 'https://gist.github.com/%s' % gist['id']
    result['files'] = gist['files'].values()
    result['description'] = gist['description']
    result['created_at'] = gist['created_at'][:10]
    return result

def convert_gists(gists):
    """Convert gists for html template renderring"""
    result = map(simplify_gist, gists)
    for i in range(len(result)):
        result[i]['parity'] = ((i + 1) % 2 == 0) and 'even' or 'odd'
    return result

def get_params(query_string):
    """Convert QUERY_STRING to a dict"""
    params = {}
    for arg in urllib.unquote(query_string).split('&'):
        if not arg:
            continue
        pair = arg.split('=')
        if len(pair) < 2:
            continue
        k, v = pair[0].strip(), pair[1].strip()
        if not k:
            continue
        params[k] = v
    return params

def application(environ, start_response):
    """The WSGI application"""
    headers = [('Content-Type', 'text/html; charset=utf-8')]

    if environ['PATH_INFO'] != '/':
        start_response('404 Not Found', headers)
        return ''

    params = get_params(environ['QUERY_STRING'])
    user = params.get('user')
    if not user:
        gists = []
    else:
        try:
            gists = convert_gists(fetch_gists(user))
        except FetchGistError, e:
            start_response('500 Internal Server Error', headers)
            return repr(e)

    vars = {'user': user, 'data': gists}
    body = IndexTmpl.render(vars).encode('utf-8')

    start_response('200 OK', headers)
    return [body]

def usage():
    """Show help message"""
    print """Usage: %s [Options]

Options:
    -h, --help               Print this help message
    -H, --host <HOST>        Specify listening host (default: 0.0.0.0)
    -p, --port <PORT>        Specify listening port (default: 8080)
    -v, --version            Print version information
""" % sys.argv[0]

def version():
    """Show version number"""
    print 'gistindex.py 0.0.1'

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8080

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hH:p:u:v',
            ['help', 'host=', 'port=', 'version'])
    except getopt.GetoptError, e:
        print str(e)
        exit(2)

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            exit()
        if o in ('-H', '--host'):
            host = a
        elif o in ('-p', '--port'):
            port = int(a)
        if o in ('-v', '--version'):
            version()
            exit()

    from wsgiref.simple_server import make_server
    server = make_server(host, port, application)
    print 'Listening on %s:%s...' % (host, port)
    server.serve_forever()
