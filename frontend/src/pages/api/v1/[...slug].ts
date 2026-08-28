import type { NextApiRequest, NextApiResponse } from "next";

// Server-side: reads BACKEND_URL at request time, not build time.
// This means docker-compose can inject BACKEND_URL=http://backend:8000
// and the frontend container will use it correctly.

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export const config = { api: { bodyParser: false } };

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const slug = (req.query.slug as string[]) || [];
  const path = slug.join("/");
  const qs = req.url?.split("?")[1] ? `?${req.url.split("?")[1]}` : "";
  const url = `${BACKEND}/api/v1/${path}${qs}`;

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
