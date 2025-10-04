from fugashi import Tagger
import unidic_lite
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
        raw = m.feature[7] if len(m.feature) > 7 and m.feature[7] not in (None, "*") else m.surface
        clean = str(raw).split("-")[0]
        hira = clean.translate(kana_map).lower()
        tokens.append(hira)
    return tokens

# トークン照合（部分一致）
def token_match(input_text, target_text):
    input_tokens = to_hiragana_tokens(input_text)
    target_tokens = to_hiragana_tokens(target_text)
    return any(tok in target_tokens for tok in input_tokens)

# Googleスプレッドシートからデータ取得
def get_sheet_data(sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('food-checker-473911-f196582d590.json', scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("石山の規約情報")
    worksheet = spreadsheet.worksheet(sheet_name)
    return worksheet.get_all_values()

# 照合関数（Flaskから呼び出す）
def check_food(text):
    sheets = ["不食品", "可食品"]
    normalized_input = text.strip()
    results = []

    for sheet_name in sheets:
        rows = get_sheet_data(sheet_name)
        for row in rows[3:]:  # 4行目から照合開始
            b_val = row[1] if len(row) > 1 else ""
            c_val = row[2] if len(row) > 2 else ""

            if not b_val:
                continue

            if normalized_input.lower() == b_val.strip().lower():
                msg = f"✅ {sheet_name}に完全一致しました：{b_val}"
                if c_val:
                    msg += f"備考：{c_val}"
                results.append(msg)
                return results

            if token_match(normalized_input, b_val):
                msg = f"🔍 {sheet_name}に部分一致しました：{b_val}"
                if c_val:
                    msg += f"備考：{c_val}"
                results.append(msg)

    if not results:
        results.append('⚠️ 判定不能です。<a href="https://forms.gle/8YMNuueEZqaEKAox8" target="_blank">Googleフォーム</a>もしくはLINE、Slack等で連絡してください。')

    return results
