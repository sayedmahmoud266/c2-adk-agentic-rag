---
description: General Instructions to be used in the entire project
applyTo: **/*
---
- Always document the updated version of the code in a clean and concise manner inside a set of markdown files in a /docs folder in the root of the project. The documentation should be organized in a way that makes it easy for developers to find the information they need.
- always keep the README.md file up to date with the latest changes and instructions for using the project. The README should provide clear and concise information about the project, including its purpose, features, installation instructions, and usage guidelines. all of that while being simple and not too long.
- Always write clean, readable, and maintainable code. Follow best practices for coding style, including consistent indentation, meaningful variable names, and clear comments where necessary. Avoid writing complex and convoluted code that is difficult to understand and maintain.
- Always create unit tests to test the functionality of the code. Unit tests should be comprehensive and cover all possible scenarios, including edge cases and error handling. Use a testing framework that is appropriate for the programming language being used.
- use a .env file to manage environment variables and sensitive information. The .env file should be included in the .gitignore file to prevent it from being committed to version control. Use a library like dotenv to load the environment variables from the .env file into the application.
- include .env.example file in the root of the project that contains the structure of the .env file and the required environment variables for the project. This will help developers to understand what environment variables are needed and how to set them up.
- use venv to manage dependencies and create a virtual environment for the project. This will help to ensure that the project has a consistent and isolated environment for development and deployment. Use a tool like pip to install the required dependencies in the virtual environment.
- use a requirements.txt file to manage the dependencies for the project. The requirements.txt file should list all the required dependencies for the project, along with their versions. Use pip to install the dependencies from the requirements.txt file.
- use a makefile to automate common tasks such as building, testing, and deploying the project. The makefile should include targets for each of these tasks, along with any necessary dependencies and commands. Use a tool like Make to execute the targets in the makefile.
