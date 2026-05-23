import json
import os
import ssl
import random
import urllib.request
import time

ssl._create_default_https_context = ssl._create_unverified_context

ANNOTATIONS_URL = "https://dl.fbaipublicfiles.com/textvqa/data/TextVQA_0.5.1_val.json"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
IMAGE_DIR = os.path.join(DATA_DIR, "textvqa_images")
OUTPUT_FILE = os.path.join(DATA_DIR, "textvqa_200.json")
TARGET_COUNT = 200
MAX_QUESTION_LEN = 50


def _try_download(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as f:
            return f.read()
    except Exception:
        return None


def main():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    random.seed(42)

    # Download annotations
    print(f"Downloading annotations...")
    req = urllib.request.Request(ANNOTATIONS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as f:
        data = json.loads(f.read().decode("utf-8"))

    all_items = data.get("data", [])
    print(f"Total annotations: {len(all_items)}")

    # Filter: has image URL and question length < 50
    candidates = []
    for item in all_items:
        q = item.get("question", "")
        url1 = item.get("flickr_300k_url", "")
        url2 = item.get("flickr_original_url", "")
        answers = item.get("answers", [])
        if (url1 or url2) and len(q) < MAX_QUESTION_LEN:
            candidates.append({
                "urls": [url1, url2],
                "question": q,
                "answers": answers,
            })

    print(f"Candidates: {len(candidates)}")

    # Process more than needed to account for failures
    sample_count = min(TARGET_COUNT * 10, len(candidates))
    sampled = random.sample(candidates, sample_count)
    print(f"Sampled {sample_count} for download attempts...")

    # Download images
    saved = []
    idx = 0
    for item in sampled:
        if len(saved) >= TARGET_COUNT:
            break

        # Try both URLs
        content = None
        for url in item["urls"]:
            if not url:
                continue
            content = _try_download(url, timeout=10)
            if content:
                break
            time.sleep(0.5)

        if not content:
            continue

        filename = f"textvqa_{idx:04d}.jpg"
        path = os.path.join(IMAGE_DIR, filename)
        with open(path, "wb") as out:
            out.write(content)

        saved.append({
            "image_path": f"data/textvqa_images/{filename}",
            "question": item["question"],
            "answers": item["answers"],
        })
        idx += 1

        if idx % 25 == 0:
            print(f"  Saved {idx}/{TARGET_COUNT} (processed {len(saved)} so far)")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)

    print(f"\nSuccessfully saved: {len(saved)} items")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
