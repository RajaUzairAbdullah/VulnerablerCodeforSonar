/**
 * ============================================================
 *  VULNERABLE SERVER - SCA DEMO - EDUCATIONAL USE ONLY
 *  This file USES the vulnerable packages so SCA tools
 *  confirm they are actually referenced, not just listed.
 * ============================================================
 */

const express        = require('express');
const lodash         = require('lodash');
const serialize      = require('node-serialize');
const ejs            = require('ejs');
const fileUpload     = require('express-fileupload');
const handlebars     = require('handlebars');
const axios          = require('axios');
const moment         = require('moment');
const marked         = require('marked');
const jwt            = require('jsonwebtoken');
const bcrypt         = require('bcrypt');
const mongoose       = require('mongoose');
const minimist       = require('minimist');
const NodeForge      = require('node-forge');
const multer         = require('multer');
const ws             = require('ws');
const dotProp        = require('dot-prop');
const ini            = require('ini');
const nodeFetch      = require('node-fetch');
const xmldom         = require('xmldom');
const vm2            = require('vm2');
const immer          = require('immer');
const objectPath     = require('object-path');
const validator      = require('validator');
const normalizeUrl   = require('normalize-url');
const Tar            = require('tar');

const app = express();
app.use(express.json());
app.use(fileUpload());      // CVE-2020-7699 — express-fileupload prototype pollution
app.use(express.urlencoded({ extended: true }));

// ============================================================
// 1. LODASH — CVE-2019-10744 — CRITICAL — Prototype Pollution
//    Attacker can pollute Object.prototype → affects all objects
// ============================================================
app.post('/api/merge-config', (req, res) => {
  const userConfig = req.body.config;
  const defaultConfig = {};
  // VULNERABLE: lodash.merge with attacker-controlled input
  const merged = lodash.merge(defaultConfig, userConfig);
  // Payload: {"config": {"__proto__": {"admin": true}}}
  res.json(merged);
});

// ============================================================
// 2. NODE-SERIALIZE — CVE-2017-5941 — CRITICAL — RCE
//    Deserializing untrusted data allows arbitrary code execution
// ============================================================
app.post('/api/restore-session', (req, res) => {
  const sessionData = req.body.session;
  // VULNERABLE: unserializing user input — RCE via IIFE in serialized functions
  // Payload: {"rce":"_$$ND_FUNC$$_function(){require('child_process').exec('id')}()"}
  const obj = serialize.unserialize(sessionData);
  res.json(obj);
});

// ============================================================
// 3. EJS — CVE-2022-29078 — CRITICAL — RCE via template injection
//    The 'outputFunctionName' option is not sanitized
// ============================================================
app.get('/api/render', (req, res) => {
  const template = req.query.template || '<h1>Hello</h1>';
  const name = req.query.name || 'World';
  // VULNERABLE: user controls template options
  ejs.render(template, { name }, {
    outputFunctionName: req.query.outputFunctionName // RCE here!
  });
  res.send('Rendered');
});

// ============================================================
// 4. HANDLEBARS — CVE-2021-23369 — CRITICAL — RCE via prototype
//    Prototype pollution leads to RCE in template compilation
// ============================================================
app.post('/api/template', (req, res) => {
  const templateStr = req.body.template;
  // VULNERABLE: compiling user-supplied template
  const compiledTemplate = handlebars.compile(templateStr);
  const result = compiledTemplate({ name: 'World' });
  res.send(result);
});

// ============================================================
// 5. VM2 — CVE-2023-29017 — CRITICAL — Sandbox Escape / RCE
//    Attacker can break out of VM2 sandbox
// ============================================================
app.post('/api/execute', (req, res) => {
  const { VM } = vm2;
  const userCode = req.body.code;
  // VULNERABLE: vm2 sandbox escape — attacker can escape to host
  const vmInstance = new VM({ timeout: 1000, sandbox: {} });
  const result = vmInstance.run(userCode);
  res.json({ result });
});

// ============================================================
// 6. AXIOS — CVE-2021-3749 — HIGH — SSRF + ReDoS
//    Authorization header forwarded to third-party redirects
// ============================================================
app.get('/api/proxy', async (req, res) => {
  const targetUrl = req.query.url;
  // VULNERABLE: axios follows redirects and leaks auth headers
  const response = await axios.get(targetUrl, {
    headers: { Authorization: `Bearer ${process.env.INTERNAL_TOKEN}` }
  });
  res.json(response.data);
});

// ============================================================
// 7. MOMENT — CVE-2022-24785 — HIGH — Path Traversal
//    Locale loading allows reading arbitrary files
// ============================================================
app.get('/api/locale', (req, res) => {
  const locale = req.query.locale || 'en';
  // VULNERABLE: locale value used in file path — e.g. ../../etc/passwd
  moment.locale(locale);
  res.json({ locale: moment.locale() });
});

