from flask import Flask, jsonify, render_template
import os
from supabase import create_client, Client
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# --- Supabase Configuration ---
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and Key must be set in the .env file.")

supabase: Client = create_client(supabase_url, supabase_key)

# --- Global Constants ---
# Define the list of labs once to avoid repetition (DRY principle)
LABS = [
    "The Basics of Google Cloud Compute", "Get Started with Cloud Storage",
    "Get Started with Pub_Sub", "Get Started with API Gateway",
    "Get Started with Looker", "Get Started with Dataplex",
    "Get Started with Google Workspace Tools", "App Building with AppSheet",
    "Develop with Apps Script and AppSheet",
    "Develop GenAI Apps with Gemini and Streamlit",
    "Build a Website on Google Cloud", "Set Up a Google Cloud Network",
    "Store, Process, and Manage Data on Google Cloud - Console",
    "Cloud Run Functions: 3 Ways", "App Engine: 3 Ways",
    "Cloud Speech API: 3 Ways", "Analyze Speech and Language with Google APIs",
    "Monitoring in Google Cloud", "Prompt Design in Vertex AI"
]

def get_initials(name):
    """Gets the initials from a name."""
    parts = name.split()
    if len(parts) > 1:
        return parts[0][0].upper() + parts[1][0].upper()
    elif parts:
        return parts[0][0].upper()
    return ""

def get_processed_participant_data():
    """
    OPTIMIZED: Fetches all participant data in a single query and processes it.
    This is much more efficient than making multiple queries per request.
    Returns a tuple: (list_of_participants, dict_of_lab_completion_counts)
    """
    # 1. Fetch all participant data in ONE go
    try:
        all_participants_raw = supabase.table("participants").select("*").execute().data
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return [], {lab: 0 for lab in LABS} # Return empty data on error

    # 2. Initialize containers to hold processed data
    processed_participants = []
    lab_completion_counts = {lab: 0 for lab in LABS}

    # 3. Process the raw data in a single loop (in memory, very fast)
    for row in all_participants_raw:
        completed_labs_list = []
        for lab in LABS:
            if row.get(lab) == "Yes":
                completed_labs_list.append(lab)
                lab_completion_counts[lab] += 1 # Increment count for this lab

        processed_participants.append({
            "name": row.get("name", "N/A"),
            "email": row.get("email", "N/A"),
            "completed_labs": len(completed_labs_list),
            "name_of_completed_labs": completed_labs_list
        })

    # 4. Sort participants by the number of labs they completed
    processed_participants.sort(key=lambda x: x["completed_labs"], reverse=True)

    # 5. Add final derived fields like rank, initials, and percentages
    final_participant_data = []
    for rank, user in enumerate(processed_participants, start=1):
        user["rank"] = rank
        user["initials"] = get_initials(user["name"])
        user['badge_count'] = user['completed_labs']
        user['completion_percentage'] = round((user['completed_labs'] / len(LABS)) * 100) if LABS else 0
        final_participant_data.append(user)

    return final_participant_data, lab_completion_counts


@app.route('/')
def index():
    """Renders the home page."""
    return render_template('index.html')


@app.route('/progress')
def progress():
    """Renders the progress page."""
    return render_template('progress.html')


@app.route('/api/home-data')
def get_stats():
    """Provides statistics for the home page using the single optimized function."""
    # Call the efficient function ONCE to get all data
    participant_data, badge_completion_rate = get_processed_participant_data()

    total_participants = len(participant_data)
    
    # Handle case with no participants to avoid division by zero errors
    if total_participants == 0:
        return jsonify({
            'total_participants': 0,
            'completion_percentage': 0,
            'average_progress': 0,
            'top_performer': {'name': 'N/A', 'initials': 'N/A', 'badges': 0},
            'badge_completion_rate': badge_completion_rate,
            'badge_popularity': []
        })

    total_completed_all = sum(1 for p in participant_data if p["completed_labs"] == len(LABS))
    completion_percentage = (total_completed_all / total_participants) * 100

    total_badges = sum(p["completed_labs"] for p in participant_data)
    average_progress = total_badges / total_participants

    # Find the top performer (list is already sorted, so it's the first one)
    top_performer_data = participant_data[0]
    if top_performer_data["completed_labs"] > 0:
        top_performer = {
            "name": top_performer_data["name"],
            "initials": top_performer_data["initials"],
            "badges": top_performer_data["completed_labs"]
        }
    else:
        top_performer = {"name": "N/A", "initials": "N/A", "badges": 0}

    # Get top 6 popular badges
    badge_popularity = sorted(badge_completion_rate.items(), key=lambda item: item[1], reverse=True)[:6]

    return jsonify({
        'total_participants': total_participants,
        'completion_percentage': round(completion_percentage),
        'average_progress': round(average_progress),
        'top_performer': top_performer,
        'badge_completion_rate': badge_completion_rate,
        'badge_popularity': badge_popularity
    })


@app.route('/api/progress-data')
def get_progress_data():
    """Provides data for the progress page leaderboard using the single optimized function."""
    participant_data, _ = get_processed_participant_data() # We don't need lab_counts here

    return jsonify({
        'labs': LABS,
        'participants': participant_data
    })


if __name__ == '__main__':
    app.run(debug=True)