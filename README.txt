HEALTH MYTH BUSTER V2

Folder layout:
app.py
requirements.txt
data/myths.json

Replace your app.py with this app.py and replace data/myths.json with the included database.
Do not rename data/myths.json. The app intentionally supports both this path and a root data.json.

Run in VS Code terminal:
python -m pip install -r requirements.txt
python -m streamlit run app.py

Navigation is a horizontal 3-screen control so the app remains usable even when Streamlit's sidebar is collapsed. The app does not hide or override Streamlit's native sidebar toggle.

Database note: records are starter entries and marked needs_human_review. Source links are provided as research starting points, not proof that every individual verdict has been independently verified. Check each verdict against two relevant reliable sources and ask a teacher or qualified health professional to review the final list before competition submission.

Accuracy testing: ask at least 5 people to test 20+ claims in their own words, including claims outside the database. Record expected answer, app answer, correct/incorrect, then calculate accuracy = correct answers / total tests * 100. Do not invent test results.
