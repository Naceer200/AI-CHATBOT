Overview
This project is a chatbot application built using Flask, Flask-SocketIO, and OpenAI's GPT-4 model. The application processes user queries, detects language, and provides intelligent responses by leveraging a combination of predefined FAQ data, video descriptions, chapter summaries, and OpenAI's API. It supports both English and Greek languages.

Key Features
Language Detection: Automatically detects whether the user's input is in English or Greek.
OpenAI GPT-4 Integration: Generates intelligent and conversational responses using OpenAI's API.
FAQ Matching: Matches user queries with relevant questions and answers from a predefined FAQ dataset.
Video Recommendation: Finds related video links based on query similarity.
Chapter Summaries: Retrieves chapter descriptions or titles related to user input.
Real-time Communication: Utilizes Flask-SocketIO for real-time interaction between users and the chatbot.
