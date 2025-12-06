import flask
import pickle
import pandas as pd
import numpy as np
from flask_cors import CORS
from flask import jsonify, request

# --- 1. CONFIGURATION AND MODEL LOADING ---

# The 16 features the model was trained on, in the exact required order
X_TRAIN_COLS = ['BloodPressure', 'Insulin', 'DiabetesPedigreeFunction', 'Age',
                'PRE_AGE_CAT', 'INSULIN_GLUCOSE_CAT', 'NEW_BMI_CAT_obese',
                'NEW_BMI_CAT_overweight', 'NEW_BMI_CAT_underweight',
                'NEW_GLUCOSE_CAT_low', 'NEW_GLUCOSE_CAT_normal',
                'NEW_GLUCOSE_CAT_very_high', 'NEW_PREGNANCIES_std_pregnancies',
                'NEW_SKIN_THICKNESS_normal', 'NEW_CIRCULATION_LEVEL_medium_risk',
                'NEW_CIRCULATION_LEVEL_normal']

# The 8 raw features expected from the React frontend
RAW_INPUT_COLS = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
                  'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']

# IMPORTANT: Load the trained model. Ensure you saved the GridSearchCV's best_estimator_.
try:
    with open('trained_model.pkl', 'rb') as f:
        LOADED_MODEL = pickle.load(f)
except FileNotFoundError:
    print("Error: trained_model.pkl not found. Please ensure the file is in the same directory.")
    LOADED_MODEL = None

app = flask.Flask(__name__)
CORS(app,  origins=["http://localhost:5173","http://localhost:5174", "http://localhost:3000"],supports_credentials=True,methods=['GET', 'POST', 'OPTIONS'],) # Enable CORS for frontend connection

# --- 2. FEATURE ENGINEERING LOGIC REPLICATION ---
# Note: Imputation logic is skipped here as the web app must only deal with valid inputs
# or use pre-calculated medians from the training set, not the complex train-time logic.

def create_new_bmi(df):
    new_cat = "NEW_BMI_CAT"
    # Note: Using .copy() to avoid SettingWithCopyWarning, though usually not needed for a single row
    df.loc[(df['BMI'] < 18.5), new_cat] = "underweight"
    df.loc[(df['BMI'] > 18.5) & (df['BMI'] < 25), new_cat] = "normal"
    df.loc[(df['BMI'] > 24) & (df['BMI'] < 30), new_cat] = "overweight"
    df.loc[(df['BMI'] > 30) & (df['BMI'] < 40), new_cat] = "obese"
    return df

def create_new_glucose(df):
    new_cat = "NEW_GLUCOSE_CAT"
    df.loc[(df['Glucose'] < 70), new_cat] = "low"
    df.loc[(df['Glucose'] > 70) & (df['Glucose'] < 99), new_cat] = "normal"
    df.loc[(df['Glucose'] > 99) & (df['Glucose'] < 126), new_cat] = "high"
    df.loc[(df['Glucose'] > 126) & (df['Glucose'] < 200), new_cat] = "very_high"
    return df

def create_new_pregnancies(df):
    new_cat = "NEW_PREGNANCIES"
    df.loc[df['Pregnancies'] == 0, new_cat] = "no_pregnancies"
    df.loc[(df['Pregnancies'] > 0) & (df['Pregnancies'] <= 4), new_cat] = "std_pregnancies"
    df.loc[(df['Pregnancies'] > 4), new_cat] = "over_pregnancies"
    return df

def create_new_skinthickness(df):
    new_cat = "NEW_SKIN_THICKNESS"
    df.loc[df['SkinThickness'] < 30, new_cat] = "normal"
    df.loc[df['SkinThickness'] >= 70, new_cat] = "highfat"
    return df

def create_circulation_level(df):
    new_cat = "NEW_CIRCULATION_LEVEL"
    df.loc[(df['SkinThickness'] < 30) & (df['BloodPressure'] < 80), new_cat] = "normal"
    df.loc[(df['SkinThickness'] > 30) & (df['BloodPressure'] >= 80), new_cat] = "high_risk"
    df.loc[((df['SkinThickness'] < 30) & (df['BloodPressure'] >= 80)) | ((df['SkinThickness'] > 30) & (df['BloodPressure'] < 80)), new_cat] = "medium_risk"
    df.drop('SkinThickness', axis=1, inplace=True)
    return df

def create_other_features(df):
    df['PRE_AGE_CAT'] = df['Age'] * df['Pregnancies']
    df['INSULIN_GLUCOSE_CAT'] = df['Insulin'] * df['Glucose']
    df.drop('Pregnancies', axis=1, inplace=True)
    df.drop('Glucose', axis=1, inplace=True)
    return df

def transform_input(raw_data_df):
    # Apply all feature creation steps
    df = create_new_bmi(raw_data_df.copy())
    df = create_new_glucose(df)
    df = create_new_pregnancies(df)
    df = create_new_skinthickness(df)
    df = create_circulation_level(df)
    df = create_other_features(df)

    # One-Hot Encoding (must ensure all 16 columns are created)
    categ_cols = [col for col in df.columns if col not in X_TRAIN_COLS and col not in RAW_INPUT_COLS]
    
    # Use get_dummies on the categorical columns
    df_encoded = pd.get_dummies(df, columns=categ_cols, drop_first=True)
    
    # Ensure all 16 columns are present (even if 0) and in the right order
    # This is crucial for fixing the NameError/ValueError you saw previously
    for col in X_TRAIN_COLS:
        if col not in df_encoded.columns:
            df_encoded[col] = 0
            
    # Select only the model's required columns and enforce the order
    final_df = df_encoded[X_TRAIN_COLS]
    
    return final_df

# --- 3. FLASK API ENDPOINT ---

@app.route('/predict', methods=['POST'])
def predict():
    if LOADED_MODEL is None:
        return jsonify({'error': 'Model not loaded. Check server logs.'}), 500
        
    try:
        data = request.get_json()
        
        # 1. Convert incoming JSON array (with 8 raw features) to a DataFrame
        raw_df = pd.DataFrame([data])
        
        # 2. Replicate entire feature engineering pipeline
        final_input_df = transform_input(raw_df)
        
        # 3. Run prediction
        prediction = LOADED_MODEL.predict(final_input_df)[0]
        probabilities = LOADED_MODEL.predict_proba(final_input_df)[0]
        
        # 4. Return results
        return jsonify({
            'prediction': int(prediction),
            'result_text': 'Diabetic' if prediction == 1 else 'Healthy',
            'probability_healthy': round(probabilities[0], 4),
            'probability_diabetic': round(probabilities[1], 4)
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred during prediction: {str(e)}'}), 500

if __name__ == '__main__':
    
    print("🚀 Flask Diabetes Prediction Server is attempting to start on port 4000...")
    
    # You can change the port here, e.g., port=8000
    app.run(host='0.0.0.0', debug=True, port=4000)