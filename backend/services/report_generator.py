import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.config import REPORTS_DIR
from backend.utils.logger import setup_logger

logger = setup_logger("report_generator")

class ReportGeneratorService:
    def generate_pdf_report(self, alert_db_model, analysis_result: dict, comparison_image_path: str) -> str:
        """
        Generates a professional PDF evidence report for a deforestation alert.
        
        Args:
            alert_db_model: The Alert database record.
            analysis_result (dict): The result from LLM reasoning.
            comparison_image_path (str): Path to the 4-panel comparison PNG.
            
        Returns:
            str: Path to the generated PDF report.
        """
        try:
            report_id = f"FG_REPORT_{alert_db_model.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            pdf_path = REPORTS_DIR / f"{report_id}.pdf"
            
            logger.info(f"Generating PDF report at: {pdf_path}")
            
            # Ensure folder exists
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 1. Setup Document
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # 2. Custom Styles
            # Risk color coding
            risk_level = analysis_result.get("risk_level", "Medium").upper()
            if risk_level == "CRITICAL":
                header_bg = colors.HexColor("#C0392B")  # Dark Red
            elif risk_level == "HIGH":
                header_bg = colors.HexColor("#D35400")  # Orange
            elif risk_level == "MEDIUM":
                header_bg = colors.HexColor("#F39C12")  # Yellow
            else:
                header_bg = colors.HexColor("#27AE60")  # Green
                
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.white,
                spaceAfter=10,
                alignment=1 # Centered
            )
            
            section_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor("#2C3E50"),
                spaceBefore=12,
                spaceAfter=6,
                borderPadding=4
            )
            
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['Normal'],
                fontSize=10.5,
                leading=14,
                textColor=colors.HexColor("#2C3E50")
            )
            
            table_header_style = ParagraphStyle(
                'TableHeader',
                parent=styles['Normal'],
                fontSize=9.5,
                leading=12,
                textColor=colors.white,
                fontName='Helvetica-Bold'
            )
            
            table_cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=9.5,
                leading=12,
                textColor=colors.HexColor("#34495E")
            )

            # 3. Header Banner Table
            header_data = [
                [Paragraph("FORESTGUARD INCIDENT EVIDENCE REPORT", title_style)],
                [Paragraph(f"RISK RATING: {risk_level} &nbsp;|&nbsp; STATUS: UNRESOLVED &nbsp;|&nbsp; ID: {report_id}", ParagraphStyle('Sub', parent=title_style, fontSize=10))]
            ]
            header_table = Table(header_data, colWidths=[530])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), header_bg),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('TOPPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 15))
            
            # 4. Incident Metadata Table
            pa_name = alert_db_model.region.name if alert_db_model.region else "Outside Region of Interest"
            is_protected_str = "YES" if analysis_result.get("is_protected", False) else "NO"
            if analysis_result.get("is_protected"):
                is_protected_str += f" ({analysis_result.get('protected_area_name')})"
                
            metadata_data = [
                [Paragraph("Coordinate GPS (Lat, Lon)", table_header_style), Paragraph(f"{alert_db_model.latitude:.6f}, {alert_db_model.longitude:.6f}", table_cell_style)],
                [Paragraph("Detection Timestamp", table_header_style), Paragraph(alert_db_model.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC'), table_cell_style)],
                [Paragraph("Detected Area (GFW Alert)", table_header_style), Paragraph(f"{alert_db_model.area_ha:.2f} Hectares", table_cell_style)],
                [Paragraph("Verified Loss Area (NDVI)", table_header_style), Paragraph(f"{alert_db_model.ndvi_diff is not None and f'{alert_db_model.ndvi_diff:.2f}' or 'N/A'} Hectares", table_cell_style)],
                [Paragraph("Mean NDVI Drop", table_header_style), Paragraph(f"{alert_db_model.ndvi_diff is not None and f'{alert_db_model.ndvi_diff:.3f}' or 'N/A'}", table_cell_style)],
                [Paragraph("Inside Protected Boundary", table_header_style), Paragraph(is_protected_str, table_cell_style)],
                [Paragraph("Active Cluster Nearby (30d)", table_header_style), Paragraph(f"{analysis_result.get('neighboring_alerts_30d', 0)} nearby alerts", table_cell_style)],
            ]
            
            metadata_table = Table(metadata_data, colWidths=[180, 350])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#34495E")),
                ('BACKGROUND', (1,0), (1,-1), colors.HexColor("#ECF0F1")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.white),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 15))
            
            # 5. Visual Evidence Section
            story.append(Paragraph("Visual Evidence: Pre- vs Post-Clearing Satellite Comparison", section_style))
            if comparison_image_path and os.path.exists(comparison_image_path):
                # Scale the image to fit the page nicely (width ~500 pixels, height ~250 pixels)
                # Max width on letter is 612 - 80 = 532.
                img_flowable = Image(comparison_image_path, width=480, height=320)
                story.append(img_flowable)
            else:
                story.append(Paragraph("[Missing Visual Imagery]", body_style))
                
            story.append(Spacer(1, 15))
            
            # 6. LLM Analysis Narrative Summary
            story.append(Paragraph("Incident Summary & AI Reasoning Analysis", section_style))
            narrative = analysis_result.get("narrative_summary", "No narrative available.")
            story.append(Paragraph(narrative, body_style))
            
            # 7. Action Plan
            story.append(Paragraph("Recommended Action Plan", section_style))
            action = analysis_result.get("recommended_action", "Monitor coordinates for further updates.")
            
            action_box_data = [[
                Paragraph("<b>URGENT ACTION DIRECTIVE:</b><br/>" + action, ParagraphStyle('ActionText', parent=body_style, textColor=colors.HexColor("#7F8C8D")))
            ]]
            action_box_table = Table(action_box_data, colWidths=[530])
            action_box_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9F9")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#BDC3C7")),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ]))
            story.append(action_box_table)
            
            # 8. Build Document
            doc.build(story)
            logger.info("PDF report generation complete.")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise e
