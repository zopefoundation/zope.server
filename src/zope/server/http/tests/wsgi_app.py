# a WSGI app for testing

def test_app(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return ['Hello world!\n']

def test_app_factory(global_config, **local_config):
    return test_app

