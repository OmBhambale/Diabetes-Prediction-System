import React, { useState } from 'react';

// URL for the Flask backend endpoint (Ensure your Flask server is running here)
const API_URL = 'http://127.0.0.1:4000/predict'; 

// Define the 8 raw input fields needed by the model
const RAW_INPUT_FIELDS = [
    { name: 'Pregnancies', type: 'number', label: '1. Pregnancies (Count)' },
    { name: 'Glucose', type: 'number', label: '2. Glucose (mg/dL)' },
    { name: 'BloodPressure', type: 'number', label: '3. Blood Pressure (mm Hg)' },
    { name: 'SkinThickness', type: 'number', label: '4. Skin Thickness (mm)' },
    { name: 'Insulin', type: 'number', label: '5. Insulin (mu U/ml)' },
    { name: 'BMI', type: 'number', label: '6. BMI (kg/m²)' },
    { name: 'DiabetesPedigreeFunction', type: 'number', label: '7. Diabetes Pedigree Function' },
    { name: 'Age', type: 'number', label: '8. Age (Years)' },
];

function PredictionForm() {
    // Initialize state with default values for the 8 features
    const [formData, setFormData] = useState({
        Pregnancies: 0, Glucose: 0, BloodPressure: 0, SkinThickness: 0, 
        Insulin: 0, BMI: 0, DiabetesPedigreeFunction: 0.0, Age: 0 
    });
    const [predictionResult, setPredictionResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Handles changes in the input fields, ensuring they are stored as numbers
    const handleChange = (e) => {
        const value = parseFloat(e.target.value);
        setFormData({ 
            ...formData, 
            [e.target.name]: isNaN(value) ? 0 : value 
        });
    };

    // Handles form submission and API call
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setPredictionResult(null);
        setError(null);

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Send the raw data object to the Flask server
                body: JSON.stringify(formData), 
            });

            const result = await response.json();

            if (!response.ok) {
                // Handle errors returned by the Flask backend
                throw new Error(result.error || `HTTP error: ${response.status}`);
            }

            setPredictionResult(result);
        } catch (err) {
            console.error("API Error:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: '800px', margin: '50px auto', padding: '30px', boxShadow: '0 4px 8px rgba(0,0,0,0.1)', borderRadius: '10px', backgroundColor: '#ffffffff' }}>
            <h2 style={{ textAlign: 'center', color: '#333' }}>🧬 Diabetes Risk Assessment</h2>
            
            <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '25px', marginTop: '20px' }}>
                {RAW_INPUT_FIELDS.map((field) => (
                    <div key={field.name}>
                        <label htmlFor={field.name} style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#555' }}>
                            {field.label}:
                        </label>
                        <input
                            type={field.type}
                            name={field.name}
                            value={formData[field.name]}
                            onChange={handleChange}
                            required
                            min="0"
                            step={field.name === 'DiabetesPedigreeFunction' || field.name === 'BMI' ? "0.01" : "1"}
                            style={{ width: '100%', padding: '10px', boxSizing: 'border-box', border: '1px solid #ccc', borderRadius: '5px', fontSize: '16px' }}
                        />
                    </div>
                ))}
                <button 
                    type="submit" 
                    disabled={loading} 
                    style={{ gridColumn: '1 / -1', padding: '12px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '18px', fontWeight: 'bold' }}>
                    {loading ? 'Analyzing Data...' : 'Get Risk Prediction'}
                </button>
            </form>

            {/* Prediction Output / Error Handling */}
            <div style={{ gridColumn: '1 / -1', marginTop: '30px', textAlign: 'center' }}>
                {error && (
                    <div style={{ color: '#000000ff', padding: '15px', border: '1px solid #dc3545', backgroundColor: '#dc3545', borderRadius: '5px' }}>
                        **Server Error:** {error}
                    </div>
                )}

                {predictionResult && (
                    <div style={{ 
                        padding: '20px', 
                        border: predictionResult.prediction === 1 ? '3px solid #dc3545' : '3px solid #28a745', 
                        borderRadius: '8px', 
                        backgroundColor: predictionResult.prediction === 1 ? '#ffffffff' : '#ffffffff',
                        marginTop: '20px',
                        
                    }}>
                        <h3>Prediction Result: 
                            <span style={{ color: predictionResult.prediction === 1 ? '#dc3545' : '#28a745' }}> 
                                {predictionResult.result_text}
                            </span>
                        </h3>
                        <p style={{ fontSize: '1.1em' }}>Probability of being Diabetic: {(predictionResult.probability_diabetic * 100).toFixed(2)}%</p>
                        <p style={{ fontSize: '1.1em' }}>Probability of being Healthy: {(predictionResult.probability_healthy * 100).toFixed(2)}%</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default PredictionForm;