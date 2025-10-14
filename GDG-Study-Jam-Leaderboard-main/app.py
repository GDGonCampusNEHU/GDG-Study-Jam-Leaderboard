from flask import Flask, jsonify, render_template
import os
from supabase import create_client, Client
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

# --- Supabase Configuration ---
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Check if the credentials are provided
if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and Key must be set in the .env file.")

# Initialize the Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

LABS = [
    "The Basics of Google Cloud Compute",
    "Get Started with Cloud Storage",
    "Get Started with Pub_Sub",
    "Get Started with API Gateway",
    "Get Started with Looker",
    "Get Started with Dataplex",
    "Get Started with Google Workspace Tools",
    "App Building with AppSheet",
    "Develop with Apps Script and AppSheet",
    "Develop GenAI Apps with Gemini and Streamlit",
    "Build a Website on Google Cloud",
    "Set Up a Google Cloud Network",
    "Store, Process, and Manage Data on Google Cloud - Console",
    "Cloud Run Functions: 3 Ways",
    "App Engine: 3 Ways",
    "Cloud Speech API: 3 Ways",
    "Analyze Speech and Language with Google APIs",
    "Monitoring in Google Cloud",
    "Prompt Design in Vertex AI"
]


def get_initials(name):
    """Gets the initials from a name."""
    parts = name.split()
    if len(parts) > 1:
        return parts[0][0].upper() + parts[1][0].upper()
    elif parts:
        return parts[0][0].upper()
    return ""


def get_participant_data():
    """Retrieves participant data"""
    data = supabase.table("participants").select("*").execute().data
    LAB_NAMES = [
        "The Basics of Google Cloud Compute",
        "Get Started with Cloud Storage",
        "Get Started with Pub_Sub",
        "Get Started with API Gateway",
        "Get Started with Looker",
        "Get Started with Dataplex",
        "Get Started with Google Workspace Tools",
        "App Building with AppSheet",
        "Develop with Apps Script and AppSheet",
        "Develop GenAI Apps with Gemini and Streamlit",
        "Build a Website on Google Cloud",
        "Set Up a Google Cloud Network",
        "Store, Process, and Manage Data on Google Cloud - Console",
        "Cloud Run Functions: 3 Ways",
        "App Engine: 3 Ways",
        "Cloud Speech API: 3 Ways",
        "Analyze Speech and Language with Google APIs",
        "Monitoring in Google Cloud",
        "Prompt Design in Vertex AI"
    ]
    names_of_lab = []
    ranking_list = []

    for row in data:
        completed = sum(1 for lab in LAB_NAMES if row.get(lab) == "Yes")
        for lab in LAB_NAMES:
            if row.get(lab) == "Yes":
                names_of_lab.append(lab)
        ranking_list.append({
            "name": row["name"],
            "email": row["email"],
            "completed": completed,
            "name_of_lab": names_of_lab
        })
        names_of_lab = []

    # Sort and assign ranks
    ranking_list.sort(key=lambda x: x["completed"], reverse=True)

    participant_data = []
    for rank, user in enumerate(ranking_list, start=1):
        participant_data.append({
            "rank": rank,
            "name": user["name"],
            "initials": get_initials(user["name"]),
            "completed_labs": user["completed"],
            "name_of_completed_labs": user["name_of_lab"]
        })
    return participant_data


def labs_completion_rate():
    """No of Completions for each lab"""
    lab_counts = {}

    for lab in LABS:
        response = supabase.table("participants").select("*", count="exact").eq(lab, "Yes").execute()
        lab_counts[lab] = response.count

    return lab_counts


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
    """Provides statistics for the home page."""
    participant_data = get_participant_data()
    total_participants = len(participant_data)

    total_possible = 20*total_participants
    total_completed_all = 0

    for participant in participant_data:
        labs_count = participant.get("completed_labs", 0)
        total_completed_all += labs_count



    if total_participants > 0:
        completion_percentage = (total_completed_all / total_possible) * 100
    else:
        completion_percentage = 0

    print("\n", total_completed_all, completion_percentage)

    total_badges = 0
    for i in participant_data:
        total_badges += i["completed_labs"]
    print("\n",total_badges)
    if total_participants > 0:
        average_progress = total_badges / total_participants
    else:
        average_progress = 0

    flag = 0
    top_performer = {}
    for i in participant_data:
        if i["rank"] == 1 and i["completed_labs"] > 0:
            top_performer = {"name": i["name"], "initials": i["initials"], "badges": i["completed_labs"]}
            flag = 1
            break

    if flag != 1:
        top_performer = {"name": "N/A", "initials": "N/A", "badges": 0}

    print("\n", top_performer)

    badge_completion_rate = labs_completion_rate()
    print("\n", badge_completion_rate)

    badge_popularity = sorted(badge_completion_rate.items(), key=lambda x: x[1], reverse=True)[:6]

    return jsonify({
        'total_participants': total_participants,
        'completion_percentage': round(completion_percentage),
        'average_progress': round(average_progress),
        'top_performer': {
            'name': top_performer['name'],
            'initials': top_performer['initials'],
            'badges': top_performer["badges"]
        },
        'badge_completion_rate': badge_completion_rate,
        'badge_popularity': badge_popularity
    })


@app.route('/api/progress-data')
def get_progress_data():
    """Provides data for the progress page leaderboard."""
    participant_data = get_participant_data()

    for p in participant_data:
        p['badge_count'] = p['completed_labs']
        p['completion_percentage'] = round((p['completed_labs'] / len(LABS)) * 100)

    print(participant_data)
    return jsonify({
        'labs': LABS,
        'participants': participant_data
    })


if __name__ == '__main__':
    app.run(debug=True)
