# ForgeGuide AI — Demo Guide

## Setup

```bash
docker-compose up --build
python scripts/generate_demo_manual.py
```

Upload the demo manual via the UI (sidebar → Documents tab → drop PDF) or:

```bash
curl -X POST http://localhost:8000/api/v1/equipment/ \
  -H "Content-Type: application/json" \
  -d '{"manufacturer":"Demo Corp","model":"MX-400","equipment_type":"Motor Drive"}'

# Get the equipment ID from the response, then:
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@demo-data/MX400-Maintenance-Manual-DEMO.pdf" \
  -F "title=MX-400 Maintenance Manual" \
  -F "equipment_id=<id from above>"
```

Wait ~10-15 seconds for ingestion (check status endpoint or sidebar status dot).

---

## Demo Scenario 1 — Thermal Fault (Primary Demo)

**Query:**
> "The MX-400 keeps showing E17 after running under load for 20 minutes. What should I check?"

**Expected:**
- Evidence indicator: green / sufficient
- Answer: identifies E17 as Thermal Overtemperature, lists diagnostic steps from Section 6.3
- Citations: document title, page numbers, sections (cooling fan inspection, filter cleaning)
- Confidence bar: ~70%+

---

## Demo Scenario 2 — Fault Code Lookup

**Query:** `What does fault E09 indicate?`
**Expected:** Overcurrent fault, 150% overload, check load/motor sizing — from fault table

**Query:** `What maintenance tasks are required every 6 months?`
**Expected:** Capacitor inspection, torque check on terminals — from Section 3.1 table

---

## Demo Scenario 3 — No Evidence (Critical Demo Point)

**Query:** `How do I reprogram the PLC controller on the MX-400?`
**Expected:**
- Evidence indicator: red / insufficient
- Response begins with INSUFFICIENT_EVIDENCE
- NO invented procedure — system explicitly declines
- This is the core safety feature of the product

---

## Demo Scenario 4 — Multimodal Image Upload

Upload a photo of an equipment control panel showing `E17` on the display.

**Expected:**
- System extracts `E17` from image
- Auto-generates query: "Fault code E17 troubleshooting procedure"
- Runs full retrieval and returns grounded answer with citations
- Detected fault codes shown as orange badges

---

## Key Talking Points

1. **Evidence gate first** — retrieval confidence must exceed threshold before LLM is called
2. **Every claim is citable** — citation chips expand to show exact supporting text
3. **Safety rules are prompt-level enforced** — never disables LOTO or bypasses protections
4. **Provider-agnostic** — works with Anthropic or OpenAI; swap via env var
5. **On-prem ready** — Docker Compose, no cloud dependencies in architecture
6. **23 tests** including a named regression test: no fabrication when evidence is absent
