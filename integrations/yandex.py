import aiohttp

YANDEX_API_KEY = "906b116b-066c-4ca6-a4c1-a22789294684"  # Replace with your actual Yandex API key

async def get_address_from_coordinates(latitude, longitude):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": YANDEX_API_KEY,
        "geocode": f"{longitude},{latitude}",  # Yandex expects lon,lat format
        "format": "json",
        "lang": "ru_RU"  # Change to "uz_UZ" if needed
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()

            try:
                # Extract the full formatted location name
                location_name = (
                    data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"]
                    ["GeocoderMetaData"]["text"]
                )
                return location_name  # Return full name instead of separate parts

            except (KeyError, IndexError):
                return "Локация не найдена"  # Handle cases where no data is found
