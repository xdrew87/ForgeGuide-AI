import type { NextApiRequest, NextApiResponse } from "next";

// Server-side: reads BACKEND_URL at request time, not build time.
// This means docker-compose can inject BACKEND_URL=http://backend:8000
// and the frontend container will use it correctly.

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";
const BACKEND_ORIGIN = new URL(BACKEND);

// Only allow simple path segments — no "..", no slashes, no scheme/host
// injection — so the request can never be redirected off BACKEND_ORIGIN.
const SAFE_SEGMENT = /^[A-Za-z0-9_.-]+$/;

export const config = { api: { bodyParser: false } };

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const slug = (req.query.slug as string[]) || [];
  if (slug.some((seg) => seg === ".." || seg === "." || !SAFE_SEGMENT.test(seg))) {
    res.status(400).json({ error: "Invalid path" });
    return;
  }

  const url = new URL(`/api/v1/${slug.map(encodeURIComponent).join("/")}`, BACKEND_ORIGIN);
  const qs = req.url?.split("?")[1];
  if (qs) url.search = qs;

  const headers: Record<string, string> = {};
  for (const [k, v] of Object.entries(req.headers)) {
    if (typeof v === "string" && k !== "host") headers[k] = v;
  }

  // Stream body for file uploads
  const chunks: Buffer[] = [];
  await new Promise<void>((resolve) => {
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", resolve);
  });
  const body = chunks.length ? Buffer.concat(chunks) : undefined;

  const upstream = await fetch(url, {
    method: req.method,
    headers,
    body: body && body.length > 0 ? body : undefined,
  });

  res.status(upstream.status);
  upstream.headers.forEach((v, k) => {
    if (!["transfer-encoding", "connection"].includes(k)) res.setHeader(k, v);
  });

  const data = await upstream.arrayBuffer();
  res.end(Buffer.from(data));
}
