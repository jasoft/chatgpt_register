/**
 * Cloudflare Worker - Catch-All 邮箱收件 + API
 *
 * 绑定要求:
 *   KV Namespace: MAIL_KV
 *   环境变量:    ADMIN_PASSWORD (管理密码)
 *               JWT_SECRET     (JWT 签名密钥, 随机字符串即可) yuyuihuqwer8972137984308947
 *               EMAIL_DOMAIN   (你的邮箱域名, 如 mail.example.com)
 *
 * Cloudflare Email Routing:
 *   设置 catch-all rule → 转发到此 Worker
 *
 * API:
 *   POST /admin/new_address  { name, domain, enablePrefix }  → 注册地址
 *   GET  /api/mails?limit=10&offset=0                        → 获取邮件 (需 Bearer JWT)
 */

// ─── 工具函数 ───

async function signJWT(payload, secret) {
    const header = { alg: "HS256", typ: "JWT" }
    const enc = (obj) => btoa(JSON.stringify(obj)).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_")
    const data = `${enc(header)}.${enc(payload)}`
    const key = await crypto.subtle.importKey(
        "raw",
        new TextEncoder().encode(secret),
        { name: "HMAC", hash: "SHA-256" },
        false,
        ["sign"],
    )
    const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data))
    const sigB64 = btoa(String.fromCharCode(...new Uint8Array(sig)))
        .replace(/=+$/, "")
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
    return `${data}.${sigB64}`
}

async function verifyJWT(token, secret) {
    try {
        const [headerB64, payloadB64, sigB64] = token.split(".")
        const data = `${headerB64}.${payloadB64}`
        const key = await crypto.subtle.importKey(
            "raw",
            new TextEncoder().encode(secret),
            { name: "HMAC", hash: "SHA-256" },
            false,
            ["verify"],
        )
        const sig = Uint8Array.from(atob(sigB64.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0))
        const valid = await crypto.subtle.verify("HMAC", key, sig, new TextEncoder().encode(data))
        if (!valid) return null
        return JSON.parse(atob(payloadB64.replace(/-/g, "+").replace(/_/g, "/")))
    } catch {
        return null
    }
}

function json(data, status = 200) {
    return new Response(JSON.stringify(data), {
        status,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    })
}

// ─── Email 事件处理 (catch-all 收件) ───

async function handleEmail(message, env) {
    const to = message.to
    const from = message.from
    const subject = message.headers.get("subject") || ""
    const rawEmail = await new Response(message.raw).text()

    // KV key: mails:<address> → JSON array
    const key = `mails:${to.toLowerCase()}`
    const existing = JSON.parse((await env.MAIL_KV.get(key)) || "[]")

    existing.unshift({
        id: crypto.randomUUID(),
        source: from,
        subject,
        raw: rawEmail,
        timestamp: Date.now(),
    })

    // 最多保留 50 封
    if (existing.length > 50) existing.length = 50

    // TTL 24 小时
    await env.MAIL_KV.put(key, JSON.stringify(existing), { expirationTtl: 86400 })
}

// ─── HTTP 路由 ───

async function handleRequest(request, env) {
    const url = new URL(request.url)

    // CORS preflight
    if (request.method === "OPTIONS") {
        return new Response(null, {
            status: 204,
            headers: {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        })
    }

    // ── POST /admin/new_address ──
    if (url.pathname === "/admin/new_address" && request.method === "POST") {
        const auth = request.headers.get("x-admin-auth") || ""
        if (auth !== env.ADMIN_PASSWORD) return json({ error: "unauthorized" }, 401)

        const body = await request.json()
        const name = body.name || crypto.randomUUID().slice(0, 12)
        const domain = body.domain || env.EMAIL_DOMAIN
        const address = `${name}@${domain}`.toLowerCase()

        // 注册地址到 KV (标记已知地址)
        await env.MAIL_KV.put(`addr:${address}`, "1", { expirationTtl: 86400 })
        // 初始化空邮箱
        await env.MAIL_KV.put(`mails:${address}`, "[]", { expirationTtl: 86400 })

        const jwt = await signJWT({ sub: address, exp: Math.floor(Date.now() / 1000) + 86400 }, env.JWT_SECRET)

        return json({ address, jwt })
    }

    // ── GET /api/mails ──
    if (url.pathname === "/api/mails" && request.method === "GET") {
        const bearer = (request.headers.get("Authorization") || "").replace("Bearer ", "")
        const payload = await verifyJWT(bearer, env.JWT_SECRET)
        if (!payload || !payload.sub) return json({ error: "unauthorized" }, 401)
        if (payload.exp && payload.exp < Date.now() / 1000) return json({ error: "token expired" }, 401)

        const limit = parseInt(url.searchParams.get("limit") || "10")
        const offset = parseInt(url.searchParams.get("offset") || "0")

        const key = `mails:${payload.sub.toLowerCase()}`
        const mails = JSON.parse((await env.MAIL_KV.get(key)) || "[]")

        return json({ results: mails.slice(offset, offset + limit) })
    }

    return json({ error: "not found" }, 404)
}

// ─── 导出 ───

export default {
    async fetch(request, env, ctx) {
        return handleRequest(request, env)
    },
    async email(message, env, ctx) {
        await handleEmail(message, env)
    },
}
