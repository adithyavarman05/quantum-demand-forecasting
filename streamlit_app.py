"""
Streamlit Web App: Quantum AI Electricity Demand Forecasting
Run:  streamlit run streamlit_app.py   (after running quantum_demand_forecasting.py)
Student: Adithya Varman Nandhivarman
"""
import os
import numpy as np
import joblib
import streamlit as st
import pennylane as qml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="Quantum Demand Forecasting",
    page_icon="⚡",
    layout="wide",
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 800;
    }
    .sub-header {
        text-align: center;
        color: #b0b0d0;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        color: #9090b0;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚡ Quantum AI Electricity Demand Forecasting</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Hybrid Variational Quantum Circuit (VQC) vs Linear Regression  •  PennyLane + Streamlit</div>', unsafe_allow_html=True)

# ---------- Load Artifacts ----------
artifacts_path = os.path.join(BASE_DIR, "artifacts.joblib")
try:
    art = joblib.load(artifacts_path)
except FileNotFoundError:
    st.error("⚠️ Run `python quantum_demand_forecasting.py` first to train the model.")
    st.stop()

N_QUBITS = 4
dev = qml.device("default.qubit", wires=N_QUBITS)


@qml.qnode(dev)
def vqc(x, w):
    qml.AngleEmbedding(np.pi * x, wires=range(N_QUBITS), rotation="X")
    qml.StronglyEntanglingLayers(w, wires=range(N_QUBITS))
    return qml.expval(qml.PauliZ(0))


# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["🔮 Predict", "📊 Results", "🔬 Circuit"])

# ===== TAB 1: Predict =====
with tab1:
    st.subheader("Enter the last 4 hourly demand values (MW)")
    st.caption("These are used as lag features (t-4, t-3, t-2, t-1) to predict the next hour's demand.")

    defaults = art["last_values"]
    cols = st.columns(4)
    vals = []
    for i, c in enumerate(cols):
        v = c.number_input(
            f"t−{4-i} h",
            value=float(defaults[i]),
            step=100.0,
            format="%.1f",
            key=f"input_{i}",
        )
        vals.append(v)

    if st.button("⚡ Predict Next Hour", type="primary", use_container_width=True):
        x_scaled = np.clip(art["x_scaler"].transform([vals])[0], 0, 1)

        # VQC prediction
        q_out = vqc(x_scaled, art["weights"])
        pred_q = art["y_scaler"].inverse_transform([[float(q_out)]])[0, 0]

        # Linear Regression prediction
        lr_out = art["lr_model"].predict([x_scaled])[0]
        pred_l = art["y_scaler"].inverse_transform([[float(lr_out)]])[0, 0]

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">⚛️ VQC (Quantum) Prediction</div>
                <div class="metric-value">{pred_q:,.2f} MW</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📐 Linear Regression Prediction</div>
                <div class="metric-value">{pred_l:,.2f} MW</div>
            </div>
            """, unsafe_allow_html=True)

# ===== TAB 2: Results =====
with tab2:
    st.subheader("📊 Model Performance Comparison")

    mv = art["metrics_vqc"]
    ml = art["metrics_lr"]
    vqc_time = art.get("vqc_time", "N/A")
    lr_time = art.get("lr_time", "N/A")
    n_params_vqc = art.get("n_params_vqc", "N/A")
    n_params_lr = art.get("n_params_lr", "N/A")

    # Metrics table
    st.table({
        "Metric": ["MAE (MW)", "RMSE (MW)", "R²", "Train Time (s)", "Parameters"],
        "VQC (Quantum)": [
            f"{mv[0]:.4f}", f"{mv[1]:.4f}", f"{mv[2]:.4f}",
            f"{vqc_time:.2f}" if isinstance(vqc_time, float) else str(vqc_time),
            str(n_params_vqc),
        ],
        "Linear Regression": [
            f"{ml[0]:.4f}", f"{ml[1]:.4f}", f"{ml[2]:.4f}",
            f"{lr_time:.4f}" if isinstance(lr_time, float) else str(lr_time),
            str(n_params_lr),
        ],
    })

    # Show plots
    results_img = os.path.join(BASE_DIR, "results_plots.png")
    if os.path.exists(results_img):
        st.image(results_img, caption="Actual vs Predicted | Training Loss | Model Comparison")
    else:
        st.warning("results_plots.png not found.")

# ===== TAB 3: Circuit =====
with tab3:
    st.subheader("🔬 Variational Quantum Circuit Architecture")
    st.markdown("""
    - **Qubits:** 4 (one per lag feature)
    - **Encoding:** `AngleEmbedding` with RX gates (angle = π × x)
    - **Ansatz:** `StronglyEntanglingLayers` (2 layers) — each layer applies Rot gates + CNOT entanglement
    - **Measurement:** Expectation value of PauliZ on qubit 0
    - **Differentiation:** Backpropagation on simulator (`default.qubit`, `diff_method="backprop"`)
    """)

    circuit_img = os.path.join(BASE_DIR, "quantum_circuit.png")
    if os.path.exists(circuit_img):
        st.image(circuit_img, caption="4-qubit VQC: AngleEmbedding + StronglyEntanglingLayers (2 layers)")
    else:
        st.warning("quantum_circuit.png not found.")
