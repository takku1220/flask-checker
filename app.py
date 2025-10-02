from flask import Flask, request, render_template_string
import 参照

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head><title>食品照合フォーム</title></head>
<body>
  <h2>食品照合フォーム</h2>
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
