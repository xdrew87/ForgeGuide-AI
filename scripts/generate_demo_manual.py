"""
Generate a synthetic MX-400 Industrial Motor Drive manual for demo purposes.
Uses reportlab to produce a multi-page PDF with realistic maintenance content.
All content is SYNTHETIC — created for demonstration only.
"""
import sys
import os

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
    )
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
except ImportError:
    print("Installing reportlab...")
    os.system(f"{sys.executable} -m pip install reportlab --quiet")
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
    )
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT


def build_manual(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=8)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6)
    warn = ParagraphStyle("Warn", parent=styles["Normal"], fontSize=10, leading=14,
                          textColor=colors.darkred, spaceAfter=6, leftIndent=12)
    caption = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
    center = ParagraphStyle("Center", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10)

    story = []

    # ── Cover Page ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("MX-400 INDUSTRIAL MOTOR DRIVE", ParagraphStyle(
        "Cover", parent=styles["Title"], fontSize=26, textColor=colors.HexColor("#1a3a5c"), spaceAfter=8)))
    story.append(Paragraph("Operations, Maintenance & Troubleshooting Manual", ParagraphStyle(
        "Sub", parent=styles["Normal"], fontSize=14, alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph("Document No. MX400-MNT-002  |  Revision 2.4", center))
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "<b>⚠ DEMO CONTENT — SYNTHETIC DOCUMENTATION — FOR DEMONSTRATION PURPOSES ONLY ⚠</b>",
        ParagraphStyle("Demo", parent=styles["Normal"], alignment=TA_CENTER,
                       textColor=colors.HexColor("#b85c00"), fontSize=11, spaceAfter=4)
    ))
    story.append(Paragraph(
        "This document contains entirely fictional technical specifications created for the "
        "ForgeGuide AI hackathon demonstration. It does not represent any real product.",
        ParagraphStyle("DemoSub", parent=styles["Normal"], alignment=TA_CENTER,
                       textColor=colors.grey, fontSize=9)
    ))
    story.append(PageBreak())

    # ── 1. Equipment Overview ────────────────────────────────────────────────
    story.append(Paragraph("1. Equipment Overview", h1))
    story.append(Paragraph(
        "The MX-400 is a variable-frequency motor drive designed for industrial conveyor, "
        "pump, and fan applications requiring precise speed control from 0.1 Hz to 400 Hz. "
        "The unit accepts 3-phase input power at 380–480 VAC (±10%) and delivers up to "
        "400 A continuous output current.", body))
    story.append(Paragraph(
        "The drive incorporates an internal IGBT inverter stage, DSP-based control, a "
        "passive input rectifier, and a DC bus capacitor bank. A built-in heat sink with "
        "forced-air cooling fan maintains component temperatures within operating limits.", body))

    story.append(Paragraph("1.1 Nameplate Data", h2))
    data = [
        ["Parameter", "Value"],
        ["Model", "MX-400"],
        ["Input voltage", "380–480 VAC, 3-phase, 50/60 Hz"],
        ["Output voltage", "0–480 VAC, 3-phase, variable"],
        ["Rated current", "400 A continuous"],
        ["Frequency range", "0.1–400 Hz"],
        ["Ambient temperature", "0°C to +40°C operating"],
        ["Cooling method", "Forced-air (internal fan)"],
        ["Protection class", "IP20"],
        ["Weight", "42 kg"],
    ]
    t = Table(data, colWidths=[2.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2*inch))
    story.append(PageBreak())

    # ── 2. Operating Limits ──────────────────────────────────────────────────
    story.append(Paragraph("2. Operating Limits", h1))
    story.append(Paragraph(
        "Operating the MX-400 outside the limits below may result in equipment damage, "
        "unplanned shutdown, or safety hazards. Monitor operating parameters continuously "
        "using the drive's built-in diagnostics or an external SCADA system.", body))

    story.append(Paragraph("2.1 Thermal Limits", h2))
    story.append(Paragraph(
        "The MX-400 heat sink must remain below 85°C during normal operation. "
        "At ambient temperatures above 40°C, derate output current by 2% per °C. "
        "If the internal thermal sensor (mounted on the IGBT module) reads above 75°C, "
        "the drive reduces output frequency automatically to protect components.", body))
    story.append(Paragraph(
        "[SAFETY-CRITICAL] Do NOT defeat or bypass thermal protection circuits. "
        "Overheating may damage insulation, cause IGBT failure, or create fire risk.",
        warn))

    story.append(Paragraph("2.2 Load Limits", h2))
    story.append(Paragraph(
        "Maximum continuous output current is 400 A. Short-term overload of 150% rated current "
        "is permitted for up to 60 seconds per 10-minute period. Exceeding these limits will "
        "trigger fault E09 (Overcurrent) and halt the drive.", body))
    story.append(PageBreak())

    # ── 3. Maintenance Schedule ──────────────────────────────────────────────
    story.append(Paragraph("3. Preventive Maintenance Schedule", h1))
    story.append(Paragraph(
        "Perform the following inspections and maintenance tasks at the specified intervals. "
        "All maintenance must be performed by qualified personnel. Disconnect and lockout/tagout "
        "all power sources before opening the enclosure.", body))
    story.append(Paragraph(
        "[SAFETY-CRITICAL] LOCKOUT/TAGOUT REQUIRED before any internal maintenance. "
        "Capacitors may retain dangerous voltage for up to 5 minutes after power removal. "
        "Verify voltage is below 50 VDC before touching internal components.",
        warn))

    story.append(Paragraph("3.1 Maintenance Intervals", h2))
    sched_data = [
        ["Interval", "Task", "Reference"],
        ["Weekly", "Inspect cooling fan airflow; check for obstructions", "Sec 4.1"],
        ["Weekly", "Check ambient temperature at enclosure intake", "Sec 2.1"],
        ["Monthly", "Clean air intake filter with compressed air (≤0.5 bar)", "Sec 4.2"],
        ["Monthly", "Inspect cable connections for signs of overheating", "Sec 5.1"],
        ["Monthly", "Verify fault log for unreported codes", "Sec 6"],
        ["6 Months", "Inspect DC bus capacitors for bulging or leakage", "Sec 4.3"],
        ["6 Months", "Check torque on power terminal connections (20 N·m)", "Sec 5.2"],
        ["Annually", "Replace air intake filter element", "Sec 4.2"],
        ["Annually", "Full thermal imaging inspection under load", "Sec 4.4"],
        ["3 Years", "Replace DC bus capacitor bank", "Sec 4.3"],
        ["3 Years", "Replace cooling fan assembly", "Sec 4.1"],
    ]
    st = Table(sched_data, colWidths=[1.2*inch, 3.8*inch, 1*inch])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(st)
    story.append(PageBreak())

    # ── 4. Cooling System ────────────────────────────────────────────────────
    story.append(Paragraph("4. Cooling System Maintenance", h1))

    story.append(Paragraph("4.1 Cooling Fan Inspection", h2))
    story.append(Paragraph(
        "The MX-400 uses a dual-impeller forced-air cooling fan mounted at the base of the "
        "heat sink assembly. Fan failure is the leading cause of thermal faults, including E17.", body))
    story.append(Paragraph("Fan Inspection Procedure:", h3))
    steps = [
        "Observe the fan operation during normal drive run — audible grinding, rattling, or "
        "reduced airflow indicates bearing wear.",
        "With drive de-energized and LOTO applied, inspect fan blades for cracks, debris, "
        "or blade deformation.",
        "Check fan motor connector (CN-FAN1) for corrosion or loose contacts.",
        "Measure fan supply voltage at CN-FAN1: should read 24 VDC ±5% when drive is powered.",
        "If airflow is reduced but voltage is correct, replace fan assembly (Part No. MX4-FAN-02).",
        "After replacement, verify heat sink temperature drops to within 10°C of ambient within "
        "5 minutes of drive startup at no-load.",
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"{i}. {step}", body))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("4.2 Air Intake Filter Maintenance", h2))
    story.append(Paragraph(
        "The intake filter is located on the left panel of the enclosure behind the louvered vent "
        "cover. A clogged filter reduces airflow and is a common secondary cause of E17 faults.", body))
    story.append(Paragraph("Filter Cleaning Procedure:", h3))
    filter_steps = [
        "Remove the four M4 screws securing the vent cover (retain for reinstallation).",
        "Slide filter element out of the retaining channel.",
        "Blow filter clean with dry compressed air at no more than 0.5 bar, directed from the "
        "clean side outward.",
        "Inspect filter for tears or holes — replace if damaged (Part No. MX4-FLT-01).",
        "Reinstall filter and vent cover. Confirm all four screws are torqued to 1.2 N·m.",
    ]
    for i, step in enumerate(filter_steps, 1):
        story.append(Paragraph(f"{i}. {step}", body))

    story.append(Paragraph("4.3 DC Bus Capacitor Inspection", h2))
    story.append(Paragraph(
        "The DC bus capacitor bank consists of six 2200 µF / 800 VDC electrolytic capacitors "
        "mounted on the main power board. Inspect visually for:", body))
    for item in ["Bulging or domed tops", "Electrolyte leakage (brown residue)", "Discoloration from heat"]:
        story.append(Paragraph(f"• {item}", body))
    story.append(Paragraph(
        "[SAFETY-CRITICAL] Never attempt capacitor replacement while the bus is energized. "
        "Verify bus voltage below 50 VDC with a calibrated meter before touching capacitor terminals.",
        warn))
    story.append(PageBreak())

    # ── 5. Wiring & Connections ──────────────────────────────────────────────
    story.append(Paragraph("5. Wiring and Connections", h1))
    story.append(Paragraph("5.1 Power Terminal Layout", h2))
    story.append(Paragraph(
        "Input power terminals (L1, L2, L3) are located at the top-left of the power board. "
        "Output terminals (T1, T2, T3) are at the top-right. DC bus terminals (+DC, -DC) are "
        "in the center. Ground terminal (PE) is at the far left.", body))

    # ASCII wiring diagram representation
    wiring_text = """
    INPUT TERMINALS          DC BUS              OUTPUT TERMINALS
    ┌──────────────┐       ┌────────┐           ┌──────────────┐
    │ L1  L2  L3   │──────▶│ +DC   │──────────▶│ T1  T2  T3   │
    │ (3Ø AC In)   │       │ -DC   │           │ (3Ø AC Out)  │
    └──────────────┘       └────────┘           └──────────────┘
         │                                            │
        PE (Ground)                               Load Motor
    """
    story.append(Paragraph(f"<font name='Courier' size='8'>{wiring_text}</font>", body))
    story.append(Paragraph("Figure 5-1: Simplified power terminal layout (SYNTHETIC DIAGRAM)", caption))

    story.append(Paragraph("5.2 Connection Torque Specifications", h2))
    torque_data = [
        ["Terminal", "Wire Size", "Torque (N·m)"],
        ["L1, L2, L3 (Input)", "70–120 mm²", "20 N·m"],
        ["T1, T2, T3 (Output)", "70–120 mm²", "20 N·m"],
        ["+DC, -DC (Bus)", "50–95 mm²", "16 N·m"],
        ["PE (Ground)", "70 mm² min.", "20 N·m"],
        ["Control terminals (CN-CTL)", "0.5–2.5 mm²", "0.5 N·m"],
    ]
    tt = Table(torque_data, colWidths=[2.2*inch, 1.8*inch, 1.5*inch])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tt)
    story.append(PageBreak())

    # ── 6. Fault Codes ──────────────────────────────────────────────────────
    story.append(Paragraph("6. Fault Codes and Troubleshooting", h1))
    story.append(Paragraph(
        "When the MX-400 detects a fault condition, it halts the drive, displays the fault "
        "code on the operator panel, and logs the event with a timestamp. The fault LED "
        "(red) illuminates. The drive will not restart until the fault is acknowledged "
        "and the root cause is resolved.", body))
    story.append(Paragraph(
        "To acknowledge a fault: press the RESET button on the operator panel after resolving "
        "the underlying condition. Repeated faults without resolution indicate an unresolved "
        "mechanical, electrical, or environmental issue.", body))

    story.append(Paragraph("6.1 Fault Code Reference Table", h2))
    fault_data = [
        ["Code", "Name", "Possible Causes", "Immediate Action"],
        ["E01", "Input Undervoltage", "Supply voltage below 342 VAC", "Check input supply; inspect fuses L1–L3"],
        ["E02", "Input Overvoltage", "Supply voltage above 528 VAC", "Inspect supply; check for capacitor bank issues"],
        ["E03", "Output Phase Loss", "Open output phase T1/T2/T3", "Inspect output wiring; check motor terminals"],
        ["E05", "Ground Fault", "Output insulation failure", "Megger test motor cable; isolate fault"],
        ["E07", "DC Bus Overvoltage", "Regen energy / braking", "Add braking resistor; check decel ramp"],
        ["E09", "Overcurrent", "Motor load exceeded 150% × 60s", "Check load; verify motor sizing"],
        ["E11", "Motor Stall", "Locked rotor or high breakaway torque", "Check mechanical coupling; reduce starting load"],
        ["E14", "Control Board Fault", "Internal DSP error", "Cycle power; if persists, replace control board"],
        ["E17", "Thermal Overtemperature", "Heat sink >85°C", "See Section 6.3 — Thermal Fault Procedure"],
        ["E19", "Fan Fault", "Cooling fan failure detected", "Inspect fan; replace MX4-FAN-02 if failed"],
        ["E22", "Parameter CRC Error", "Non-volatile memory corruption", "Restore factory defaults; reprogram parameters"],
        ["E31", "Communication Fault", "Fieldbus/SCADA link lost", "Check fieldbus wiring; verify master address"],
    ]
    ft = Table(fault_data, colWidths=[0.6*inch, 1.5*inch, 2.2*inch, 2.2*inch])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        # Highlight E17 row
        ("BACKGROUND", (0, 9), (-1, 9), colors.HexColor("#fff3cd")),
        ("FONTNAME", (0, 9), (-1, 9), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ft)
    story.append(PageBreak())

    # ── 6.3 E17 Thermal Fault — detailed ────────────────────────────────────
    story.append(Paragraph("6.3 E17 — Thermal Overtemperature Fault", h1))
    story.append(Paragraph(
        "Fault E17 indicates the internal heat sink temperature sensor has exceeded 85°C. "
        "The drive halts immediately to protect the IGBT modules from thermal damage. "
        "This fault is most commonly observed after sustained high-load operation, particularly "
        "in warm ambient conditions or after extended duty cycles.", body))
    story.append(Paragraph(
        "[SAFETY-CRITICAL] Allow the drive to cool for at least 10 minutes before opening "
        "the enclosure. Internal components may exceed 100°C immediately after shutdown.",
        warn))

    story.append(Paragraph("E17 Root Cause Categories", h2))
    causes = [
        ("Cooling fan failure", "Fan motor bearing failure or blade blockage reduces airflow. "
         "Most common single cause. Refer to Section 4.1."),
        ("Clogged air intake filter", "Accumulated dust blocks intake and restricts airflow. "
         "Refer to Section 4.2 for cleaning procedure."),
        ("Elevated ambient temperature", "Drive enclosure ambient exceeding 40°C. "
         "Install supplemental ventilation or air conditioning."),
        ("Prolonged overload operation", "Sustained current draw above rated capacity elevates "
         "IGBT junction temperature. Verify load sizing."),
        ("Blocked heat sink fins", "Debris accumulation in heat sink fin channels. "
         "Inspect and clean with compressed air."),
    ]
    for cause, desc in causes:
        story.append(Paragraph(f"<b>{cause}:</b> {desc}", body))

    story.append(Paragraph("E17 Step-by-Step Diagnostic Procedure", h2))
    diag_steps = [
        "Record the drive's fault log: navigate to MENU → DIAGNOSTICS → FAULT LOG and note "
        "the heat sink temperature (parameter D-HS-TEMP) at time of fault.",
        "Allow a minimum 10-minute cool-down with enclosure closed. Do not open enclosure prematurely.",
        "Apply LOCKOUT/TAGOUT to all power sources. Verify bus voltage below 50 VDC.",
        "Inspect the cooling fan (Section 4.1): check for rotation, unusual noise, and correct "
        "24 VDC supply at connector CN-FAN1.",
        "Inspect the air intake filter (Section 4.2): if visibly grey/brown or restricted, "
        "clean or replace immediately.",
        "Inspect heat sink fin channels for accumulated debris. Clear with dry compressed air "
        "(≤0.5 bar) directed along fin channels.",
        "Verify ambient temperature at the drive enclosure air intake. Must not exceed 40°C "
        "for rated operation.",
        "If all cooling components are functional and ambient is acceptable, review the load profile: "
        "check parameter D-AV-CURR (average output current over last 10 minutes).",
        "Restore power, reset fault, and monitor D-HS-TEMP for the first 20 minutes of operation.",
        "If E17 recurs within 20 minutes under normal load, escalate to service — possible IGBT "
        "degradation or thermal sensor failure.",
    ]
    for i, step in enumerate(diag_steps, 1):
        story.append(Paragraph(f"{i}. {step}", body))

    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("E17 Verification After Resolution", h2))
    story.append(Paragraph(
        "After completing the diagnostic and corrective steps, confirm resolution by monitoring "
        "parameter D-HS-TEMP for a minimum of 20 minutes under representative load. "
        "Heat sink temperature should stabilize below 70°C for normal operation at ≤40°C ambient. "
        "If temperature remains above 75°C, the drive requires further inspection or derating.", body))
    story.append(PageBreak())

    # ── 7. Parameter Reference ───────────────────────────────────────────────
    story.append(Paragraph("7. Key Diagnostic Parameters", h1))
    story.append(Paragraph(
        "Access diagnostic parameters via the operator panel: MENU → DIAGNOSTICS → MONITOR.",
        body))
    param_data = [
        ["Parameter ID", "Description", "Normal Range"],
        ["D-HS-TEMP", "Heat sink temperature (°C)", "< 75°C at rated load"],
        ["D-AV-CURR", "Average output current (A)", "≤ 400 A continuous"],
        ["D-DC-BUS", "DC bus voltage (VDC)", "560–680 VDC (at 480 VAC input)"],
        ["D-FAN-SPD", "Cooling fan speed (%)", "> 85% at full load"],
        ["D-OUT-FREQ", "Output frequency (Hz)", "Application dependent"],
        ["D-FLT-CNT", "Fault count since last reset", "0 after corrective action"],
        ["D-RUN-HRS", "Total run hours", "Maintenance reference"],
    ]
    pt = Table(param_data, colWidths=[1.4*inch, 3.2*inch, 1.9*inch])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(pt)
    story.append(PageBreak())

    # ── 8. Parts List ────────────────────────────────────────────────────────
    story.append(Paragraph("8. Replacement Parts", h1))
    parts_data = [
        ["Part Number", "Description", "Replacement Interval"],
        ["MX4-FAN-02", "Cooling fan assembly, dual-impeller 24 VDC", "3 years or on E19/E17"],
        ["MX4-FLT-01", "Air intake filter element", "Annual or when clogged"],
        ["MX4-CAP-SET", "DC bus capacitor bank (6 × 2200 µF / 800 VDC)", "3 years"],
        ["MX4-CTRL-BD", "DSP control board assembly", "On E14 (persistent)"],
        ["MX4-TERM-KIT", "Power terminal screw kit (M10, stainless)", "As needed"],
    ]
    rt = Table(parts_data, colWidths=[1.4*inch, 3.3*inch, 1.8*inch])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(rt)
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "END OF DOCUMENT — MX400-MNT-002 Rev 2.4 — SYNTHETIC DEMO CONTENT ONLY",
        ParagraphStyle("Footer", parent=styles["Normal"], alignment=TA_CENTER,
                       textColor=colors.grey, fontSize=8)
    ))

    doc.build(story)
    print(f"✓ Demo manual written: {output_path}")


if __name__ == "__main__":
    import pathlib
    out = pathlib.Path(__file__).parent.parent / "demo-data" / "MX400-Maintenance-Manual-DEMO.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    build_manual(str(out))
