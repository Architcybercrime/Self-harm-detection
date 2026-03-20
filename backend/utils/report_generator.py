"""
report_generator.py
Professional psychological risk assessment report generator.
Generates clinical-style PDF reports for self-harm risk analysis.
"""

import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


# ── COLORS ───────────────────────────────────────────
DARK_BLUE   = HexColor('#1a237e')
BLUE        = HexColor('#1565c0')
LIGHT_BLUE  = HexColor('#e3f2fd')
GREEN       = HexColor('#2e7d32')
LIGHT_GREEN = HexColor('#e8f5e9')
RED         = HexColor('#b71c1c')
LIGHT_RED   = HexColor('#ffebee')
ORANGE      = HexColor('#e65100')
LIGHT_ORANGE= HexColor('#fff3e0')
GREY        = HexColor('#424242')
LIGHT_GREY  = HexColor('#f5f5f5')
PURPLE      = HexColor('#4a148c')
LIGHT_PURPLE= HexColor('#f3e5f5')


def get_risk_color(risk_level):
    if risk_level in ['HIGH', 'CRITICAL']:
        return RED, LIGHT_RED
    elif risk_level == 'MEDIUM':
        return ORANGE, LIGHT_ORANGE
    else:
        return GREEN, LIGHT_GREEN


def get_tendencies(prediction_data):
    """Analyze prediction data and return behavioral tendencies."""
    tendencies = []
    sentiment  = prediction_data.get('sentiment_score', 0)
    confidence = prediction_data.get('confidence', 0)
    risk_level = prediction_data.get('risk_level', 'LOW')
    indicators = prediction_data.get('risk_indicators', {})

    if sentiment < -0.6:
        tendencies.append({
            "tendency": "Severe Negative Affect",
            "description": "The language patterns indicate deeply negative emotional states, "
                           "including possible feelings of hopelessness, worthlessness, or despair.",
            "severity": "HIGH"
        })
    elif sentiment < -0.3:
        tendencies.append({
            "tendency": "Moderate Negative Affect",
            "description": "Noticeable negative emotional tone detected in the communication. "
                           "This may indicate persistent low mood or emotional distress.",
            "severity": "MEDIUM"
        })

    if confidence > 0.85 and risk_level == 'HIGH':
        tendencies.append({
            "tendency": "High-Risk Ideation Patterns",
            "description": "Language patterns strongly correlate with self-harm ideation "
                           "as identified in clinical research datasets. Immediate professional "
                           "evaluation is recommended.",
            "severity": "HIGH"
        })

    if indicators.get('text_sentiment') == 'negative':
        tendencies.append({
            "tendency": "Negative Cognitive Patterns",
            "description": "Communication reflects negative cognitive schemas which may include "
                           "catastrophizing, all-or-nothing thinking, or self-blame patterns "
                           "commonly associated with depression and anxiety.",
            "severity": "MEDIUM"
        })

    if indicators.get('severity') == 'critical':
        tendencies.append({
            "tendency": "Crisis-Level Distress Indicators",
            "description": "The analysis detected language consistent with acute psychological "
                           "crisis. This pattern is associated with immediate risk and requires "
                           "urgent professional intervention.",
            "severity": "CRITICAL"
        })

    if not tendencies:
        tendencies.append({
            "tendency": "No Significant Risk Tendencies",
            "description": "Current communication patterns do not indicate significant "
                           "self-harm risk tendencies. Continue regular wellness monitoring.",
            "severity": "LOW"
        })

    return tendencies


def get_possible_issues(prediction_data):
    """Identify possible underlying psychological issues."""
    issues = []
    sentiment  = prediction_data.get('sentiment_score', 0)
    risk_level = prediction_data.get('risk_level', 'LOW')
    confidence = prediction_data.get('confidence', 0)

    if sentiment < -0.5 and risk_level == 'HIGH':
        issues.append({
            "issue":       "Major Depressive Episode",
            "likelihood":  "High",
            "description": "Persistent negative affect combined with high-risk language "
                           "patterns suggests possible major depressive episode requiring "
                           "clinical evaluation."
        })

    if risk_level in ['HIGH', 'CRITICAL']:
        issues.append({
            "issue":       "Self-Harm Ideation",
            "likelihood":  "High" if confidence > 0.85 else "Moderate",
            "description": "Detected language patterns are strongly correlated with "
                           "self-harm ideation based on clinical research. Professional "
                           "assessment is essential."
        })

    if sentiment < -0.3:
        issues.append({
            "issue":       "Anxiety or Mood Disorder",
            "likelihood":  "Moderate",
            "description": "Negative emotional patterns may indicate underlying anxiety "
                           "or mood disorder. A comprehensive psychological evaluation "
                           "would help determine appropriate support."
        })

    if sentiment < -0.6:
        issues.append({
            "issue":       "Social Isolation or Withdrawal",
            "likelihood":  "Moderate",
            "description": "Extreme negative affect is often accompanied by social "
                           "withdrawal. Building or maintaining social support networks "
                           "is recommended."
        })

    if not issues:
        issues.append({
            "issue":       "No Significant Issues Detected",
            "likelihood":  "Low",
            "description": "Current analysis does not indicate significant underlying "
                           "psychological issues. Maintain regular wellness practices."
        })

    return issues


