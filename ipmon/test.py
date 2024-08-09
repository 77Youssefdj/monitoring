import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ipmon import app, db
from ipmon.database import PollHistory

# Create an application context
with app.app_context():
    # Check if the database connection is working and fetch data
    poll_data = PollHistory.query.all()
    for entry in poll_data:
        print(entry.id, entry.poll_time, entry.poll_status)
