import requests
from dotenv import load_dotenv
import os
load_dotenv()

def get_nasa_apod() -> dict[str, str]:
	api_key = os.getenv("NASA_API_KEY")

	url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch data from NASA API: {response.status_code}")

	return response.json()

def get_dog_pic() -> str:
	url = "https://dog.ceo/api/breeds/image/random"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch dog picture: {response.status_code}")

	data = response.json()
	if 'message' not in data:
		raise ValueError("Unexpected response format from dog API")

	return data['message']

def get_fox_pic() -> str:
	url = "https://randomfox.ca/floof/"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch fox picture: {response.status_code}")

	data = response.json()
	if 'image' not in data:
		raise ValueError("Unexpected response format from fox API")

	return data['image']

def get_cat_pic() -> str:
	url = "https://api.thecatapi.com/v1/images/search"

	header = {'x-api-key':os.getenv("CAT_API_KEY"), 'Content-Type': 'application/json'}
	response = requests.get(url, headers=header)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch cat picture: {response.status_code}")

	data = response.json()
	if not data or 'url' not in data[0]:
		raise ValueError("Unexpected response format from cat API")

	return data[0]['url']

def get_insult() -> str:
	url = "https://evilinsult.com/generate_insult.php?lang=en&type=json"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch insult: {response.status_code}")

	data = response.json()
	if 'insult' not in data:
		raise ValueError("Unexpected response format from insult API")

	return data['insult']

def get_advice() -> str:
	url = "https://api.adviceslip.com/advice"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch advice: {response.status_code}")

	data = response.json()
	if 'slip' not in data or 'advice' not in data['slip']:
		raise ValueError("Unexpected response format from advice API")

	return data['slip']['advice']

def get_joke() -> str:
	url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=racist,sexist"
	response = requests.get(url)

	if response.status_code != 200:
		raise Exception(f"Failed to fetch joke: {response.status_code}")

	data = response.json()
	if 'joke' not in data and ('setup' not in data or 'delivery' not in data):
		raise ValueError("Unexpected response format from joke API")

	if 'joke' in data:
		# Single joke format
		return data['joke']

	# Two-part joke format
	if 'setup' in data and 'delivery' in data:
		return f"{data['setup']}\n{data['delivery']}"
	else:
		raise ValueError("Unexpected joke format from joke API")