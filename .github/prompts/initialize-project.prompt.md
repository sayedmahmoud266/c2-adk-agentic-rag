---
name: initialize-project
description: This prompt is used to initialize the project skeleton and core features
---

# Role
You are a highly skilled software engineer with expertise in project architecture and design. Your task is to create a solid foundation for a new software project by setting up the project structure, configuring essential tools, and implementing core features.

# Goal
The goal of this prompt is to establish a well-organized project skeleton that includes the necessary directories, configuration files, and initial codebase. This will enable the development team to efficiently build upon this foundation and accelerate the development process.

# Project Summary
This project is a simple chatbot web application that allows users to interact with an HR AI assistant. The AI should be able to answer questions that related to a set of data stored in a vector database. The data will be a collection of HR documents and standards. The chatbot will be accessible through a web interface, and it should provide accurate and helpful responses based on the information stored in the vector database.

# Business Requirements
## Landing Page
- The landing page should be a simple KYC form that collects the user's name, email address, department, and position. This information will be used to mimic a real-world scenario in which the HR AI assistant retrieves relevant information based on the user's profile from an Auth service or any identity provider.
- The form should have a submit button that, when clicked, will store the user's information in a session or a temporary storage mechanism for later use.
- After submitting the form, the user should be redirected to the chatbot interface.

## Chatbot Interface
- The chatbot interface should allow users to input their questions and receive responses from the HR AI assistant.
- The chatbot should be designed to provide accurate and helpful responses based on the information stored in the vector database.
- The interface should be user-friendly and visually appealing, with a clear distinction between user messages and AI responses.
- The chatbot should maintain a conversation history, allowing users to see previous interactions with the AI assistant.
- The chatbot should be responsive and work well on both desktop and mobile devices.
- The chatbot should have a loading indicator while the AI is processing the user's question to enhance user experience.
- The chatbot should stream responses from the AI assistant in real-time, allowing users to see the response as it is generated.
- The chatbot should handle edge cases gracefully, such as when the AI assistant is unable to provide a relevant response or when there are connectivity issues with the vector database.
- The chatbot should have an ability to clear the conversation history, allowing users to start a new conversation with the AI assistant if needed. In addition to that, the chatbot should have an option to delete all data related to the user, including the conversation history and any stored information in the session or temporary storage. This will ensure that users have control over their data and can maintain their privacy.


# Technical Requirements
- The project should be structured in a modular and scalable way, following best practices for software architecture and design patterns.
- The project should be implemented using the following libraries/technologies:
  - Chatbot UI: Chainlit
  - Vector Database: in-memory vector database (vectordb or FAISS)
  - Agent Manager: Google's ADK (Agent Development Kit)
  - AI Model: Litellm with the ability to connect to local or remote models, and support for streaming responses on any model (openai, anthropic, google, ollama, lmstudio, etc.)
- The project should have a cli command to build the vector database from a set of HR documents and standards (from an /assets directory). This command should take the path to the documents as input and populate the vector database with the relevant information (save it to /data directory).
- The project should have a cli command to start the web server for the chatbot interface. This command should initialize the necessary components and make the chatbot accessible through a web browser.
- the project should use environment variables to manage configuration settings, such as database connection details, API keys, and other sensitive information. This will enhance security and allow for easy configuration across different environments (development, staging, production).
- The project should include error handling and logging mechanisms to facilitate debugging and maintenance. This will help ensure that any issues that arise during development or in production can be quickly identified and resolved.

# Architectural Requirements
- The project should follow a layered architecture, with clear separation of concerns between the presentation layer (chatbot interface), the business logic layer (AI assistant and agent manager), and the data access layer (vector database).
- The project should be designed to be an agentic RAG (Retrieval-Augmented Generation) system, where the AI assistant can retrieve relevant information from the vector database to generate accurate and helpful responses to user queries.
- flow of the system should be as follows:
  1. User submits the KYC form on the landing page, and their information is stored in a session or temporary storage.
  2. User is redirected to the chatbot interface, where they can input their questions.
  3. The chatbot interface sends the user's question along with their profile information to the AI assistant.
  4. The AI assistant uses the user's profile information to query the vector database for relevant information.
  5. The AI assistant generates a response based on the retrieved information and sends it back to the chatbot interface.
  6. The chatbot interface displays the AI assistant's response to the user, maintaining a conversation history for reference.