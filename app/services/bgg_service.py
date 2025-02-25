import requests
import xml.etree.ElementTree as ET

BGG_API_URL = "https://boardgamegeek.com/xmlapi2"

async def fetch_bgg_game_raw(game_id: int):
    """BGG API에서 원본 XML 데이터를 반환"""
    url = f"{BGG_API_URL}/thing?id={game_id}"
    response = requests.get(url)
    return response.text  # 원본 XML 그대로 반환

async def fetch_bgg_game(game_id: int):
    """BGG API에서 보드게임 정보를 파싱해서 반환"""
    raw_xml = await fetch_bgg_game_raw(game_id)
    root = ET.fromstring(raw_xml)

    name_element = root.find(".//name[@type='primary']")
    name = name_element.attrib["value"] if name_element is not None else "Unknown"

    description_element = root.find(".//description")
    description = description_element.text if description_element is not None else "No description available"

    return {"id": game_id, "name": name, "description": description, "raw_xml": raw_xml}
