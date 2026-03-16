# Setup

# Running the app 
1. Create a venv
```python3 -m venv env```
2. Activate env
```source env/bin/activate```
3. Install requirements
```pip install -r requirements.txt```
4. Get the secrets from Authenticator App, save as ```secrets.toml``` in ``.streamlit`` directory
4. Run the app
```streamlit run Tour_Results.py```

# To run against the test db
1. Change all references to of `textkey` to `textkeytest`

WHen adding a new tour year, remember to go to Automatic index settings in firebase and add a new index for collecionGroupAsc for tournamens and field major. 

// allembic db for connection to neon
alembic revision --autogenerate -m "initial schema"
alembic upgrade head

Change url in the alembic.ini file to connect to neon db for test db and production db.

# Deploy tasks using trigger.dev
1. Create a new task in trigger.dev
2. run the cli npx trigger.dev@latest dev to test
3. Add env variables
4. Deploy
5. npx trigger.dev@latest deploy