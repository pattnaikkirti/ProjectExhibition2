import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,classification_report
import joblib

df = pd.read_csv("isl_landmarks.csv")
print("Dataset shape : ",df.shape)
print("sample data : \n ",df.head())

x=df.drop("label",axis=1).values
y=df["label"].values

encoder= LabelEncoder()
y_encoded= encoder.fit_transform(y)
print("Classes : ", encoder.classes_)

x_train,x_test,y_train,y_test = train_test_split(x,y_encoded,test_size=0.2,random_state=42,)

clf = RandomForestClassifier(n_estimators=200,random_state=42)
clf.fit(x_train,y_train)

y_pred = clf.predict(x_test)
print("Accuracy : ",accuracy_score(y_test,y_pred))
unique_lables = np.unique(y_test)
target_names = encoder.inverse_transform(unique_lables)
print("\nClassification Report : \n",classification_report(y_test,y_pred,target_names=target_names))

joblib.dump(clf,"isl_model.pkl")
joblib.dump(encoder,"isl_label_encoder.pkl")
print("model encoder saved as 'isl_model.pkl' and 'isl_label_encoder.pkl'")