"""
Stock Signal Generator - Alerts Module
======================================
Sends notifications via email and SMS.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
from datetime import datetime
import yaml
import os


class AlertManager:
    """Manages sending alerts via email and SMS."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.alert_config = self.config.get('alerts', {})
        
    def _format_signal_text(self, signal: Dict) -> str:
        """Format a single signal for text display."""
        emoji = {
            'STRONG BUY': '🟢🟢',
            'BUY': '🟢',
            'HOLD': '🟡',
            'SELL': '🔴',
            'STRONG SELL': '🔴🔴'
        }
        
        return (
            f"{emoji.get(signal['signal'], '⚪')} {signal['ticker']}: {signal['signal']}\n"
            f"   Price: ${signal['current_price']} ({signal['daily_change']:+.2f}%)\n"
            f"   Confidence: {signal['confidence']}%\n"
            f"   Buy Range: {signal['buy_range']}\n"
            f"   Sell Range: {signal['sell_range']}\n"
        )
    
    def _format_sms_brief(self, results: Dict) -> str:
        """Format a brief SMS summary."""
        regime = results['market_regime']['regime']
        summary = results['summary']
        
        lines = [f"📊 Market: {regime}"]
        
        if summary['strong_buy']:
            lines.append(f"🟢🟢 STRONG BUY: {', '.join(summary['strong_buy'])}")
        if summary['buy']:
            lines.append(f"🟢 BUY: {', '.join(summary['buy'])}")
        if summary['sell']:
            lines.append(f"🔴 SELL: {', '.join(summary['sell'])}")
        if summary['strong_sell']:
            lines.append(f"🔴🔴 STRONG SELL: {', '.join(summary['strong_sell'])}")
        
        if not any([summary['strong_buy'], summary['buy'], summary['sell'], summary['strong_sell']]):
            lines.append("No actionable signals")
        
        return '\n'.join(lines)
    
    def _format_email_html(self, results: Dict) -> str:
        """Format full HTML email report."""
        regime = results['market_regime']
        signals = results['signals']
        
        # Color coding
        regime_colors = {
            'BULLISH': '#22c55e',
            'NEUTRAL': '#eab308',
            'BEARISH': '#ef4444',
            'CRASH': '#7f1d1d'
        }
        
        signal_colors = {
            'STRONG BUY': '#15803d',
            'BUY': '#22c55e',
            'HOLD': '#6b7280',
            'SELL': '#ef4444',
            'STRONG SELL': '#991b1b'
        }
        
        # Sort signals by composite score
        sorted_signals = sorted(signals, key=lambda x: x['composite_score'], reverse=True)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background: #1f2937; color: white; padding: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .regime {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; margin-top: 10px; }}
                .market-info {{ padding: 15px 20px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; }}
                .market-info span {{ margin-right: 20px; }}
                .signals {{ padding: 20px; }}
                .signal-card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
                .signal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                .ticker {{ font-size: 20px; font-weight: bold; }}
                .signal-badge {{ padding: 4px 12px; border-radius: 4px; color: white; font-weight: bold; font-size: 14px; }}
                .details {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 14px; }}
                .detail {{ }}
                .detail-label {{ color: #6b7280; font-size: 12px; }}
                .detail-value {{ font-weight: 500; }}
                .positive {{ color: #22c55e; }}
                .negative {{ color: #ef4444; }}
                .indicators {{ margin-top: 10px; padding-top: 10px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
                .summary {{ padding: 20px; background: #f9fafb; }}
                .summary-group {{ margin-bottom: 10px; }}
                .summary-label {{ font-weight: bold; margin-right: 10px; }}
                .footer {{ padding: 15px 20px; text-align: center; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Stock Signal Report</h1>
                    <div class="regime" style="background: {regime_colors.get(regime['regime'], '#6b7280')};">
                        {regime['regime']} MARKET
                    </div>
                </div>
                
                <div class="market-info">
                    <span><strong>SPY:</strong> ${regime['details']['spy_price']} ({regime['details']['spy_vs_50ma']:+.1f}% vs 50MA)</span>
                    <span><strong>QQQ:</strong> ${regime['details']['qqq_price']} ({regime['details']['qqq_vs_50ma']:+.1f}% vs 50MA)</span>
                    <span><strong>VIX:</strong> {regime['details']['vix']}</span>
                </div>
                
                <div class="summary">
                    <div class="summary-group">
                        <span class="summary-label" style="color: #15803d;">🟢🟢 STRONG BUY:</span>
                        {', '.join(results['summary']['strong_buy']) or 'None'}
                    </div>
                    <div class="summary-group">
                        <span class="summary-label" style="color: #22c55e;">🟢 BUY:</span>
                        {', '.join(results['summary']['buy']) or 'None'}
                    </div>
                    <div class="summary-group">
                        <span class="summary-label" style="color: #ef4444;">🔴 SELL:</span>
                        {', '.join(results['summary']['sell']) or 'None'}
                    </div>
                    <div class="summary-group">
                        <span class="summary-label" style="color: #991b1b;">🔴🔴 STRONG SELL:</span>
                        {', '.join(results['summary']['strong_sell']) or 'None'}
                    </div>
                </div>
                
                <div class="signals">
                    <h2 style="margin-top: 0;">Detailed Signals</h2>
        """
        
        for signal in sorted_signals:
            change_class = 'positive' if signal['daily_change'] >= 0 else 'negative'
            
            html += f"""
                    <div class="signal-card">
                        <div class="signal-header">
                            <div>
                                <span class="ticker">{signal['ticker']}</span>
                                <span style="color: #6b7280; font-size: 14px; margin-left: 8px;">{signal['sector']}</span>
                            </div>
                            <span class="signal-badge" style="background: {signal_colors.get(signal['signal'], '#6b7280')};">
                                {signal['signal']}
                            </span>
                        </div>
                        
                        <div class="details">
                            <div class="detail">
                                <div class="detail-label">Price</div>
                                <div class="detail-value">${signal['current_price']} <span class="{change_class}">({signal['daily_change']:+.2f}%)</span></div>
                            </div>
                            <div class="detail">
                                <div class="detail-label">Confidence</div>
                                <div class="detail-value">{signal['confidence']}%</div>
                            </div>
                            <div class="detail">
                                <div class="detail-label">Score</div>
                                <div class="detail-value">{signal['composite_score']:.3f}</div>
                            </div>
                            <div class="detail">
                                <div class="detail-label">Buy Range</div>
                                <div class="detail-value">{signal['buy_range']}</div>
                            </div>
                            <div class="detail">
                                <div class="detail-label">Sell Range</div>
                                <div class="detail-value">{signal['sell_range']}</div>
                            </div>
                            <div class="detail">
                                <div class="detail-label">Support / Resist</div>
                                <div class="detail-value">${signal['support']} / ${signal['resistance']}</div>
                            </div>
                        </div>
                        
                        <div class="indicators">
                            RSI: {signal['indicators']['rsi']} | 
                            MACD Hist: {signal['indicators']['macd_hist']:.4f} | 
                            BB%: {signal['indicators']['bb_position']:.0f}% |
                            vs 50MA: {signal['indicators']['vs_sma50']:+.1f}% |
                            Vol Ratio: {signal['indicators']['volume_ratio']:.1f}x
                        </div>
                    </div>
            """
        
        html += f"""
                </div>
                
                <div class="footer">
                    Generated at {results['generated_at']}<br>
                    <em>This is not financial advice. Always do your own research.</em>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_email(self, results: Dict, attach_html: bool = True) -> bool:
        """Send email alert with full report."""
        email_config = self.alert_config.get('email', {})
        
        if not email_config.get('enabled', False):
            print("Email alerts disabled")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 Stock Signals - {results['market_regime']['regime']} Market - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            msg['From'] = email_config['sender_email']
            msg['To'] = ', '.join(email_config['recipient_emails'])
            
            # Plain text version
            text_content = f"Market Regime: {results['market_regime']['regime']}\n\n"
            text_content += f"STRONG BUY: {', '.join(results['summary']['strong_buy']) or 'None'}\n"
            text_content += f"BUY: {', '.join(results['summary']['buy']) or 'None'}\n"
            text_content += f"SELL: {', '.join(results['summary']['sell']) or 'None'}\n"
            text_content += f"STRONG SELL: {', '.join(results['summary']['strong_sell']) or 'None'}\n\n"
            
            for signal in results['signals']:
                text_content += self._format_signal_text(signal) + "\n"
            
            msg.attach(MIMEText(text_content, 'plain'))
            
            # HTML version
            html_content = self._format_email_html(results)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)
            
            print(f"✅ Email sent to {len(email_config['recipient_emails'])} recipients")
            return True
            
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False
    
    def send_sms_via_email(self, results: Dict) -> bool:
        """Send SMS via email-to-SMS gateway."""
        sms_config = self.alert_config.get('sms', {})
        email_config = self.alert_config.get('email', {})
        
        if not sms_config.get('enabled', False):
            print("SMS alerts disabled")
            return False
        
        if not email_config.get('enabled', False):
            print("Email required for SMS gateway")
            return False
        
        try:
            brief = self._format_sms_brief(results)
            
            for recipient in sms_config.get('recipients', []):
                msg = MIMEText(brief)
                msg['Subject'] = 'Stock Alert'
                msg['From'] = email_config['sender_email']
                msg['To'] = recipient
                
                with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                    server.starttls()
                    server.login(email_config['sender_email'], email_config['sender_password'])
                    server.send_message(msg)
            
            print(f"✅ SMS sent to {len(sms_config['recipients'])} recipients")
            return True
            
        except Exception as e:
            print(f"❌ SMS failed: {e}")
            return False
    
    def send_twilio_sms(self, results: Dict) -> bool:
        """Send SMS via Twilio (more reliable but paid)."""
        twilio_config = self.alert_config.get('twilio', {})
        
        if not twilio_config.get('enabled', False):
            return False
        
        try:
            from twilio.rest import Client
            
            client = Client(twilio_config['account_sid'], twilio_config['auth_token'])
            brief = self._format_sms_brief(results)
            
            for to_number in twilio_config.get('to_numbers', []):
                message = client.messages.create(
                    body=brief,
                    from_=twilio_config['from_number'],
                    to=to_number
                )
                print(f"✅ Twilio SMS sent: {message.sid}")
            
            return True
            
        except ImportError:
            print("❌ Twilio not installed. Run: pip install twilio")
            return False
        except Exception as e:
            print(f"❌ Twilio SMS failed: {e}")
            return False
    
    def send_all_alerts(self, results: Dict) -> Dict[str, bool]:
        """Send all configured alerts."""
        return {
            'email': self.send_email(results),
            'sms_gateway': self.send_sms_via_email(results),
            'twilio': self.send_twilio_sms(results)
        }
