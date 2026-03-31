from flask import Flask, render_template, request, session, redirect, url_for
import random
import os

app = Flask(__name__)

#セッションのためのシークレットを作成
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# ポケモンの全タイプをリストに入れておく
pokemonType = [
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
    "Fighting", "Poison", "Ground", "Flying", "Psychic",
    "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
]

# 各ポケモンタイプの弱点(x2倍)を辞書で管理する
weaknesses = {
    "Normal": ["Fighting"],
    "Fire": ["Water", "Rock", "Ground"],
    "Water": ["Electric", "Grass"],
    "Electric": ["Ground"],
    "Grass": ["Fire", "Ice", "Poison", "Flying", "Bug"],
    "Ice": ["Fire", "Fighting", "Rock", "Steel"],
    "Fighting": ["Flying", "Psychic", "Fairy"],
    "Poison": ["Ground", "Psychic"],
    "Ground": ["Water", "Grass", "Ice"],
    "Flying": ["Electric", "Ice", "Rock"],
    "Psychic": ["Bug", "Ghost", "Dark"],
    "Bug": ["Fire", "Flying", "Rock"],
    "Rock": ["Water", "Grass", "Fighting", "Ground", "Steel"],
    "Ghost": ["Ghost", "Dark"],
    "Dragon": ["Ice", "Dragon", "Fairy"],
    "Dark": ["Fighting", "Bug", "Fairy"],
    "Steel": ["Fire", "Fighting", "Ground"],
    "Fairy": ["Poison", "Steel"]
}

# 各ポケモンタイプの長点(x1/2倍)を辞書で管理する
strength = {
    "Normal": ["Ghost"],
    "Fire": ["Bug", "Fire", "Fairy", "Grass", "Ice", "Steel"],
    "Water": ["Fire", "Ice", "Steel", "Water"],
    "Electric": ["Electric", "Flying", "Steel"],
    "Grass": ["Electric", "Grass", "Ground", "Water"],
    "Ice": ["Ice"],
    "Fighting": ["Bug", "Dark", "Rock"],
    "Poison": ["Bug", "Fighting", "Fairy", "Grass", "Poison"],
    "Ground": ["Poison", "Rock", "Electric"],
    "Flying": ["Bug", "Fighting", "Grass", "Ground"],
    "Psychic": ["Fighting", "Psychic"],
    "Bug": ["Fighting", "Grass", "Ground"],
    "Rock": ["Fire", "Flying", "Normal", "Poison"],
    "Ghost": ["Bug","Poison","Normal", "Fighting"],
    "Dragon": ["Electric","Fire", "Grass", "Water"],
    "Dark": ["Dark","Ghost","Psychic"],
    "Steel": ["Bug","Dragon","Flying", "Fairy", "Grass", "Ice", "Normal", "Psychic", "Rock", "Steel"],
    "Fairy": ["Bug", "Dark", "Fighting", "Dragon"]
}

# 存在しない複合タイプ(https://nonbirimaru.net/multiple-types/#toc1)を辞書で管理する
invalid_combinations = {
    ("Normal", "Rock"), ("Normal", "Bug"), ("Normal", "Ice"),
    ("Normal", "Steel"),("Fire", "Fairy"), ("Ground", "Fairy"),
    ("Ice", "Poison"), ("Bug", "Dragon"), ("Rock", "Ghost")
}

#新しい問題を作って session に保存する
def make_new_question():

    # 単タイプ or 複合タイプをランダムに選ぶ
    while True:
      type1 = random.choice(pokemonType)
      type2 = random.choice(pokemonType) if random.random() < 0.5 else None # 50%の確率で複合タイプ

      # 無効な組み合わせを排除
      if type2 and (type1 == type2 or (type1, type2) in invalid_combinations or (type2, type1) in invalid_combinations):
          continue  # やり直し
      break

    print("type1 =", type1)
    print("type2 =", type2)
    
    weakness_list = set()
    
    # type1 の弱点を追加
    if type1 in weaknesses:
        weakness_list.update(weaknesses[type1])
    
    # type2 の弱点を追加（複合タイプの場合）
    if type2 and type2 in weaknesses:
        weakness_list.update(weaknesses[type2])

    # それぞれの長点を弱点リストから削除
    if type1 in strength:
      for strong_type in strength[type1]:
          weakness_list.discard(strong_type)

    if type2 and type2 in strength:
      for strong_type in strength[type2]:
          weakness_list.discard(strong_type)

    session["type1"] = type1
    session["type2"] = type2
    session["answers"] = list(weakness_list)
    session["display_types"] = list(pokemonType)

def make_hint_choices():
    correct_answers = session["answers"]
    wrong_answers = [t for t in pokemonType if t not in correct_answers]

    target_count = max(8, len(correct_answers))
    wrong_count = min(len(wrong_answers), target_count - len(correct_answers))

    selected_wrong = random.sample(wrong_answers, wrong_count)

    hint_choices = list(correct_answers) + selected_wrong
    random.shuffle(hint_choices)

    session["display_types"] = hint_choices

@app.route('/', methods=["GET", "POST"])
def home():
    result = None

    if "score" not in session:
      session["score"] = 0

    #最初にページを開いたときだけ問題を作成する
    if "type1" not in session or "display_types" not in session:
        make_new_question()

    #ユーザーの選択とセッションに入れた正解を比べて答え合わせをする
    if request.method == "POST":
        user_answer = request.form["user_answer"]
        correct_answers = session["answers"]

        if user_answer in correct_answers:
            session["score"] += 1
            result = f"Correct! {user_answer} is right! The correct answer is {', '.join(sorted(correct_answers))}."
        else:
            result = f"Wrong! You chose {user_answer}. The correct answer is {', '.join(sorted(correct_answers))}."

    # 出題
    if session.get("type2"):
      question_text = f'What are {session["type1"]}/{session["type2"]}-type Pokémon weak against?'
    else:
      question_text = f'What are {session["type1"]}-type Pokémon weak against?'

    return render_template(
        "index.html",
        question=question_text,
        types=session.get("display_types", pokemonType),
        result=result,
        score=session["score"]
    )

@app.route("/hint", methods=["POST"])
def show_hint():
    make_hint_choices()
    return redirect(url_for("home"))

@app.route("/next", methods=["POST"])
def next_question():
    make_new_question()
    return redirect(url_for("home"))

@app.route("/restart", methods=["POST"])
def restart_question():
    session.clear()
    session["score"] = 0
    make_new_question()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)