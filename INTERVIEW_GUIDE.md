# Interview Guide — Explain the Project Simply

## 30-second explanation

“I built a network intrusion detection system that analyzes network-flow features from labelled traffic data. XGBoost identifies known attack classes, while an autoencoder is trained on benign traffic and flags records that behave unusually. I then show the predictions, anomaly scores and risk levels on a Streamlit dashboard.”

## Why XGBoost?

The traffic data is structured/tabular. XGBoost is strong for tabular classification, handles nonlinear relationships, and gives a practical baseline without requiring a very large deep-learning model.

## Why an autoencoder too?

A supervised classifier learns known labels. The autoencoder learns how benign traffic normally looks. If a record reconstructs poorly, its reconstruction error is high and it can be flagged as anomalous even when the classifier is uncertain.

## What is reconstruction error?

The autoencoder tries to reproduce its input. The difference between original and reconstructed feature values is the reconstruction error. A high error means the record does not look like the benign examples the model learned.

## Why not use accuracy only?

Cybersecurity datasets can be imbalanced. Precision, recall and F1-score are useful because they show how well attacks are detected and how many false alarms are produced.

## What is the limitation?

This is an offline ML prototype using network-flow CSVs. A production IDS would need continuous packet/flow collection, concept-drift monitoring, stronger validation, model versioning, security hardening and real-time alert integration.

## Honest answers to likely questions

**Is it a real-time IDS?**  
Not yet. The current version analyzes uploaded/recorded network-flow CSVs. The design can later be connected to live flow collectors.

**Does the autoencoder identify the exact unknown attack?**  
No. It flags unusual behavior. Exact attribution would require additional analysis or labels.

**Did you create the CICIDS dataset?**  
No. It is a public intrusion-detection research dataset from the Canadian Institute for Cybersecurity at the University of New Brunswick.
