import streamlit as st
from google import genai
from PIL import Image

# --- style.css ファイルを読み込むコード ---
try:
    with open("style.css", "r", encoding="utf-8") as f:
        css_content = f.read()
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass
# ----------------------------------------

#生成されたレシピを記憶しておく場所
if "recipe_text" not in st.session_state:
    st.session_state.recipe_text = ""

#アプリのタイトル
st.title("レシピぐらい自分で考えろ")
st.write("仕方ないから冷蔵庫にある食材を俺らAIが見てやるよ")

#サイドバーで常備調味料を設定
st.sidebar.header("常備してる調味料")
st.sidebar.write("一つ以上はあるよね？")
seasonings = st.sidebar.multiselect(
    "持ってるものにチェックを入れろ",
    ["塩", "醤油", "味噌", "砂糖", "マヨネーズ", "ケチャップ", "ソース", "みりん", "酒", "酢", "油", "ニンニク", "ショウガ", "コンソメ", "鶏ガラ", "胡椒"],
    default=["塩", "醤油", "砂糖", "油", "胡椒"] # 最初からチェックされているもの
)
seasonings_text = ", ".join(seasonings) if seasonings else "何もなし(水のみ)"

st.divider() #横線を入れる

#　1.食材の入力エリア
st.subheader("食材を書け。")
ingredients = st.text_input("例: トマト、玉ねぎ、卵", placeholder = "ここに入力...")

#写真アップロード用ボタン
uploaded_file = st.file_uploader("または、冷蔵庫の中の写真をアップロード", type=["jpg", "jpeg", "png"])

# 2.気分ボタン
st.subheader("2. 今日の気分なに？")

#チェックボックスで複数選択可能にする
st.write("調理の条件を選べ。満足するまでな")
cond_1 = st.checkbox("10分以内で出来る")
cond_2 = st.checkbox("包丁を使いたくない")
cond_3 = st.checkbox("電子レンジだけで簡単調理")
cond_4 = st.checkbox("満腹になれる")
cond_5 = st.checkbox("ヘルシー・ダイエット中")

#自由入力欄の追加
custom_condition = st.text_input("その他、めんどくさいが細かい注文があればここだ", placeholder = "はよ")

st.divider() 

# 3.決定ボタン
if st.button("レシピを考えてくださいお願いします", use_container_width=True):
    if ingredients or uploaded_file:
        st.info("仕方なく考え中...(次のステップで動かしてやる)")

        try:
            #パソコンに保存したAPIキーを使ってgeminiを準備
            client = genai.Client()

            #選択されたチェックボックスを文章にまとめる処理
            selected_moods = []
            if cond_1: selected_moods.append("10分以内で出来る")
            if cond_2: selected_moods.append("包丁を使いたくない")
            if cond_3: selected_moods.append("電子レンジだけで簡単調理")
            if cond_4: selected_moods.append("満腹になれる")
            if cond_5: selected_moods.append("ヘルシー・ダイエット中")

            #何も選ばれていない場合は「こだわらん」にする
            mood_text = ", ".join(selected_moods) if selected_moods else "こだわらん"

            #自由入力欄に文字があれば追加する
            if custom_condition:
                mood_text += f"、さらに追加条件: {custom_condition}"

            #Aiへの指示文を作る
            prompt = f"""
            あなたは見かけは乱暴ですが、根は親切でプロの料理研究家です。提供された食材と条件に合わせて、以下の情報を分かりやすく日本語で出力してください。

            0. 今回の食材の組み合わせに対するセンスの採点(0-100点)と、手厳しい一言コメント
            1. 調理難易度 (「easy] [normal」「advanced」「professional」)の4段階から選べ
            2. おすすめのレシピ名
            3. 調理時間と必要な材料・手順
            4. 「もしこの食材(1つ)を買い足したら、こんな別メニューも作れますよ」という提案
            5. 今回使う食材の豆知識や栄養素、保存方法のワンポイント
            6. すべての説明は、言葉使いが荒く、上から目線で(ただしレシピ自体は親切で正確に)出力すること

            【条件】
            ・利用可能な食材: {ingredients}
            ・利用可能な調味料: {seasonings_text}
            ・調理の希望: {mood_text}
            """

            #写真がアップロードされている場合は、写真も一緒にAIに送る
            contents = [prompt]
            if uploaded_file is not None:
                img = Image.open(uploaded_file)
                contents.append(img)
            
            #Geminiに質問を投げる
            response = client.models.generate_content(
                model='gemini-3.5-flash', #最新のやつ
                contents=contents
            )

            #結果をセッションステートに保存
            st.session_state.recipe_text = response.text

        except Exception as e:
            st.error("エラーだよ。API確認して。")
            st.write(e)

    else:
        st.warning("食材を入力しろ!! それか写真を今すぐ送れgm")

#保存(ダウンロード)ボタン
if st.session_state.recipe_text:
    st.success("レシピできた。")
    st.markdown(st.session_state.recipe_text)

    st.divider()
    st.subheader("レシピを保存？それともやり直し？")

    #ボタンを横並びにするために２つの列(カラム)を作る
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="レシピを「おそなえ」する",
            data=st.session_state.recipe_text,
            file_name="my_recipe.txt",
            mime="text/plain",
            use_container_width=True
    )

    with col2:
        #やり直しの確認用ポップオーバーを配置
        with st.popover("もういいのか？", use_container_width=True):
            st.warning("本当にやり直すのか？今あるレシピは消えるぞ。")

            #ポップオーバーの中に、本当の実行ボタンを配置する
            if st.button("やり直す", use_container_width=True, type="primary"):
                #記憶していたレシピを空っぽにする
                st.session_state.recipe_text = ""
                #画面を強制的に再起動して、表示を消す
                st.rerun()