// ============================================================
// 8. MARKED — CVE-2022-21681 / CVE-2022-21680 — MEDIUM — ReDoS
//    Specially crafted markdown causes catastrophic backtracking
// ============================================================
app.post('/api/render-markdown', (req, res) => {
  const content = req.body.content;
  // VULNERABLE: ReDoS with crafted markdown input
  const html = marked(content);
  res.send(html);
});

// ============================================================
// 9. NODE-FETCH — CVE-2022-0235 — HIGH — Exposure of Sensitive Info
//    Redirects to other origins leak Authorization headers
// ============================================================
app.get('/api/fetch', async (req, res) => {
  const url = req.query.url;
  // VULNERABLE: Authorization header leaked on redirect
  const response = await nodeFetch(url, {
    headers: { Authorization: 'Bearer internal-token-xyz' }
  });
  const data = await response.text();
  res.send(data);
});

// ============================================================
// 10. JSONWEBTOKEN — CVE-2022-23529 — HIGH — RCE via secretOrKey
//     If secretOrKey is an object, attacker can achieve RCE
// ============================================================
const JWT_SECRET = 'weak_hardcoded_secret';  // Also bad!
app.post('/api/login', (req, res) => {
  const { username, role } = req.body;
  // VULNERABLE: weak secret + no algorithm pinning
  const token = jwt.sign({ username, role }, JWT_SECRET);
  res.json({ token });
});

app.get('/api/profile', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  // VULNERABLE: algorithm not specified — 'none' algorithm attack possible
  const decoded = jwt.verify(token, JWT_SECRET);
  res.json(decoded);
});

// ============================================================
// 11. DOT-PROP — CVE-2020-8116 — MEDIUM — Prototype Pollution
//     set() allows polluting Object.prototype
// ============================================================
app.post('/api/settings', (req, res) => {
  const settings = {};
  const key = req.body.key;    // e.g. "__proto__.admin"
  const value = req.body.value;
  // VULNERABLE: prototype pollution via dot-prop.set
  dotProp.set(settings, key, value);
  res.json(settings);
});

// ============================================================
// 12. OBJECT-PATH — CVE-2021-23434 — HIGH — Prototype Pollution
// ============================================================
app.post('/api/user-prefs', (req, res) => {
  const prefs = {};
  const path = req.body.path;
  const value = req.body.value;
  // VULNERABLE: object-path prototype pollution
  objectPath.set(prefs, path, value);
  res.json(prefs);
});

// ============================================================
// 13. IMMER — CVE-2021-23436 — CRITICAL — Prototype Pollution
// ============================================================
app.post('/api/state', (req, res) => {
  const { produce } = immer;
  const baseState = { user: 'guest' };
  const patch = req.body.patch;
  // VULNERABLE: immer prototype pollution
  const nextState = produce(baseState, draft => {
    Object.assign(draft, patch);
  });
  res.json(nextState);
});

// ============================================================
// 14. INI — CVE-2020-7788 — MEDIUM — Prototype Pollution
// ============================================================
app.post('/api/parse-config', (req, res) => {
  const configStr = req.body.config;
  // VULNERABLE: ini.parse with __proto__ keys
  const parsed = ini.parse(configStr);
  res.json(parsed);
});

// ============================================================
// 15. WS — CVE-2021-32640 — MEDIUM — ReDoS
//     Crafted Sec-Websocket-Protocol header causes DoS
// ============================================================
const wss = new ws.Server({ port: 8080 });
wss.on('connection', (socket, req) => {
  // VULNERABLE: header parsing triggers ReDoS
  console.log('WS connected:', req.headers['sec-websocket-protocol']);
  socket.send('Connected');
});

// ============================================================
// 16. MULTER — CVE-2022-24434 — HIGH — Denial of Service
//     Malformed multipart data causes server crash
// ============================================================
const upload = multer({ dest: 'uploads/' });
app.post('/api/upload', upload.single('file'), (req, res) => {
  // VULNERABLE: multer DoS with crafted multipart
  res.json({ filename: req.file?.originalname });
});

// ============================================================
// 17. NORMALIZE-URL — CVE-2021-33502 — MEDIUM — ReDoS
// ============================================================
app.get('/api/normalize', (req, res) => {
  const url = req.query.url;
  // VULNERABLE: ReDoS with crafted URL
  const normalized = normalizeUrl(url);
  res.json({ normalized });
});

// ============================================================
// START SERVER
// ============================================================
app.listen(3000, () => {
  console.log('Vulnerable SCA Demo server running on :3000');
  console.log('WARNING: This server contains intentional vulnerabilities!');
});

module.exports = app;
