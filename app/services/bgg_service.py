import requests
import xml.etree.ElementTree as ET

BGG_API_URL = "https://boardgamegeek.com/xmlapi"

async def fetch_bgg_thing_raw(game_id: int):
    """BGG API에서 원본 XML 데이터를 반환"""
    url = f"{BGG_API_URL}2/thing?id={game_id}&stats=1"
    response = requests.get(url)
    return response.text  # 원본 XML 그대로 반환

async def fetch_bgg_game_raw(game_id: int):
    """BGG API에서 원본 XML 데이터를 반환"""
    url = f"{BGG_API_URL}/boardgame/{game_id}"
    response = requests.get(url)
    return response.text  # 원본 XML 그대로 반환

async def fetch_bgg_game(game_id: int):
    """BGG API에서 보드게임 정보를 파싱해서 반환 (모든 태그 포함)"""
    raw_xml = await fetch_bgg_thing_raw(game_id)
    #raw_xml = await fetch_bgg_game_raw(game_id)
    return get_desired_tags(raw_xml)
    #return get_all_tags(raw_xml)
    root = ET.fromstring(raw_xml)

    def parse_element(element):
        """재귀적으로 XML 요소를 파싱하여 딕셔너리로 변환"""
        parsed = {f"@{k}": v for k, v in element.attrib.items()}  # 속성 파싱
        if element.text and element.text.strip():
            parsed["#text"] = element.text.strip()  # 태그 내 텍스트 값 저장

        children = [parse_element(child) for child in element]  # 자식 요소 파싱
        if children:
            parsed["children"] = children

        return {element.tag: parsed}  # 태그명 포함한 딕셔너리 반환

    parsed_data = parse_element(root)  # XML 전체를 파싱

    return {"id": game_id, "parsed_data": parsed_data, "raw_xml": raw_xml}


def get_all_tags(xml_string):
    root = ET.fromstring(xml_string)
    tags = set()  # 중복 제거를 위한 set 사용

    def traverse(element):
        tags.add(element.tag)  # 현재 태그 저장
        for child in element:
            traverse(child)  # 재귀적으로 탐색

    traverse(root)
    return tags

# desired_tags = [
#     "minplaytime", "boardgamedesigner", "boardgamecategory",
#     "poll-summary", "playingtime", "age",
#     "minplayers", "maxplaytime", "boardgamemechanic", "name", "image",
#     "maxplayers", "thumbnail"
# ]

desired_tags = [
    "item",
    "poll-summary",
    "usersrated",
    "median",
    "rank",
    "minplayers",
    "owned",
    "maxplaytime",
    "minplaytime",
    "thumbnail",
    "playingtime",
    "ratings",
    "link",
    "wanting",
    "maxplayers",
    "average",
    "stddev",
    "minage",
    "results",
    "name",
    "result",
    "statistics",
    "items",
    "poll",
    "trading",
    "image",
    "description",
    "wishing",
    "ranks",
    "bayesaverage",
    "yearpublished",
    "numweights",
    "numcomments",
    "averageweight"
  ]

def get_desired_tags(xml_string):
    root = ET.fromstring(xml_string)
    filtered_elements = {}

    def traverse(element):
        # 태그가 여러 번 나올 수 있는 경우 리스트로 저장
        if element.tag in desired_tags:
            if element.tag not in filtered_elements:
                filtered_elements[element.tag] = []
            filtered_elements[element.tag].append(element.text)  # 모든 값을 리스트에 추가

        # poll-summary와 같은 하위 구조가 있는 경우 하위 태그는 무시
        if element.tag != "poll-summary":
            for child in element:
                traverse(child)  # 재귀적으로 탐색

    traverse(root)
    return filtered_elements
# def get_desired_tags(xml_string):
#     root = ET.fromstring(xml_string)
#     filtered_elements = {}

#     def traverse(element):
#         # 태그가 여러 번 나올 수 있는 경우 리스트로 저장
#         if element.tag in desired_tags:
#             if element.tag not in filtered_elements:
#                 filtered_elements[element.tag] = []
#             filtered_elements[element.tag].append(element.text if element.tag != "poll-summary" else None)

#         # poll-summary와 같은 하위 구조가 있는 경우, 하위 내용까지 추출
#         if element.tag == "poll-summary":
#             poll_data = {"@name": element.attrib.get("name"), "@title": element.attrib.get("title"), "children": []}
#             for child in element:
#                 if child.tag == "result":
#                     result_data = {"@name": child.attrib.get("name"), "@value": child.attrib.get("value")}
#                     poll_data["children"].append(result_data)
#             filtered_elements["poll-summary"] = poll_data

#         # 다른 태그들에 대해서는 재귀적으로 탐색
#         for child in element:
#             traverse(child)

#     traverse(root)
#     return filtered_elements


# [
#   "results",
#   "boardgamepodcastepisode",
#   "result",
#   "boardgames",
#   "minplaytime",
#   "description",
#   "boardgamedesigner",
#   "boardgamepublisher",
#   "boardgamecategory",
#   "yearpublished",
#   "videogamebg",
#   "poll-summary",
#   "boardgamehonor",
#   "boardgameimplementation",
#   "playingtime",
#   "age",
#   "boardgameversion",
#   "boardgameartist",
#   "boardgamesubdomain",
#   "boardgamefamily",
#   "minplayers",
#   "maxplaytime",
#   "boardgameaccessory",
#   "boardgamemechanic",
#   "poll",
#   "name",
#   "image",
#   "maxplayers",
#   "cardset",
#   "thumbnail",
#   "boardgame"
# ]

# [
#   "minplaytime",
#   "description",
#   "boardgamedesigner",
#   "boardgamecategory",
#   "poll-summary",
#   "playingtime",
#   "age",
#   "boardgameartist",
#   "boardgamefamily",
#   "minplayers",
#   "maxplaytime",
#   "boardgamemechanic",
#   "name",
#   "image",
#   "maxplayers",
#   "thumbnail",
#   "boardgame"
# ]
