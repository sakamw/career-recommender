# CareerPathAI

A Django web app that helps people discover AI and tech career paths based on their skills, interests, and goals. Fill out a quick questionnaire, and get personalized career recommendations with detailed explanations.

## What it does

You answer some questions about your skills, interests, work style, and long-term goals. The app uses Google's GenAI (Gemini) to analyze your responses and suggest 3 career paths that match your profile. Each recommendation includes:

- Why this path fits you
- Benefits of pursuing it
- Employment opportunities and market outlook
- Related sub-careers you might also consider

There's also a recycle bin feature - deleted recommendations hang around for 30 days before being permanently removed, so you can restore them if you change your mind.

## Getting started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repo and navigate into it:

```bash
cd CareerPathAI
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your environment variables. Create a `.env` file in the `CareerPathAI` directory:

```env
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
DEBUG=True
ALLOWED_HOSTS=localhost 127.0.0.1
GENAI_API_KEY=your-google-genai-api-key
GENAI_MODEL=gemini-1.5-flash
```

You can get a GenAI API key from [Google AI Studio](https://makersuite.google.com/app/apikey). The app will still work without it, but you'll get basic rule-based recommendations instead of AI-generated ones.

5. Run migrations:

```bash
python manage.py migrate
```

6. Create a superuser (optional, for admin access):

```bash
python manage.py createsuperuser
```

7. Start the development server:

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser and you're good to go.

## Project structure

```
CareerPathAI/
├── CareerPathAI/          # Main project settings
│   ├── settings.py        # Django configuration
│   ├── urls.py            # Root URL routing
│   └── ...
├── recommender/           # Main app
│   ├── models.py          # Database models (UserProfile, Questionnaire, Recommendation)
│   ├── views.py           # View logic
│   ├── forms.py           # Form definitions
│   ├── ai.py              # GenAI integration and recommendation logic
│   ├── urls.py            # App URL routing
│   └── templates/         # HTML templates
├── templates/             # Base templates (base.html)
├── static/                 # Static files (CSS, JS, images)
│   ├── css/
│   └── js/
└── manage.py              # Django management script
```

## Features

- **User authentication**: Register, login, logout with Django's built-in auth
- **Questionnaire system**: Answer questions about skills, interests, strengths, work style, and goals
- **AI-powered recommendations**: Uses Google GenAI (Gemini) for intelligent career suggestions
- **Detailed insights**: Each recommendation explains why it fits, benefits, job market info, and related paths
- **Dashboard**: View all your recommendations in one place
- **Recycle bin**: Soft delete with 30-day retention and restore capability
- **Profile customization**: Add a headline and bio to personalize your profile

## How it works

When you submit a questionnaire, the app sends your responses to Google's GenAI API (if configured). The AI analyzes your profile and returns structured recommendations. If the API isn't available or fails, it falls back to a simple rule-based system that matches keywords in your skills and interests.

Recommendations are stored in the database and linked to your user account. You can view them on your dashboard, see detailed breakdowns, and manage them (delete/restore).

## Environment variables

| Variable        | Description                                 | Required | Default              |
| --------------- | ------------------------------------------- | -------- | -------------------- |
| `SECRET_KEY`    | Django secret key for cryptographic signing | Yes      | `dev-secret-key`     |
| `DEBUG`         | Enable debug mode                           | No       | `True`               |
| `ALLOWED_HOSTS` | Space-separated list of allowed hostnames   | No       | `*` (all hosts)      |
| `GENAI_API_KEY` | Google GenAI API key                        | No       | None (uses fallback) |
| `GENAI_MODEL`   | GenAI model to use                          | No       | `gemini-1.5-flash`   |

## Development notes

The app uses SQLite by default for development. For production, you'd want to switch to PostgreSQL or MySQL and update the database settings accordingly.

Static files are served from the `static/` directory during development. In production, run `python manage.py collectstatic` to gather them into `staticfiles/` for your web server to serve.

The recycle bin cleanup happens automatically when users visit the dashboard - items older than 30 days get permanently deleted. For a production setup, you might want to move this to a scheduled task (Celery, cron, etc.).

## Tech stack

- **Backend**: Django 6.0
- **Database**: SQLite (dev), easily switchable to PostgreSQL/MySQL
- **AI**: Google GenAI (Gemini) API
- **Frontend**: Bootstrap 5.3, custom CSS/JS
- **Environment**: python-dotenv for configuration