def get_professional_advice(prediction_data):
    """Generate professional therapist-style advice."""
    risk_level = prediction_data.get('risk_level', 'LOW')
    sentiment  = prediction_data.get('sentiment_score', 0)
    confidence = prediction_data.get('confidence', 0)

    if risk_level in ['HIGH', 'CRITICAL']:
        return [
            {
                "area":   "Immediate Safety Planning",
                "advice": "It is strongly recommended to create an immediate safety plan "
                          "with a qualified mental health professional. This should include "
                          "identifying triggers, warning signs, coping strategies, and "
                          "emergency contacts. Do not delay seeking professional help."
            },
            {
                "area":   "Professional Psychiatric Evaluation",
                "advice": "A comprehensive psychiatric evaluation is essential to assess "
                          "the current mental state, identify any underlying conditions, "
                          "and determine the most appropriate course of treatment. This "
                          "evaluation should be conducted as soon as possible."
            },
            {
                "area":   "Crisis Support Resources",
                "advice": "Please reach out to crisis support services immediately. "
                          "iCall (9152987821), Vandrevala Foundation (1860-2662-345), "
                          "and AASRA (9820466627) provide immediate, confidential support. "
                          "You are not alone in this journey."
            },
            {
                "area":   "Support Network Activation",
                "advice": "Identify and connect with trusted individuals in your support "
                          "network — family members, close friends, or mentors. Sharing "
                          "your feelings with someone you trust can provide immediate "
                          "relief and reduce feelings of isolation."
            },
            {
                "area":   "Therapeutic Intervention",
                "advice": "Cognitive Behavioral Therapy (CBT) and Dialectical Behavior "
                          "Therapy (DBT) have shown significant effectiveness for individuals "
                          "experiencing self-harm ideation. Consider seeking a therapist "
                          "specializing in these modalities."
            }
        ]

    elif risk_level == 'MEDIUM' or sentiment < -0.3:
        return [
            {
                "area":   "Professional Consultation",
                "advice": "While not an immediate crisis, scheduling a consultation with "
                          "a mental health professional would be beneficial. Early intervention "
                          "is always more effective than waiting for symptoms to escalate."
            },
            {
                "area":   "Mindfulness and Stress Management",
                "advice": "Regular mindfulness practice, including meditation and deep "
                          "breathing exercises, can significantly reduce negative thought "
                          "patterns. Apps like Headspace or Calm can be helpful starting points."
            },
            {
                "area":   "Lifestyle Modifications",
                "advice": "Regular physical exercise (at least 30 minutes daily), adequate "
                          "sleep (7-9 hours), and a balanced diet have been clinically proven "
                          "to improve mood and reduce anxiety. Small consistent changes "
                          "yield significant long-term benefits."
            },
            {
                "area":   "Social Connection",
                "advice": "Actively maintain social connections and engage in meaningful "
                          "activities. Volunteering, joining interest groups, or reconnecting "
                          "with old friends can provide purpose and reduce feelings of isolation."
            }
        ]

    else:
        return [
            {
                "area":   "Wellness Maintenance",
                "advice": "Continue current positive mental health practices. Regular "
                          "self-check-ins, journaling, and maintaining social connections "
                          "are excellent preventive measures."
            },
            {
                "area":   "Preventive Mental Health Care",
                "advice": "Consider periodic mental health check-ups even when feeling "
                          "well. Proactive mental healthcare is as important as physical "
                          "health maintenance."
            },
            {
                "area":   "Building Resilience",
                "advice": "Focus on building emotional resilience through activities that "
                          "bring joy and meaning. Developing healthy coping strategies now "
                          "provides a strong foundation for handling future challenges."
            }
        ]


