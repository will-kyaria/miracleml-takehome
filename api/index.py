from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import csv
from io import StringIO
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/api/scrape-eudract")
def scrape_clinical_trials():
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
                        return start_date
                return None

            trial_data["EudraCT Number"] = get_next_text("EudraCT Number:")
            trial_data["Sponsor Protocol Number"] = get_next_text("Sponsor Protocol Number:")
            trial_data["Start Date"] = get_start_date()
            trial_data["Sponsor Name"] = get_next_text("Sponsor Name:")
            trial_data["Full Title"] = get_next_text("Full Title:")
            trial_data["Medical Condition"] = get_next_text("Medical condition:")
            trial_data["Population Age"] = get_next_text("Population Age:")
            trial_data["Gender"] = get_next_text("Gender:")

            trials_data.append(trial_data)

        return {"trials": trials_data}

    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching clinical trials data.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.get("/api/download-clinical-trials-gov")
def download_csv():
    try:
        CSV_URL = "https://clinicaltrials.gov/ct2/results/download_fields?down_count=10&down_flds=all&down_fmt=csv&flds=a&flds=b&flds=y"
        response = requests.get(CSV_URL)
        response.raise_for_status()

        csv_data = response.content.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))

        trials_data = []
        for row in csv_reader:
            trials_data.append(row)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
