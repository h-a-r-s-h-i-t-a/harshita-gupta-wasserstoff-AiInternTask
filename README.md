
# Wasserstoff AI Internship Task 2 - Dynamic PDF Processing Pipeline

This project is part of Wasserstoff AI Internship Task, aiming to create a robust pipeline for processing multiple PDF documents from a desktop folder. The pipeline extracts metadata,domain-specific summaries and keywords, which are then stored in a MongoDB database. The project is designed to handle varying PDF lengths efficiently, leveraging concurrency to maximize speed and performance.




## Features

- **Automatic PDF Detection:** Scans and detects multiple PDFs from a designated folder for batch processing.

- **Complexity-Based Library Selection:** Determines the complexity of each PDF document and selects the appropriate text extraction library accordingly, ensuring accurate and efficient extraction.

- **Text Extraction:** Extracts text from the PDFs using the chosen library based on document complexity.

- **Metadata Storage:** Stores relevant metadata (such as file information and document attributes) in a MongoDB database for future reference and efficient data management.

- **First-Level Text Preprocessing:** Prepares the extracted text for analysis through initial preprocessing tasks such as removing Tags, email, URLs and special characters.

- **Text Summarization:**

-- Performs second-level text processing using lemmatization, stopword and punctuation

-- Used CV and TF-IDF to score sentences.

-- Extracts the highest-scoring sentences to generate a summary.

-- The size of the summary is dynamically adjusted based on the word count of the extracted text (longer documents get more detailed summaries).

-- Summaries are generated from the original text without further advanced preprocessing (no lemmatization, stopword removal, or punctuation correction).

- **Keyword Extraction:**

-- Applies second-level text preprocessing, including lemmatization, stopword removal, and normalization.

-- Uses TF-IDF to rank and score individual words in the document.

-- A function determines the keyword list length and threshold for selecting top keywords based on the processed text’s word count.

- **MongoDB Integration:** Integrates the generated summaries and keywords into MongoDB using the inserted document IDs, ensuring efficient linkage between metadata and processed content, Summary and Keywords.

- **Final Function:** In this fn all the earlier functions are integrated to make a final fn to which only folder path is supplied and it performs all the remaining tasks.

- **Concurrency Support:** Optimized for handling large numbers of PDFs concurrently, ensuring fast processing times.

- **Custom Solutions:** Built with custom, non-reliant third-party solutions, focusing on innovation and scalability.

- **Requirements:** Using PyCharm created a requirements file with all the necessary libraries and their respective versions

- **Docker Containerization:** Runs within a Docker container for easy deployment.

- **Deployed on Vercel:** Application hosted and accessible via Vercel.



## Table of Contents

1. Technologies
2. Prerequisites
3. Installation
4. Project Architecture
5. Deployment
6. Contributing
## Technologies

### Programming Language: Python

### Libraries:

**PyPDF2:** For PDF handling.

**nltk:** For natural language processing 

**spacy:** For Preprocessing 

**scikit-learn:** For TF-IDF and CV, for word and sentence scoring

**MongoDB:** As the NoSQL database for storing results.

**Concurrency with ThreadPoolExecutor**

**Other Libraries from Requirement.txt**

### Docker: For containerization and easier deployment.

### Vercel: For hosting and deployment.


## Prerequisites

#### Before you begin, ensure you have met the following requirements:

- Python 3.x installed on your local machine.

- Docker installed and running.

- MongoDB set up via MongoDBAtlas.

- Vercel account for deployment.

- PyCharm for requirements file and docker Image creation
## Installation

Install my-project with npm

1. Clone the Repository
```bash
  git clone https://github.com/h-a-r-s-h-i-t-a/harshita-gupta-wasserstoff-AiInternTask.git

```
2. Navigate to the project directory:
```bash
cd harshita-gupta-wasserstoff-AiInternTask
```
3. Set up a virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate     # For Windows

```
4. Install required dependencies:
```bash
pip install -r requirements.txt
```
5. Set up Docker:
 - Ensure Docker is installed and running on your system.
 - Build the Docker image:
 ```bash
 docker build -t wasserstoff-pdf-pipeline .
```
- Run the Docker Container
```bash
docker run -p 8000:8000 wasserstoff-pdf-pipeline
```

6. MongoDB Setup:

- Ensure MongoDB is running locally or provide connection details in the configuration.

7. Deploy on Vercel:

- To deploy on Vercel, follow the Vercel deployment guide.
- Link your GitHub repository during the Vercel deployment process for continuous integration.
## Project Architecture

The project is built on modular principles to ensure scalability and maintainability.

- **PDF Handler:** Extracts text content from each PDF.
- **Summarization Module:** Processes the text to generate summaries based on PDF size.
- **Keyword Extraction:** Extracts relevant keywords using NLP techniques.
- **Database Handler:** Stores the processed data (summaries and keywords) into MongoDB.
- **Concurrency Manager:** Manages the concurrent processing of multiple PDF documents using Python's Concurrency module.
## Deployment

1. Docker Deployment:

To deploy using Docker, ensure Docker is installed and run the following commands:

```bash
docker build -t wasserstoff-pdf-pipeline .
docker run -d -p 8000:8000 wasserstoff-pdf-pipeline

```

2. Deploying on Vercel:

- Log into your Vercel account.

- In the Vercel dashboard, click "New Project" and import this GitHub repository.
- Follow the prompts to configure your deployment settings.
- Your app will be deployed at a yourproject.vercel.app URL.


## Contibuting

Contributions are welcome! Follow these steps to contribute:

1. Fork the project.

2. Create your feature branch 
```bash 
git checkout -b feature/new-feature
```

3. Commit your changes 
```bash 
git commit -m 'Add a new feature')
```

4. Push to the branch 
```bash  
git push origin feature/new-feature
```

5. Open a pull request.

## Vercel Deployed Link

[Visit Vercel](https://harshita-gupta-wasserstoff-ai-intern-task.vercel.app/)
