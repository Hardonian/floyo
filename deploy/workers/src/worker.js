/**
 * Cloudflare Worker for Floyo API.
 * Dependency-free router: deploys without npm package resolution.
 */

const SERVICE = 'floyo-api';
const VERSION = '0.1.0';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  });
}

function error(message, status = 400) {
  return json({ error: message }, status);
}

async function parseJSON(request) {
  try { return await request.json(); } catch { return {}; }
}

async function createRecord(request, env) {
  const body = await parseJSON(request);
  const name = body.workspace_name || body.name || SERVICE;
  const source = body.repo_url || body.source || null;
  const result = await env.DB.prepare(
    `CREATE TABLE IF NOT EXISTS records (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      source TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )`
  ).run();
  await env.DB.prepare(
    `INSERT INTO records (name, source, status, created_at)
     VALUES (?, ?, 'pending', datetime('now'))`
  ).bind(name, source).run();
  const latest = await env.DB.prepare('SELECT * FROM records ORDER BY id DESC LIMIT 1').first();
  return json({ service: SERVICE, record: latest }, 201);
}

async function listRecords(env) {
  await env.DB.prepare(
    `CREATE TABLE IF NOT EXISTS records (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      source TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )`
  ).run();
  const result = await env.DB.prepare('SELECT * FROM records ORDER BY created_at DESC LIMIT 50').all();
  return json({ service: SERVICE, records: result.results || [] });
}

async function route(request, env) {
  const url = new URL(request.url);
  if (request.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (url.pathname === '/' || url.pathname === '/health') {
    return json({ status: 'ok', service: SERVICE, version: VERSION, timestamp: new Date().toISOString() });
  }
  if (url.pathname === '/api/v1' || url.pathname === '/api/v1/health') {
    return json({ status: 'ok', service: SERVICE, version: VERSION });
  }
  if (url.pathname === '/api/v1/records' && request.method === 'GET') return listRecords(env);
  if (url.pathname === '/api/v1/records' && request.method === 'POST') return createRecord(request, env);
  if (url.pathname === '/api/v1/audits' && request.method === 'GET') return listRecords(env);
  if (url.pathname === '/api/v1/audits' && request.method === 'POST') return createRecord(request, env);
  return error('Not found', 404);
}

export default {
  async fetch(request, env, ctx) { return route(request, env); },
  async scheduled(event, env, ctx) { ctx.waitUntil(Promise.resolve()); },
};