def generate_report(prediction_data, username="Anonymous", report_id=None):
    """
    Generate a professional psychological risk assessment PDF report.

    Args:
        prediction_data: dict with prediction results from API
        username: name of the user
        report_id: unique report identifier

    Returns:
        path to generated PDF file
    """
    if not report_id:
        report_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Create reports directory
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    filename  = f"risk_assessment_{report_id}.pdf"
    filepath  = os.path.join(reports_dir, filename)
    risk_level = prediction_data.get('risk_level', 'LOW')
    confidence = prediction_data.get('confidence', 0)
    sentiment  = prediction_data.get('sentiment_score', 0)
    timestamp  = prediction_data.get('analysis_timestamp',
                                     datetime.datetime.now().isoformat())
    risk_color, risk_bg = get_risk_color(risk_level)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Normal'],
        fontSize=18, textColor=white, alignment=TA_CENTER,
        fontName='Helvetica-Bold', spaceAfter=4)

    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=10, textColor=HexColor('#90caf9'), alignment=TA_CENTER,
        spaceAfter=2)

    h2_style = ParagraphStyle('H2', parent=styles['Normal'],
        fontSize=13, textColor=DARK_BLUE, fontName='Helvetica-Bold',
        spaceAfter=6, spaceBefore=12)

    h3_style = ParagraphStyle('H3', parent=styles['Normal'],
        fontSize=11, textColor=BLUE, fontName='Helvetica-Bold',
        spaceAfter=4, spaceBefore=8)

    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=9.5, textColor=GREY, spaceAfter=4,
        leading=15, alignment=TA_JUSTIFY)

    disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'],
        fontSize=8, textColor=HexColor('#757575'), alignment=TA_CENTER,
        spaceAfter=4, leading=12)

    story = []

    # ── HEADER ───────────────────────────────────────
    header_data = [[
        Paragraph('PSYCHOLOGICAL RISK ASSESSMENT REPORT', title_style),
    ]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK_BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('ROUNDEDCORNERS', [5,5,5,5]),
    ]))
    story.append(header_table)

    sub_data = [[
        Paragraph('Self-Harm Detection & Mental Health Analysis System', subtitle_style),
    ]]
    sub_table = Table(sub_data, colWidths=[170*mm])
    sub_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 6*mm))

    # ── REPORT META ──────────────────────────────────
    meta_data = [
        ['Report ID',        f'RPT-{report_id}',
         'Generated',         datetime.datetime.now().strftime('%d %B %Y, %H:%M')],
        ['Patient/User',     username,
         'Analysis Time',     timestamp[:19].replace('T', ' ')],
        ['Model Accuracy',   '92.2%',
         'Analysis Type',     prediction_data.get('modality', 'Text Analysis').title()],
    ]
    meta_table = Table(meta_data, colWidths=[35*mm, 55*mm, 35*mm, 45*mm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME',    (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME',    (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',    (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 9),
        ('TEXTCOLOR',   (0,0), (0,-1), DARK_BLUE),
        ('TEXTCOLOR',   (2,0), (2,-1), DARK_BLUE),
        ('GRID',        (0,0), (-1,-1), 0.5, HexColor('#e0e0e0')),
        ('BACKGROUND',  (0,0), (-1,-1), LIGHT_GREY),
        ('TOPPADDING',  (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6*mm))

    # ── RISK SUMMARY ─────────────────────────────────
    story.append(Paragraph('1. RISK ASSESSMENT SUMMARY', h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 3*mm))

    risk_data = [
        ['OVERALL RISK LEVEL', 'CONFIDENCE SCORE', 'SENTIMENT SCORE', 'ALERT STATUS'],
        [
            risk_level,
            f'{confidence:.1%}',
            f'{sentiment:.4f}',
            '🚨 ALERT TRIGGERED' if prediction_data.get('alert_triggered') else '✅ NO ALERT'
        ]
    ]
    risk_table = Table(risk_data, colWidths=[42*mm, 42*mm, 42*mm, 44*mm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0), DARK_BLUE),
        ('TEXTCOLOR',    (0,0), (-1,0), white),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 10),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND',   (0,1), (0,1), risk_bg),
        ('TEXTCOLOR',    (0,1), (0,1), risk_color),
        ('FONTNAME',     (0,1), (0,1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,1), (0,1), 14),
        ('BACKGROUND',   (1,1), (-1,1), LIGHT_BLUE),
        ('GRID',         (0,0), (-1,-1), 0.5, HexColor('#bdbdbd')),
        ('TOPPADDING',   (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 4*mm))

    # Risk indicators
    if 'risk_indicators' in prediction_data:
        ri = prediction_data['risk_indicators']
        ind_data = [
            ['Indicator', 'Value', 'Indicator', 'Value'],
            ['Text Sentiment',   ri.get('text_sentiment', 'N/A').title(),
             'Confidence Level', ri.get('confidence_level', 'N/A').title()],
            ['Severity Level',   ri.get('severity', 'N/A').title(),
             'Alert Status',     'Active' if prediction_data.get('alert_triggered') else 'Inactive'],
        ]
        ind_table = Table(ind_data, colWidths=[42*mm, 42*mm, 42*mm, 44*mm])
        ind_table.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,0), BLUE),
            ('TEXTCOLOR',    (0,0), (-1,0), white),
            ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME',     (0,2), (0,2), 'Helvetica-Bold'),
            ('FONTNAME',     (2,1), (2,-1), 'Helvetica-Bold'),
            ('FONTSIZE',     (0,0), (-1,-1), 9),
            ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
            ('GRID',         (0,0), (-1,-1), 0.5, HexColor('#bdbdbd')),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [white, LIGHT_BLUE]),
            ('TOPPADDING',   (0,0), (-1,-1), 6),
            ('BOTTOMPADDING',(0,0), (-1,-1), 6),
        ]))
        story.append(ind_table)

    story.append(Spacer(1, 6*mm))

    # ── BEHAVIORAL TENDENCIES ────────────────────────
    story.append(Paragraph('2. BEHAVIORAL TENDENCIES IDENTIFIED', h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'The following behavioral tendencies have been identified through AI-powered '
        'analysis of language patterns, sentiment indicators, and risk markers:',
        body_style
    ))
    story.append(Spacer(1, 3*mm))

    tendencies = get_tendencies(prediction_data)
    for i, t in enumerate(tendencies, 1):
        sev_color = RED if t['severity'] in ['HIGH','CRITICAL'] else \
                    ORANGE if t['severity'] == 'MEDIUM' else GREEN
        sev_bg    = LIGHT_RED if t['severity'] in ['HIGH','CRITICAL'] else \
                    LIGHT_ORANGE if t['severity'] == 'MEDIUM' else LIGHT_GREEN

        tend_data = [[
            Paragraph(f'{i}. {t["tendency"]}',
                      ParagraphStyle('TH', parent=styles['Normal'],
                                     fontSize=10, textColor=sev_color,
                                     fontName='Helvetica-Bold')),
            Paragraph(t['severity'],
                      ParagraphStyle('SEV', parent=styles['Normal'],
                                     fontSize=9, textColor=sev_color,
                                     fontName='Helvetica-Bold',
                                     alignment=TA_CENTER))
        ], [
            Paragraph(t['description'], body_style), ''
        ]]
        tend_table = Table(tend_data, colWidths=[140*mm, 30*mm])
        tend_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0), sev_bg),
            ('BACKGROUND',  (0,1), (-1,1), white),
            ('GRID',        (0,0), (-1,-1), 0.5, HexColor('#e0e0e0')),
            ('SPAN',        (0,1), (1,1)),
            ('TOPPADDING',  (0,0), (-1,-1), 8),
            ('BOTTOMPADDING',(0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(tend_table)
        story.append(Spacer(1, 3*mm))

    story.append(Spacer(1, 4*mm))

    # ── POSSIBLE ISSUES ──────────────────────────────
    story.append(Paragraph('3. POSSIBLE UNDERLYING CONDITIONS', h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'Based on the analysis, the following underlying psychological conditions '
        'may be contributing to the observed patterns. This is NOT a clinical '
        'diagnosis — professional evaluation is required for accurate diagnosis:',
        body_style
    ))
    story.append(Spacer(1, 3*mm))

    issues = get_possible_issues(prediction_data)
    issues_data = [['Possible Condition', 'Likelihood', 'Clinical Notes']]
    for issue in issues:
        like_color = RED if issue['likelihood'] == 'High' else \
                     ORANGE if issue['likelihood'] == 'Moderate' else GREEN
        issues_data.append([
            issue['issue'],
            issue['likelihood'],
            issue['description']
        ])

    issues_table = Table(issues_data, colWidths=[45*mm, 25*mm, 100*mm])
    issues_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0), DARK_BLUE),
        ('TEXTCOLOR',    (0,0), (-1,0), white),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 9),
        ('ALIGN',        (1,0), (1,-1), 'CENTER'),
        ('GRID',         (0,0), (-1,-1), 0.5, HexColor('#bdbdbd')),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [white, LIGHT_BLUE]),
        ('TOPPADDING',   (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        ('WORDWRAP',     (0,0), (-1,-1), 1),
    ]))
    story.append(issues_table)
    story.append(Spacer(1, 6*mm))

    # ── PROFESSIONAL ADVICE ──────────────────────────
    story.append(Paragraph('4. PROFESSIONAL RECOMMENDATIONS', h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=DARK_BLUE))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'The following recommendations are provided based on the risk assessment '
        'findings. These are evidence-based suggestions aligned with clinical '
        'best practices for mental health intervention:',
        body_style
    ))
    story.append(Spacer(1, 3*mm))

    advice_list = get_professional_advice(prediction_data)
    for i, adv in enumerate(advice_list, 1):
        adv_data = [[
            Paragraph(f'{i}. {adv["area"]}',
                      ParagraphStyle('AH', parent=styles['Normal'],
                                     fontSize=10, textColor=DARK_BLUE,
                                     fontName='Helvetica-Bold'))
        ], [
            Paragraph(adv['advice'], body_style)
        ]]
        adv_table = Table(adv_data, colWidths=[170*mm])
        adv_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0), LIGHT_BLUE),
            ('BACKGROUND',  (0,1), (-1,1), white),
            ('GRID',        (0,0), (-1,-1), 0.5, HexColor('#e0e0e0')),
            ('TOPPADDING',  (0,0), (-1,-1), 8),
            ('BOTTOMPADDING',(0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(adv_table)
        story.append(Spacer(1, 3*mm))

    story.append(Spacer(1, 4*mm))

    # ── SUPPORT RESOURCES ────────────────────────────
    if prediction_data.get('alert_triggered'):
        story.append(Paragraph('5. EMERGENCY SUPPORT RESOURCES', h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=RED))
        story.append(Spacer(1, 3*mm))

        res_data = [
            ['Organization',          'Contact',        'Availability'],
            ['iCall',                 '9152987821',     'Mon-Sat, 8AM-10PM'],
            ['Vandrevala Foundation', '1860-2662-345',  '24/7'],
            ['AASRA',                 '9820466627',     '24/7'],
            ['iCall (WhatsApp)',       '+91 9152987821', 'Mon-Sat, 8AM-10PM'],
        ]
        res_table = Table(res_data, colWidths=[65*mm, 55*mm, 50*mm])
        res_table.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,0), RED),
            ('TEXTCOLOR',    (0,0), (-1,0), white),
            ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',     (0,0), (-1,-1), 9.5),
            ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
            ('GRID',         (0,0), (-1,-1), 0.5, HexColor('#bdbdbd')),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [LIGHT_RED, white]),
            ('TOPPADDING',   (0,0), (-1,-1), 8),
            ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ]))
        story.append(res_table)
        story.append(Spacer(1, 6*mm))

    # ── DISCLAIMER ───────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=GREY))
    story.append(Spacer(1, 3*mm))

    disclaimer_data = [[
        Paragraph(
            'IMPORTANT DISCLAIMER: This report is generated by an AI-powered system '
            'and is intended for preliminary screening purposes only. It does NOT '
            'constitute a clinical diagnosis or replace professional psychological '
            'evaluation. All findings should be reviewed by a qualified mental health '
            'professional. Model accuracy: 92.2%.',
            disclaimer_style
        )
    ]]
    disc_table = Table(disclaimer_data, colWidths=[170*mm])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), LIGHT_GREY),
        ('TOPPADDING',  (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
    ]))
    story.append(disc_table)
    story.append(Spacer(1, 3*mm))

    footer_data = [[
        Paragraph(
            f'Report ID: RPT-{report_id} | Generated: {datetime.datetime.now().strftime("%d %B %Y %H:%M")} | '
            f'Self Harm Detection System v2.0 | github.com/Architcybercrime/Self-harm-detection',
            disclaimer_style
        )
    ]]
    footer_table = Table(footer_data, colWidths=[170*mm])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), DARK_BLUE),
        ('TEXTCOLOR',   (0,0), (-1,-1), white),
        ('TOPPADDING',  (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0), (-1,-1), 6),
    ]))
    story.append(footer_table)

    doc.build(story)
    return filepath