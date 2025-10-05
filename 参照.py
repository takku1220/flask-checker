import requests

# OpenFoodFacts APIから原材料を取得
def get_ingredients_from_openfoodfacts(product_name):
    url = f"https://world.openfoodfacts.org/api/v0/product/{product_name}.json"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    if data.get("status") != 1:
        return []
    product = data.get("product", {})
    ingredients_text = product.get("ingredients_text", "")
    return [i.strip() for i in ingredients_text.replace("、", ",").split(",") if i.strip()]

# 照合関数（Flaskから呼び出す）
def check_food(text):
    sheets = ["不食品", "可食品"]
    normalized_input = text.strip()
    results = []

    # ① 食品名で照合
    for sheet_name in sheets:
        rows = get_sheet_data(sheet_name)
        for row in rows[3:]:  # 4行目から照合開始
            b_val = row[1] if len(row) > 1 else ""
            c_val = row[2] if len(row) > 2 else ""

            if not b_val:
                continue

            if c_val:
                c_val = str(c_val).replace("{", "（").replace("}", "）")

            # 完全一致
            if normalized_input.lower() == b_val.strip().lower():
                msg = f"✅ {sheet_name}に完全一致しました：{b_val}" + (f"（備考：{c_val}）" if c_val else "")
                results.append(msg)
                return results

            # 部分一致
            if token_match(normalized_input, b_val):
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

                    # 完全一致
                    if ing.lower() == b_val.strip().lower():
                        msg = f"✅ 原材料「{ing}」が {sheet_name} に完全一致しました" + (f"（備考：{c_val}）" if c_val else "")
                        results.append(msg)
                        break

                    # 部分一致
                    if token_match(ing, b_val):
                        msg = f"🔍 原材料「{ing}」が {sheet_name} に部分一致しました：{b_val}" + (f"（備考：{c_val}）" if c_val else "")
                        results.append(msg)
                        break

        if len(results) == 1:
            results.append('⚠️ 原材料も照合できませんでした。<a href="https://forms.gle/8YMNuueEZqaEKAox8" target="_blank">Googleフォーム</a>もしくはLINE、Slack等で連絡してください。')

    return results
