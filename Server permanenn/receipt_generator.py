import os
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime

class ReceiptGenerator:
    """Generate PDF receipts for transactions"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
        )
        
        self.right_align_style = ParagraphStyle(
            'CustomRightAlign',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
        )
        
    def format_currency(self, amount):
        """Format currency to Indonesian Rupiah format"""
        return f"Rp {amount:,.0f}".replace(",", ".")
        
    def generate_pdf(self, transaction_data):
        """Generate PDF receipt from transaction data"""
        try:
            # Create receipts directory if it doesn't exist
            receipts_dir = 'receipts'
            os.makedirs(receipts_dir, exist_ok=True)
            
            # Generate filename
            filename = f"receipt_{transaction_data['id']}.pdf"
            filepath = os.path.join(receipts_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Header
            story.append(Paragraph("KASIR GACOAN", self.title_style))
            story.append(Paragraph("Sistem Point of Sale", self.header_style))
            story.append(Spacer(1, 12))
            
            # Transaction info
            transaction_date = datetime.fromisoformat(transaction_data['date'].replace('Z', '+00:00'))
            formatted_date = transaction_date.strftime("%d/%m/%Y %H:%M:%S")
            
            info_data = [
                ['Transaction ID:', transaction_data['id']],
                ['Date:', formatted_date],
                ['Cashier:', transaction_data['cashier']],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Items table
            items_data = [['Item', 'Qty', 'Price', 'Subtotal']]
            
            for item in transaction_data['items']:
                # Handle both dict with 'name' and dict with 'product_name' keys
                item_name = item.get('name') or item.get('product_name', 'Unknown Item')
                item_price = item.get('price', 0)
                item_quantity = item.get('quantity', 0)
                
                items_data.append([
                    str(item_name),
                    str(item_quantity),
                    self.format_currency(item_price),
                    self.format_currency(item_price * item_quantity)
                ])
            
            items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1.2*inch, 1.2*inch])
            items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
                # Borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(items_table)
            story.append(Spacer(1, 20))
            
            # Summary table
            summary_data = [
                ['Subtotal:', self.format_currency(transaction_data['subtotal'])],
            ]
            
            if transaction_data['discount'] > 0:
                summary_data.append(['Discount:', f"-{self.format_currency(transaction_data['discount'])}"])
            
            summary_data.extend([
                ['Total:', self.format_currency(transaction_data['total'])],
                ['Payment:', self.format_currency(transaction_data['payment'])],
                ['Change:', self.format_currency(transaction_data['change'])],
            ])
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),  # Bold for total, payment, change
                ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),  # Line above total
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Footer
            story.append(Paragraph("Terima kasih atas kunjungan Anda!", self.header_style))
            story.append(Paragraph("Selamat menikmati!", self.header_style))
            
            # Build PDF
            doc.build(story)
            
            logging.info(f"Receipt PDF generated: {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"Error generating receipt PDF: {str(e)}")
            raise e
