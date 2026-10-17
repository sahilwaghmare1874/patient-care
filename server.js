const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 3000;
const FRONTEND_DIR = path.join(__dirname, 'frontend');

const MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.xml': 'application/xml; charset=utf-8',
    '.txt': 'text/plain; charset=utf-8',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf'
};

const server = http.createServer((req, res) => {
    const parsedUrl = url.parse(req.url);
    let pathname = decodeURIComponent(parsedUrl.pathname);

    // Reverse proxy API and Admin requests to Django backend on port 8000
    if (pathname.startsWith('/api') || pathname.startsWith('/admin') || pathname.startsWith('/media')) {
        const proxyReq = http.request({
            hostname: '127.0.0.1',
            port: 8000,
            path: req.url,
            method: req.method,
            headers: {
                ...req.headers,
                host: '127.0.0.1:8000'
            }
        }, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res);
        });

        proxyReq.on('error', (err) => {
            res.writeHead(502, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Backend server unavailable. Please ensure Django is running on port 8000.' }));
        });

        req.pipe(proxyReq);
        return;
    }

    // Support /frontend/... paths as well as root /
    if (pathname.startsWith('/frontend/')) {
        pathname = pathname.replace('/frontend', '');
    }

    if (pathname === '/' || pathname === '') {
        pathname = '/index.html';
    }

    const filePath = path.join(FRONTEND_DIR, pathname);

    // Prevent directory traversal attacks
    if (!filePath.startsWith(FRONTEND_DIR)) {
        res.writeHead(403, { 'Content-Type': 'text/plain' });
        res.end('403 Forbidden');
        return;
    }

    fs.stat(filePath, (err, stats) => {
        if (err || !stats.isFile()) {
            res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
            res.end(`<h1>404 Not Found</h1><p>The requested file <code>${pathname}</code> was not found in <code>frontend</code>.</p><p><a href="/">Back to Home</a></p>`);
            return;
        }

        const ext = path.extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';

        res.writeHead(200, {
            'Content-Type': contentType,
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache'
        });

        const stream = fs.createReadStream(filePath);
        stream.pipe(res);
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`\n======================================================`);
    console.log(` Healthcare Insurance Assurance Frontend is LIVE!`);
    console.log(` Local URL: http://localhost:${PORT}/`);
    console.log(` Network URL: http://127.0.0.1:${PORT}/`);
    console.log(` Connected to Backend: http://127.0.0.1:8000/api/`);
    console.log(`======================================================\n`);
});
