const { createServer } = require('http');
const next = require('next');

const port = parseInt(process.env.PORT || '3000', 10);
const dev = false;
const app = next({ dev, dir: __dirname });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = createServer((req, res) => {
    handle(req, res);
  });

  server.listen(port, '0.0.0.0', (err) => {
    if (err) throw err;
    console.log(`> Learnova Production Server Ready on http://localhost:${port}`);
  });
});
