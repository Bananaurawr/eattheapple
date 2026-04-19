# Eat the Apple
A website for Real-Time Data Streaming and Processing WebSocket Application project, using Google Pub/Sub for cloud messaging service and Google BigQuery cloud database for analytics

## Flow of the website:
User types message
       ↓
JavaScript (frontend) sends via WebSocket
       ↓
Flask-SocketIO (backend) receives it
       ↓
Pub/Sub publishes it to the cloud
       ↓
Pub/Sub subscriber receives it
       ↓
BigQuery stores it for analytics
Flask-SocketIO broadcasts to all users
       ↓
Everyone sees the message
