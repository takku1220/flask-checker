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

# 読み仮名全体をひらがなに変換
def to_hiragana(text):
    kana_map = str.maketrans(
        "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンヴー",
        "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぶー"
    )
    reading = "".join([
        m.feature[7] if len(m.feature) > 7 and m.feature[7] not in (None, "*") else m.surface
        for m in tagger(text)
    ])
    return reading.translate(kana_map).lower()

# トークン照合（助詞除外）
def token_match(input_text, target_text):
    ignore_tokens = {"の"}
    input_tokens = [tok for tok in to_hiragana_tokens(input_text) if tok not in ignore_tokens]
    target_tokens = to_hiragana_tokens(target_text)
    return any(tok in target_tokens for tok in input_tokens)

# 照合関数（Flaskから呼び出す）
def check_food(text):
    sheets = ["不食品", "可食品"]
    normalized_input = text.strip()
    results = []

    # 🥚 イースターエッグ：読み仮名に「かい」が含まれていたら発動（照合は続行）
    reading_hira = to_hiragana(normalized_input)
    if "かい" in reading_hira:
        results.append("『貝瀬』！...www")

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
            if token_match(normalized_input, b_val):
                msg = f"🔍 {sheet_name}に部分一致しました：{b_val}" + (f"（備考：{c_val}）" if c_val else "")
                results.append(msg)

    # ② 原材料照合
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
