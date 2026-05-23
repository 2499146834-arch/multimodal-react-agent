import os
import json
import ssl
import urllib.request
from PIL import Image, ImageDraw

SAVE_DIR = r"D:\Multimodal Project\multimodal_agent\data\images"
QUESTIONS_FILE = r"D:\Multimodal Project\multimodal_agent\data\sample_questions.json"

ssl._create_default_https_context = ssl._create_unverified_context

BASE = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def _download(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as f:
            with open(path, "wb") as out:
                out.write(f.read())
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def _create_placeholder(path, texts, color="white"):
    img = Image.new("RGB", (640, 480), color=color)
    draw = ImageDraw.Draw(img)
    for i, txt in enumerate(texts):
        draw.text((50, 50 + i * 60), txt, fill="black")
    img.save(path)


def _create_scene(path, objects):
    colors = {"person": "red", "car": "blue", "dog": "brown", "cat": "orange",
              "bicycle": "green", "bird": "yellow", "chair": "purple", "table": "gray"}
    img = Image.new("RGB", (640, 480), color="white")
    draw = ImageDraw.Draw(img)
    for i, obj in enumerate(objects):
        c = colors.get(obj, "black")
        x = 100 + (i % 3) * 180
        y = 80 + (i // 3) * 150
        draw.rectangle([x, y, x + 120, y + 80], fill=c, outline="black")
        draw.text((x + 10, y + 30), obj, fill="white")
    img.save(path)


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    questions = []
    success_count = 0

    # === OCR images (3): images with English text ===
    ocr_images = [
        {
            "filename": "ocr_sign.jpg",
            "urls": [
                BASE + "Hollywood_Sign_(Zuschnitt).jpg?width=640",
            ],
            "question": "What text is written in this image? Extract and read all visible text.",
            "expected_tools": ["ocr"],
            "texts": ["HOLLYWOOD SIGN", "LANDMARK TEXT", "CALIFORNIA"],
        },
        {
            "filename": "ocr_notice.jpg",
            "urls": [
                BASE + "COVID-19_vaccination_sign_at_Walmart.jpg?width=640",
                BASE + "2020-12-09_13_35_03_Read_the_sign_in_the_parking_lot_of_the_Dulles_Town_Center_in_Sterling%2C_Loudoun_County%2C_Virginia.jpg?width=640",
            ],
            "question": "Please read and transcribe all the text visible in this image.",
            "expected_tools": ["ocr"],
            "texts": ["NOTICE BOARD", "IMPORTANT", "PLEASE READ"],
        },
        {
            "filename": "ocr_label.jpg",
            "urls": [
                BASE + "US_Nutrition_Facts_Label.png?width=640",
                BASE + "Welcome_to_Las_Vegas_sign.jpg?width=640",
            ],
            "question": "Extract all text content from this image using OCR.",
            "expected_tools": ["ocr"],
            "texts": ["NUTRITION FACTS", "INGREDIENTS", "SERVING SIZE"],
        },
    ]

    # === Detection images (4): images with multiple objects ===
    detect_images = [
        {
            "filename": "detect_street.jpg",
            "urls": [
                BASE + "Manhattan_at_Dusk_by_slonecker.jpg?width=640",
                BASE + "New_York_Street_Scene_MET_1983.86.1.jpg?width=640",
            ],
            "question": "What objects can you detect in this street scene?",
            "expected_tools": ["detect"],
            "objects": ["person", "car", "truck"],
        },
        {
            "filename": "detect_park.jpg",
            "urls": [
                BASE + "Sunny_day_in_Green_Park_-_geograph.org.uk_-_7177752.jpg?width=640",
                BASE + "Sunny_Seat_in_Sutro_Park_(1993405221).jpg?width=640",
            ],
            "question": "List all detectable objects in this park image.",
            "expected_tools": ["detect"],
            "objects": ["person", "bench", "dog"],
        },
        {
            "filename": "detect_room.jpg",
            "urls": [
                BASE + "Living_room_furniture_(Unsplash).jpg?width=640",
                BASE + "Sankheda_furniture_in_a_living_room_setting.jpg?width=640",
            ],
            "question": "Detect and name all objects visible in this room.",
            "expected_tools": ["detect"],
            "objects": ["chair", "table", "couch"],
        },
        {
            "filename": "detect_animals.jpg",
            "urls": [
                BASE + "Cat_and_dog_sleeping_together.jpeg?width=640",
                BASE + "Cat_November_2010-1a.jpg?width=640",
            ],
            "question": "What animals or objects can you find in this image?",
            "expected_tools": ["detect"],
            "objects": ["cat", "dog", "bird"],
        },
    ]

    # === Search images (3): need background knowledge ===
    search_images = [
        {
            "filename": "search_landmark.jpg",
            "urls": [
                BASE + "Tour_Eiffel_Wikimedia_Commons.jpg?width=640",
            ],
            "question": "Identify this landmark and provide key facts about its history and significance.",
            "expected_tools": ["search", "vlm"],
            "objects": [],
            "texts": [],
        },
        {
            "filename": "search_monument.jpg",
            "urls": [
                BASE + "Colosseo_2020.jpg?width=640",
            ],
            "question": "What is this ancient structure? Provide historical context and interesting facts.",
            "expected_tools": ["search", "vlm"],
            "objects": [],
            "texts": [],
        },
        {
            "filename": "search_animal.jpg",
            "urls": [
                BASE + "Giant_Panda_2004-03-2.jpg?width=640",
            ],
            "question": "What species is this animal? Tell me about its habitat and conservation status.",
            "expected_tools": ["search", "vlm"],
            "objects": [],
            "texts": [],
        },
    ]

    all_specs = ocr_images + detect_images + search_images

    for spec in all_specs:
        path = os.path.join(SAVE_DIR, spec["filename"])
        downloaded = False
        for url in spec.get("urls", []):
            if _download(url, path):
                print(f"  Downloaded: {spec['filename']}")
                downloaded = True
                break

        if not downloaded:
            if spec["expected_tools"][0] == "ocr":
                _create_placeholder(path, spec.get("texts", ["PLACEHOLDER TEXT"]))
            elif spec["expected_tools"][0] == "detect":
                _create_scene(path, spec.get("objects", ["person", "car"]))
            else:
                _create_placeholder(path, ["PLACEHOLDER IMAGE", spec["filename"]])
            print(f"  Created placeholder for {spec['filename']}")
        else:
            success_count += 1

        questions.append({
            "image_path": f"data/images/{spec['filename']}",
            "question": spec["question"],
            "expected_tools": spec["expected_tools"],
        })

    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"\nDownloaded successfully: {success_count}/{len(all_specs)}")
    print(f"Placeholder images created: {len(all_specs) - success_count}")
    print(f"Questions saved to: {QUESTIONS_FILE}")


if __name__ == "__main__":
    main()
