const http = require('node:http');

const orders = new Map();

http.createServer((request, response) => {
  if (request.method === 'GET' && request.url?.startsWith('/orders/')) {
    const order = orders.get(request.url.slice('/orders/'.length));
    response.writeHead(order ? 200 : 404, {'content-type': 'application/json'});
    response.end(JSON.stringify(order || {error: 'not found'}));
    return;
  }
  if (request.method === 'POST' && request.url === '/orders') {
    let body = '';
    request.on('data', chunk => { body += chunk; });
    request.on('end', () => {
      const id = String(orders.size + 1);
      const order = {id, payload: body};
      orders.set(id, order);
      response.writeHead(201, {'content-type': 'application/json'});
      response.end(JSON.stringify(order));
    });
    return;
  }
  response.writeHead(404).end();
}).listen(3000);
