import requests
import xml.etree.ElementTree as ET
import re
from collections import defaultdict

BGG_API_URL = "https://boardgamegeek.com/xmlapi"

async def fetch_bgg_thing(game_id: int):
    """BGG API에서 원본 XML 데이터를 JSON으로 변환하여 반환"""
    raw_xml = await fetch_bgg_thing_raw(game_id)
    json_data = xml_to_json(raw_xml)
    return parse_game_data(json_data)

async def fetch_bgg_thing_raw(game_id: int):
    """BGG API에서 원본 XML 데이터를 반환"""
    url = f"{BGG_API_URL}2/thing?id={game_id}&stats=1"
    response = requests.get(url)
    return response.text  # 원본 XML 그대로 반환

def parse_xml(raw_xml):
    """XML을 JSON으로 변환하는 함수"""
    return xml_to_json(raw_xml)

def xml_to_json(xml_string):
    """XML 문자열을 JSON 객체로 변환하는 함수"""
    root = ET.fromstring(xml_string)

    def parse_element(element):
        """재귀적으로 XML 요소를 파싱하여 JSON 딕셔너리로 변환"""
        parsed = {f"@{k}": v for k, v in element.attrib.items()}  # 속성 저장

        # 텍스트 값이 있으면 저장
        if element.text and element.text.strip():
            parsed["#text"] = element.text.strip()

        # 자식 요소 처리
        children = {}
        for child in element:
            child_data = parse_element(child)
            if child.tag in children:
                if isinstance(children[child.tag], list):
                    children[child.tag].append(child_data)
                else:
                    children[child.tag] = [children[child.tag], child_data]
            else:
                children[child.tag] = child_data

        # 자식 요소가 있다면 추가
        if children:
            parsed.update(children)

        return parsed

    return parse_element(root)  # **딕셔너리 반환 (JSON 객체)**

def parse_game_data(data):
    item = data.get("item", {})
    
    # 이름 처리 (리스트인지 문자열인지 구분)
    names = item.get("name", [])
    if isinstance(names, list):
        names = [name["@value"] for name in names if isinstance(name, dict) and "@value" in name]
    else:
        names = [names]  # 이름이 문자열일 경우 리스트로 감싸서 처리
    
    parsed_data = {
        "thumbnail": item.get("thumbnail", {}).get("#text", None),
        "image": item.get("image", {}).get("#text", None),
        "name": names,  # 위에서 처리한 names 추가
        "minplayers": item.get("minplayers", {}).get("@value", None),
        "maxplayers": item.get("maxplayers", {}).get("@value", None),
        "suggested_playerage": item.get("suggested_playerage", None),  # 추후 추가될 데이터
        "suggested_numplayers": get_suggested_numplayers(item.get("poll-summary", {})),
        "playingtime": item.get("playingtime", {}).get("@value", None),
        "minplaytime": item.get("minplaytime", {}).get("@value", None),
        "maxplaytime": item.get("maxplaytime", {}).get("@value", None),
        "minage": item.get("minage", {}).get("@value", None),
        "link": filter_links(item.get("link", [])),  # 기본값 빈 리스트 추가
        "ratings": item.get("statistics", {}).get("ratings", {}).get("average", {}).get("@value", None),
        "weight": item.get("statistics", {}).get("ratings", {}).get("averageweight", {}).get("@value", None)
    }
    
    return parsed_data


def get_suggested_numplayers(poll_summary):
    """poll-summary에서 suggested_numplayers에 해당하는 값 추출 후 숫자만 리스트로 반환"""
    suggested_numplayers = {}
    
    if poll_summary.get("@name") == "suggested_numplayers":
        for result in poll_summary.get("result", []):
            name = result.get("@name")
            value = result.get("@value", "")

            # 0~9 숫자만 추출하여 리스트로 변환
            numbers = [int(n) for n in re.findall(r"\d+", value)]

            if name == "bestwith":
                suggested_numplayers["bestwith"] = numbers
            elif name == "recommmendedwith":
                suggested_numplayers["recommendedwith"] = numbers

    return suggested_numplayers

def filter_links(links):
    """boardgamecategory, boardgamemechanic, boardgamedesigner만 추출하여 value 값 리스트 반환"""
    allowed_types = {"boardgamecategory", "boardgamemechanic", "boardgamedesigner"}
    filtered_links = defaultdict(list)

    for link in links:
        link_type = link.get("@type")
        link_value = link.get("@value")

        if link_type in allowed_types and link_value:
            filtered_links[link_type].append(link_value)

    return dict(filtered_links)

