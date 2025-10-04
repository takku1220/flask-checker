from flask import Flask, request, render_template_string
import 参照

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
  <title>石山　食品照合チェッカー</title>
  <style>
    body {
  font-family: sans-serif;
  margin: 40px;
  background-image: url("/static/images/20230903_054659.jpg"); /* ← 画像のパス */
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center;
  background-attachment: fixed;
}
    input[type="text"] {
      width: 100%;
      padding: 12px;
      font-size: 1.2em;
      box-sizing: border-box;
    }
    input[type="submit"] {
      margin-top: 10px;
      padding: 10px 20px;
      font-size: 1em;
    }
  </style>
</head>
<body>
  <h2>石山食品照合チェッカー</h2>
  <p style="font-size: 1.1em; color: gray;">石山に代わって食品の可否を即時判定します。ひらがな、カタカナ、漢字のいづれでも判定できます。</p>

  <form method="post">
    <label>食品名：</label>
    <input type="text" name="word" required>
    <input type="submit" value="照合">
  </form>
  {% if result %}
    <h3>照合結果：</h3>
    <ul>
      {% for line in result %}
        <li>{{ line|safe }}</li>
      {% endfor %}
    </ul>
  {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def form():
    result = None
    if request.method == 'POST':
        word = request.form.get('word', '')
        print(f"📩 入力された語句：{word}")  # ← これがRenderのログに出ます！
        result = 参照.check_food(word)
        print("🔍 照合結果：")
        for line in result:
            print(f"  - {line}")  # ← 結果もログに出ます
    return render_template_string(HTML_FORM, result=result)
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)






