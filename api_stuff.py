import requests
from dotenv import load_dotenv
import os
load_dotenv()

async def get_nasa_apod() -> dict:
	api_key = os.getenv("NASA_API_KEY")

	url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch data from NASA API: {response.status_code}")

	return response.json()

async def get_dog_pic() -> str:
	url = "https://dog.ceo/api/breeds/image/random"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch dog picture: {response.status_code}")

	data = response.json()
	if 'message' not in data:
		raise ValueError("Unexpected response format from dog API")

	return data['message']

async def get_fox_pic() -> str:
	url = "https://randomfox.ca/floof/"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch fox picture: {response.status_code}")

	data = response.json()
	if 'image' not in data:
		raise ValueError("Unexpected response format from fox API")

	return data['image']

async def get_cat_pic() -> str:
	url = "https://api.thecatapi.com/v1/images/search"

	header = {'x-api-key':os.getenv("CAT_API_KEY"), 'Content-Type': 'application/json'}
	response = requests.get(url, headers=header)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch cat picture: {response.status_code}")

	data = response.json()
	if not data or 'url' not in data[0]:
		raise ValueError("Unexpected response format from cat API")

	return data[0]['url']

async def get_insult() -> str:
	url = "https://evilinsult.com/generate_insult.php?lang=en&type=json"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch insult: {response.status_code}")

	data = response.json()
	if 'insult' not in data:
		raise ValueError("Unexpected response format from insult API")

	return data['insult']

async def get_advice() -> str:
	url = "https://api.adviceslip.com/advice"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch advice: {response.status_code}")

	data = response.json()
	if 'slip' not in data or 'advice' not in data['slip']:
		raise ValueError("Unexpected response format from advice API")

	return data['slip']['advice']
