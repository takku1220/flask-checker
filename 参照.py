import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fugashi import Tagger
import unidic_lite
import pykakasi
kks = pykakasi.kakasi()

# MeCab設定
os.environ["MECABRC"] = os.path.join(unidic_lite.DICDIR, "dicrc")
tagger = Tagger()

# ひらがな変換＋トークン化
def to_hiragana_tokens(text):
    kana_map = str.maketrans(
        "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンヴー",
        "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぶー"
    )
    tokens = []
    for m in tagger(text):
        if len(m.feature) > 7 and m.feature[7] not in (None, "*"):
            raw = m.feature[7]
            clean = str(raw).split("-")[0]
            hira = clean.translate(kana_map).lower()
            tokens.append(hira)
        else:
            # fallback: pykakasiで分割読みを補完
            conv = kks.convert(m.surface)
            for item in conv:
                hira = item['hira'].translate(kana_map).lower()
                tokens.append(hira)
    return tokens

# トークン照合（部分一致・助詞「の」除外）
def token_match(input_text, target_text):
    ignore_tokens = {"の", "（", "(", "）", ")"}  # 除外したい語をここに追加
    input_tokens = [tok for tok in to_hiragana_tokens(input_text) if tok not in ignore_tokens]
    target_tokens = to_hiragana_tokens(target_text)
    return any(tok in target_tokens for tok in input_tokens)

# Googleスプレッドシートからデータ取得
def get_sheet_data(sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    with open("food-checker-473911-784ac676008b.json", "r") as f:
        json_str = f.read()
    creds_dict = json.loads(json_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("石山の規約情報")
    worksheet = spreadsheet.worksheet(sheet_name)
    return worksheet.get_all_values()

# OpenFoodFacts APIから原材料を取得
def get_ingredients_from_openfoodfacts(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&action=process&json=1"
    res = requests.get(url).json()
    if not res.get("products"):
        return []
    code = res["products"][0]["code"]
    detail_url = f"https://world.openfoodfacts.org/api/v0/product/{code}.json"
    detail_res = requests.get(detail_url).json()
    product = detail_res.get("product", {})
    ingredients_text = product.get("ingredients_text", "")
    return [i.strip() for i in ingredients_text.replace("、", ",").split(",") if i.strip()]

# 照合関数（Flaskから呼び出す）
def check_food(text):
    sheets = ["不食品", "可食品"]
    normalized_input = text.strip()
    results = []

    # 🥚 イースターエッグ：「かい」に反応（照合は続行）
    reading = "".join([
        m.feature[7] if len(m.feature) > 7 and m.feature[7] not in (None, "*") else m.surface
        for m in tagger(normalized_input)
    ])
    kana_map = str.maketrans(
        "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンヴー",
        "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぶー"
    )
    reading_hira = reading.translate(kana_map).lower()

    tokens = to_hiragana_tokens(normalized_input)

    if any("かい" in token for token in tokens):
        results.append("『かい』！...www")


    # ① 食品名で照合
    for sheet_name in sheets:
        rows = get_sheet_data(sheet_name)
        for row in rows[3:]:
            b_val = row[1] if len(row) > 1 else ""
            c_val = row[2] if len(row) > 2 else ""
            if not b_val:
                continue
            if c_val:
                c_val = str(c_val).replace("{", "（").replace("}", "）")
            if normalized_input.lower() == b_val.strip().lower():
                msg = f"✅ {sheet_name}に完全一致しました：{b_val}" + (f"（備考：{c_val}）" if c_val else "")
                results.append(msg)
                return results
            elif token_match(normalized_input, b_val):
                msg = f"🔍 {sheet_name}に部分一致しました：{b_val}" + (f"（備考：{c_val}）" if c_val else "")
                results.append(msg)

    # ② 食品名で照合できなかった場合 → 原材料をAPIで取得して再照合
    if not results:
        ingredients = get_ingredients_from_openfoodfacts(normalized_input)
        if not ingredients:
            results.append('⚠️ 判定不能です。<a href="https://forms.gle/8YMNuueEZqaEKAox8" target="_blank">Googleフォーム</a>もしくはLINE、Slack等で連絡してください。')
            return results

        results.append(f"🔍 OpenFoodFactsから原材料を取得しました：{', '.join(ingredients)}")

        for ing in ingredients:
            for sheet_name in sheets:
                rows = get_sheet_data(sheet_name)
                for row in rows[3:]:
                    b_val = row[1] if len(row) > 1 else ""
                    c_val = row[2] if len(row) > 2 else ""
                    if not b_val:
                        continue
                    if c_val:
                        c_val = str(c_val).replace("{", "（").replace("}", "）")
                    if ing.lower() == b_val.strip().lower():
                        msg = f"✅ 原材料「{ing}」が {sheet_name} に完全一致しました" + (f"（備考：{c_val}）" if c_val else "")
                        results.append(msg)
                        break
                    if token_match(ing, b_val):
                        msg = f"🔍 原材料「{ing}」が {sheet_name} に部分一致しました：{b_val}" + (f"（備考：{c_val}）" if c_val else "")
                        results.append(msg)
                        break

        if len(results) == 1:
            results.append('⚠️ 原材料も照合できませんでした。<a href="https://forms.gle/8YMNuueEZqaEKAox8" target="_blank">Googleフォーム</a>もしくはLINE、Slack等で連絡してください。')

    return results
