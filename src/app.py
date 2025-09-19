"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
import os
from pathlib import Path
from pymongo import MongoClient
from typing import Dict, Any

# Initialize MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['mergington_high']
activities_collection = db['activities']

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Initial activities data - will be used to populate MongoDB if collection is empty
initial_activities = {
    "Chess Club": {
        "name": "Chess Club",  # Adding name field to match the key
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "name": "Programming Class",
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "name": "Gym Class",
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "name": "Soccer Team",
        "description": "Team training, drills, and inter-school matches",
        "schedule": "Mondays, Thursdays, 4:00 PM - 6:00 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "name": "Basketball Team",
        "description": "Practice sessions and competitive games",
        "schedule": "Tuesdays, Fridays, 4:00 PM - 6:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "isabella@mergington.edu"]
    },
    "Drama Club": {
        "name": "Drama Club",
        "description": "Acting exercises, rehearsals, and school plays",
        "schedule": "Wednesdays, 3:30 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["mia@mergington.edu", "charlotte@mergington.edu"]
    },
    "Choir": {
        "name": "Choir",
        "description": "Vocal training and performances for concerts and events",
        "schedule": "Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 40,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Science Club": {
        "name": "Science Club",
        "description": "Experiments, science fairs, and research projects",
        "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["noelle@mergington.edu", "ethan@mergington.edu"]
    },
    "Debate Team": {
        "name": "Debate Team",
        "description": "Debate practice, public speaking, and tournaments",
        "schedule": "Tuesdays, 4:00 PM - 5:30 PM",
        "max_participants": 16,
        "participants": ["lucas@mergington.edu", "sophia.r@mergington.edu"]
    }
}

# Initialize the database with activities if it's empty
if activities_collection.count_documents({}) == 0:
    # Insert each activity, using the name as both the key and a field
    for name, activity in initial_activities.items():
        activities_collection.insert_one(activity)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    """Get all activities"""
    # Convert MongoDB cursor to dict with activity name as key
    activities_dict = {
        activity["name"]: {k: v for k, v in activity.items() if k != "_id"}
        for activity in activities_collection.find()
    }
    
    # Return with no-store cache header
    return JSONResponse(content=activities_dict, headers={"Cache-Control": "no-store"})


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Try to find the activity
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")
    
    # Add student using $push operator
    result = activities_collection.update_one(
        {"name": activity_name},
        {"$push": {"participants": email}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")
        
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/participants")
def unregister_participant(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Try to find the activity
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate participant exists
    if email not in activity["participants"]:
        raise HTTPException(status_code=404, detail="Participant not found for this activity")

    # Remove participant using $pull operator
    result = activities_collection.update_one(
        {"name": activity_name},
        {"$pull": {"participants": email}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")
        
    return {"message": f"Unregistered {email} from {activity_name}"}
