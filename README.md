# Eat the Apple
A website for Real-Time Data Streaming and Processing WebSocket Application project, using Google Pub/Sub for cloud messaging service and Google BigQuery cloud database. This website is made as a future extension for AUForum as a potential feature update for the website to incorporate live-chatting with people who are online in the website.


For now, the website does not have a well-established design; same goes the AUForum as both are still under development. However, future updates regarding designs and features will be updated in the GitHub.

## Flow of the website:
User types message -> JavaScript (frontend) sends via WebSocket -> Flask-SocketIO (backend) receives it -> Pub/Sub publishes it to the cloud -> Pub/Sub subscriber receives it -> BigQuery stores it for analytics -> Flask-SocketIO broadcasts to all users -> Everyone sees the message
