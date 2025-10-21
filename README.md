# Watch Party - Setup Guide

## 📁 Project Structure

Create this folder structure:

```
watch-party/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
└── README.md
```

## 🚀 Installation Steps

### 1. Install Python
Make sure you have Python 3.8+ installed. Check with:
```bash
python --version
```

### 2. Create Project Folder
```bash
mkdir watch-party
cd watch-party
```

### 3. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Create Folders
```bash
mkdir templates
```

### 6. Add Files
- Copy `app.py` to the root folder
- Copy `index.html` to the `templates/` folder
- Copy `requirements.txt` to the root folder

## ▶️ Running the Application

### Start the Server
```bash
python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

### Access the Application
1. Open your browser and go to: `http://localhost:5000`
2. Your friend can access it via your local IP: `http://YOUR_IP:5000`

To find your IP:
- **Windows**: Open CMD and type `ipconfig` (look for IPv4 Address)
- **Mac/Linux**: Open Terminal and type `ifconfig` or `ip addr`

## 📝 How to Use

### For You (Host):
1. Enter your name
2. Leave room code empty (it will create one automatically)
3. Click "Join/Create Room"
4. Share the room code with your friend
5. Click "Start Camera & Mic"
6. Load a video (URL or local file)
7. Use "Sync Play/Pause" to control

### For Your Friend:
1. Enter their name
2. Enter the room code you shared
3. Click "Join/Create Room"
4. Click "Start Camera & Mic"
5. They should see your video and you should see theirs!

## 🎥 Loading Videos

### Option 1: Direct Video URL
- Find a direct link to a video file (ends in .mp4, .webm, etc.)
- Paste it in the URL input box
- Click "Load URL"
- **Note**: YouTube links DON'T work!

### Option 2: Local File
- Click "Upload Video" button
- Select a video file from your computer
- **Note**: Only YOU can see local files. Your friend won't see it!

### Option 3: Host Video File (Recommended for both to see)
1. Put your video file in a `static` folder:
```bash
mkdir static
# Copy your video.mp4 to static folder
```

2. Update app.py to serve static files (add after imports):
```python
from flask import send_from_directory

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)
```

3. Use URL in app: `http://localhost:5000/static/video.mp4`

## 🌐 Making it Accessible Online

### Option 1: Ngrok (Easiest - Free)
```bash
# Install ngrok from https://ngrok.com/download
ngrok http 5000
```
Share the ngrok URL with your friend!

### Option 2: Port Forwarding
1. Forward port 5000 in your router settings
2. Share your public IP with friend
3. **Warning**: This exposes your computer to the internet!

### Option 3: Deploy to Cloud (Best for production)
- **Render** (Free tier): https://render.com
- **Railway**: https://railway.app
- **Heroku**: https://heroku.com
- **PythonAnywhere**: https://pythonanywhere.com

## 🔧 Troubleshooting

### Camera/Mic Not Working
- Allow browser permissions for camera/microphone
- Check if another app is using the camera
- Try a different browser (Chrome/Firefox recommended)

### Video Not Loading
- Make sure URL is a DIRECT video link (not YouTube)
- Check if URL ends in .mp4, .webm, .ogg
- Try a different video source

### Friend Can't Connect
- Make sure you're on the same network OR using ngrok
- Check firewall settings (allow port 5000)
- Make sure Flask server is running

### Video Not Syncing
- Both users must be in the same room
- Use "Sync Play/Pause" buttons (not the video player controls)
- Check console for errors (F12 in browser)

## 📚 Technical Details

### Features:
- ✅ Real-time video chat (WebRTC)
- ✅ Synchronized video playback
- ✅ Text chat
- ✅ Room-based system
- ✅ Play/Pause sync
- ✅ Multiple users support (extensible)

### Technologies:
- **Backend**: Flask + Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript
- **Real-time**: Socket.IO (WebSocket)
- **Video Chat**: WebRTC
- **STUN Server**: Google's public STUN servers

## 🎯 Next Steps / Improvements

1. **Better Video Hosting**: Set up AWS S3 or Google Cloud Storage
2. **User Authentication**: Add login system
3. **Better UI**: Improve design and responsiveness
4. **Screen Sharing**: Add screen share feature
5. **Multiple Participants**: Support for 3+ people
6. **Recording**: Record watch party sessions
7. **Playlists**: Create and share playlists
8. **Reactions**: Add emoji reactions during watching

## 🆘 Need Help?

Check browser console (F12) for errors and check the terminal running Flask for server errors.

Good luck with your Watch Party! 🎬🍿