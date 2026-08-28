import type { NextApiRequest, NextApiResponse } from "next";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export default async function handler(_req: NextApiRequest, res: NextApiResponse) {
  try {
    const r = await fetch(`${BACKEND}/health`);
    const data = await r.json();
    res.status(r.status).json(data);
  } catch {
    res.status(503).json({ status: "unreachable" });
  }
}
