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
  <form method="post">
    <label>食品名：</label>
    <input type="text" name="word" required>
    <input type="submit" value="照合">
  </form>
  {% if result %}
    <h3>照合結果：</h3>
    <ul>
      {% for line in result %}
        <li>{{ line }}</li>
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
        result = 参照.check_food(word)
    return render_template_string(HTML_FORM, result=result)

