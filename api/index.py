from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import csv
from io import StringIO
from datetime import datetime
from dateutil import parser as date_parser
import logging
from prisma import Prisma
from datetime import datetime

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/api/scrape-eudract")
async def scrape_clinical_trials():
    db = Prisma()
    await db.connect()
    
    try:
        URL = "https://www.clinicaltrialsregister.eu/ctr-search/search?query="
        response = requests.get(URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        trials_data = []
        trial_elements = soup.find_all("table", class_="result")

        for trial_element in trial_elements:
            trial_data = {}

            def get_next_text(label_text):
                label = trial_element.find("span", class_="label", text=lambda t: t and label_text in t)
                if label:
                    return label.find_parent().text.replace(label_text, '').strip()
                return None

            def get_start_date():
                start_date_label = trial_element.find("span", class_="startdatetip")
                if start_date_label:
                    start_date_parent = start_date_label.find_parent().find_parent()
                    if start_date_parent:
                        full_text = start_date_parent.text.strip()
                        start_date = full_text.split(":")[-1].strip()
                        return datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
                return None

            trial_data["eudract_number"] = get_next_text("EudraCT Number:")
            trial_data["sponsor_protocol"] = get_next_text("Sponsor Protocol Number:")
            trial_data["start_date"] = get_start_date()
            trial_data["sponsor_name"] = get_next_text("Sponsor Name:")
            trial_data["full_title"] = get_next_text("Full Title:")
            trial_data["medical_condition"] = get_next_text("Medical condition:")
            trial_data["population_age"] = get_next_text("Population Age:")
            trial_data["gender"] = get_next_text("Gender:")

            if not trial_data["eudract_number"]:
                logger.warning("Skipping trial due to missing EudraCT Number")
                continue

            trials_data.append(trial_data)
            
        # Clear existing data
        await db.eudract.delete_many()

        # Insert new data
        for trial in trials_data:
            await db.eudract.create(data=trial)

        return {"trials": trials_data}

    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching clinical trials data.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.get("/api/eudract")
async def get_eudract_trials():
    db = Prisma()
    await db.connect()
    
    try:
        trials = await db.eudract.find_many()
        return {"trials": trials}
    except Exception as e:
        logger.error(f"Error fetching EudraCT trials: {e}")
        raise HTTPException(status_code=500, detail="Error fetching EudraCT trials.")

def parse_date(date_str):
    if date_str:
        try:
            return date_parser.parse(date_str)
        except ValueError as e:
            logger.error(f"Date parsing error: {e} for date_str: {date_str}")
            return None
    return None

def check_field_lengths(trial):
    max_lengths = {
        'nct_number': 50,
        'acronym': 100,
        'status': 50,
        'gender': 20,
        'age': 50,
        'phases': 50,
        'study_type': 50,
        'other_ids': 50,
        'title': 255,  # Update this if necessary
        'study_results': 255,  # Update this if necessary
        'conditions': 255,  # Update this if necessary
        'interventions': 255,  # Update this if necessary
        'outcome_measures': 255,  # Update this if necessary
        'sponsor_collaborators': 255,  # Update this if necessary
        'funded_bys': 255,  # Update this if necessary
        'study_designs': 255,  # Update this if necessary
        'locations': 255,  # Update this if necessary
        'study_documents': 255,  # Update this if necessary
        'url': 255  # Update this if necessary
    }

    for field, max_length in max_lengths.items():
        value = trial.get(field)
        if value and len(value) > max_length:
            logger.error(f"Value too long for field '{field}': {value} (length: {len(value)})")

@app.get("/api/download-clinical-trials-gov")
async def download_csv():
    db = Prisma()
    await db.connect()

    try:
        CSV_URL = "https://clinicaltrials.gov/ct2/results/download_fields?down_count=10&down_flds=all&down_fmt=csv&flds=a&flds=b&flds=y"
        response = requests.get(CSV_URL)
        response.raise_for_status()

        csv_data = response.content.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))

        trials_data = []
        for row in csv_reader:
            trial = {
                'rank': int(row['Rank']) if row['Rank'].isdigit() else None,
                'nct_number': row['NCT Number'],
                'title': row['Title'],
                'acronym': row['Acronym'],
                'status': row['Status'],
                'study_results': row['Study Results'],
                'conditions': row['Conditions'],
                'interventions': row['Interventions'],
                'outcome_measures': row['Outcome Measures'],
                'sponsor_collaborators': row['Sponsor/Collaborators'],
                'gender': row['Gender'],
                'age': row['Age'],
                'phases': row['Phases'],
                'enrollment': int(row['Enrollment']) if row['Enrollment'].isdigit() else None,
                'funded_bys': row['Funded Bys'],
                'study_type': row['Study Type'],
                'study_designs': row['Study Designs'],
                'other_ids': row['Other IDs'],
                'start_date': parse_date(row['Start Date']),
                'primary_completion_date': parse_date(row['Primary Completion Date']),
                'completion_date': parse_date(row['Completion Date']),
                'first_posted': parse_date(row['First Posted']),
                'results_first_posted': parse_date(row['Results First Posted']),
                'last_update_posted': parse_date(row['Last Update Posted']),
                'locations': row['Locations'],
                'study_documents': row['Study Documents'],
                'url': row['URL']
            }
            check_field_lengths(trial)
            trials_data.append(trial)
            
        print(trials_data)

        # Clear existing data
        await db.clinicaltrials.delete_many()

        # Insert new data
        for trial in trials_data:
            await db.clinicaltrials.create(data=trial)

        return {"trials": trials_data}

    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail="Error downloading clinical trials CSV.")
    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        raise HTTPException(status_code=500, detail="Error parsing CSV data.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.get("/api/clinicaltrials")
async def get_clinical_trials():
    db = Prisma()
    await db.connect()
    
    try:
        trials = await db.clinicaltrials.find_many()
        return {"trials": trials}
    except Exception as e:
        logger.error(f"Error fetching ClinicalTrials.gov trials: {e}")
        raise HTTPException(status_code=500, detail="Error fetching ClinicalTrials.gov trials.")
    
@app.get("/api/trialsbysponsor")
async def get_trials_by_sponsor():
    db = Prisma()
    await db.connect()
    
    try:
        trials = await db.query_raw('''
            SELECT sponsor, COUNT(*) as count
            FROM (
                SELECT unnest(string_to_array(sponsor_collaborators, '|')) AS sponsor
                FROM clinicaltrials
            ) AS sponsors
            GROUP BY sponsor
        ''')
        return {"trials_by_sponsor": trials}
    except Exception as e:
        logger.error(f"Error fetching trials by sponsor: {e}")
        raise HTTPException(status_code=500, detail="Error fetching trials by sponsor.")
    finally:
        await db.disconnect()

@app.get("/api/trialsbycondition")
async def get_trials_by_condition():
    db = Prisma()
    await db.connect()
    
    try:
        trials = await db.query_raw('''
            SELECT condition, COUNT(*) as count
            FROM (
                SELECT unnest(string_to_array(conditions, '|')) AS condition
                FROM clinicaltrials
            ) AS conditions
            GROUP BY condition
        ''')
        return {"trials_by_condition": trials}
    except Exception as e:
        logger.error(f"Error fetching trials by condition: {e}")
        raise HTTPException(status_code=500, detail="Error fetching trials by condition.")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
