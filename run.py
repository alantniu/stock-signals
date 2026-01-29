#!/usr/bin/env python3
"""
Stock Signal Generator - Main Runner
====================================
Run this script to generate signals, update dashboard, and send alerts.

Usage:
    python run.py              # Run once
    python run.py --no-alerts  # Run without sending alerts
    python run.py --no-options # Run without options analysis
    python run.py --schedule   # Run on schedule (3x daily)
"""

import argparse
import json
from datetime import datetime
import os
import sys

from signals import SignalEngine
from alerts import AlertManager
from dashboard import generate_dashboard


def run_signal_generation(send_alerts: bool = True, analyze_options: bool = True, output_dir: str = '.') -> dict:
    """Run the full signal generation pipeline."""
    
    print("=" * 60)
    print(f"🚀 Stock Signal Generator")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Initialize engine
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    engine = SignalEngine(config_path)
    
    # Generate signals
    results = engine.generate_all_signals()
    
    print()
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Market Regime: {results['market_regime']['regime']}")
    print(f"Signal Modifier: {results['market_regime']['modifier']:.1f}x")
    print()
    print(f"🟢🟢 STRONG BUY:  {', '.join(results['summary']['strong_buy']) or 'None'}")
    print(f"🟢   BUY:         {', '.join(results['summary']['buy']) or 'None'}")
    print(f"🟡   HOLD:        {len(results['summary']['hold'])} stocks")
    print(f"🔴   SELL:        {', '.join(results['summary']['sell']) or 'None'}")
    print(f"🔴🔴 STRONG SELL: {', '.join(results['summary']['strong_sell']) or 'None'}")
    print()
    
    # Analyze options for actionable signals
    options_data = None
    if analyze_options:
        print("=" * 60)
        print("📈 ANALYZING LEAPS OPTIONS")
        print("=" * 60)
        try:
            from options import analyze_options_for_signals
            options_data = analyze_options_for_signals(results['signals'])
            
            # Print options summary
            print()
            for opt_result in options_data:
                if opt_result['options']:
                    top_opt = opt_result['options'][0]
                    print(f"  {opt_result['ticker']}: {opt_result['recommendation']}")
                    print(f"    → Best: ${top_opt['strike']} {top_opt['option_type']} exp {top_opt['expiry']}")
                    print(f"      Price: ${top_opt['mid_price']} | Return at target: {top_opt['return_at_target']:+.0f}%")
            print()
        except Exception as e:
            print(f"⚠️ Options analysis failed: {e}")
            print("   Continuing without options data...")
            options_data = None
    
    # Generate dashboard
    dashboard_path = os.path.join(output_dir, 'dashboard.html')
    generate_dashboard(results, dashboard_path, options_data)
    
    # Save JSON results
    json_path = os.path.join(output_dir, 'signals.json')
    results_with_options = results.copy()
    if options_data:
        results_with_options['options'] = options_data
    with open(json_path, 'w') as f:
        json.dump(results_with_options, f, indent=2, default=str)
    print(f"✅ JSON data saved: {json_path}")
    
    # Send alerts
    if send_alerts:
        print()
        print("📬 Sending alerts...")
        alert_manager = AlertManager(config_path)
        alert_results = alert_manager.send_all_alerts(results)
        print(f"   Email: {'✅' if alert_results['email'] else '❌'}")
        print(f"   SMS Gateway: {'✅' if alert_results['sms_gateway'] else '❌'}")
        print(f"   Twilio: {'✅' if alert_results['twilio'] else '❌'}")
    
    print()
    print("=" * 60)
    print("✅ Complete!")
    print("=" * 60)
    
    return results


def run_scheduler():
    """Run on schedule (3x daily during market hours)."""
    import schedule
    import time
    from datetime import datetime
    import pytz
    
    # Load config for schedule
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    tz_name = config.get('schedule', {}).get('timezone', 'America/New_York')
    check_times = config.get('schedule', {}).get('checks', ['09:35', '12:30', '15:00'])
    
    print(f"📅 Scheduler started")
    print(f"   Timezone: {tz_name}")
    print(f"   Check times: {', '.join(check_times)}")
    print()
    
    def job():
        print(f"\n🔔 Scheduled run triggered at {datetime.now()}")
        run_signal_generation(send_alerts=True)
    
    # Schedule jobs
    for check_time in check_times:
        schedule.every().monday.at(check_time).do(job)
        schedule.every().tuesday.at(check_time).do(job)
        schedule.every().wednesday.at(check_time).do(job)
        schedule.every().thursday.at(check_time).do(job)
        schedule.every().friday.at(check_time).do(job)
    
    print("Waiting for scheduled times... (Ctrl+C to stop)")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description='Stock Signal Generator')
    parser.add_argument('--no-alerts', action='store_true', help='Skip sending alerts')
    parser.add_argument('--no-options', action='store_true', help='Skip options analysis')
    parser.add_argument('--schedule', action='store_true', help='Run on schedule (3x daily)')
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory for files')
    
    args = parser.parse_args()
    
    if args.schedule:
        run_scheduler()
    else:
        run_signal_generation(
            send_alerts=not args.no_alerts,
            analyze_options=not args.no_options,
            output_dir=args.output_dir
        )


if __name__ == '__main__':
    main()
