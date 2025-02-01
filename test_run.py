import time
import schedule
import pytz
import os
import logging
from datetime import datetime
from scripts.writer_agent import NovelGenerator
from scripts.github_ops import GitManager
import argparse

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'scheduler.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def daily_task():
    """Execute daily writing and commit routine"""
    retries = 0
    max_retries = 3
    
    while retries < max_retries:
        try:
            logging.info("Starting daily writing task")
            writer = NovelGenerator()
            
            if writer.create_daily_content():
                logging.info("Content generated successfully")
                GitManager().commit_changes()
                logging.info("Changes committed to GitHub")
                return
            else:
                logging.warning("Content generation failed")
                raise RuntimeError("Content generation returned False")
                
        except Exception as e:
            retries += 1
            logging.warning(f"Attempt {retries} failed: {str(e)}")
            time.sleep(300)  # Wait 5 minutes between retries
    
    logging.error("All daily task retries exhausted")

def main(scheduled=True):
    """Main execution handler with scheduling"""
    if scheduled:
        # Configure for your timezone
        tz = pytz.timezone("Asia/Kolkata")  # CHANGE THIS
        schedule.every().day.at("09:00", tz).do(daily_task)
        
        logging.info("Scheduler started")
        print("AI Writer Scheduler Running (Daily at 9 AM)...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
                logging.info("Scheduler heartbeat")  # Monitor alive status
        except KeyboardInterrupt:
            logging.info("Scheduler interrupted by user")
        except Exception as e:
            logging.critical(f"Scheduler crashed: {str(e)}")
            raise
    else:
        daily_task()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AI Novel Writer')
    parser.add_argument('--auto', action='store_true',
                      help='Enable daily auto-scheduling at 9 AM')
    args = parser.parse_args()

    try:
        main(scheduled=args.auto)
    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}", exc_info=True)
        raise