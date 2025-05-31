import requests
from dotenv import load_dotenv
import os
load_dotenv()

async def get_nasa_apod() -> dict:
	api_key = os.getenv("NASA_API_KEY")
	if not api_key:
		raise ValueError("NASA API key is not set in the environment variables.")

	url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch data from NASA API: {response.status_code}")

	return response.json()