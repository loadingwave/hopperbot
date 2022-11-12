from aiohttp import web
from pprint import pprint


async def handle(request: web.Request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


async def print_post(request: web.Request):
    pprint(request.post())
    return web.Response(status=204)

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{name}', handle),
                web.post('/', print_post)])

if __name__ == '__main__':
    web.run_app(app)
