from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import shutil
from datetime import datetime
import pyscreenshot as ImageGrab
from apscheduler.schedulers.background import BackgroundScheduler
import cloudinary
import cloudinary.uploader

# load .env file
load_dotenv()

# config cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

app = FastAPI()

# cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create default background scheduler
sched = BackgroundScheduler()
sched.start()

isrunning = False

# function for taking screenshot
def take_screenshot():
    image_name = f"screenshot-{str(datetime.now()).replace(':', '')}.png"
    
    screen_shot = ImageGrab.grab()
    
    # Save screenshot to a temporary location
    temp_path = f"./{image_name}"
    screen_shot.save(temp_path)

    # upload in cloudinary
    response = cloudinary.uploader.upload(temp_path, folder="screenshots")

    # remove the temp file
    os.remove(temp_path)

# function to clear the screenshots
def clear_media():
    dir = 'media'
    shutil.rmtree(dir)
    os.mkdir(dir)

# api for taking screenshots
@app.post("/start_screenshot")
def start_screenshot(background_tasks: BackgroundTasks):
    global isrunning
    if not isrunning:
        if not sched.get_job('screenshot_job'):
            sched.add_job(take_screenshot, 'interval', seconds=5, id='screenshot_job')
        else:
            sched.resume_job('screenshot_job')
        
        if not sched.get_job('clear_media_job'):
            sched.add_job(clear_media, 'cron', hour=23, minute=42, id='clear_media_job')
        else:
            sched.resume_job('clear_media_job')
        
        isrunning = True
    return {"message": "Screenshot taking started"}

# api for stopping the screenshots
@app.post("/stop_screenshot")
def stop_screenshot():
    global isrunning
    if isrunning:
        sched.pause_job('screenshot_job')
        sched.pause_job('clear_media_job')
        isrunning = False
    return {"message": "Screenshot taking stopped"}

#api for listing all the screenshots
@app.get("/screenshots")
def get_screenshots():
    # cloudinary api for fetching all images
    response = cloudinary.api.resources(type="upload", prefix="screenshots")
    photo_urls = [resource['secure_url'] for resource in response['resources']]
    return {"photo_urls": photo_urls}


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
