import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")


# Load dataset
df = pd.read_csv(r"C:\Users\hp\Desktop\paddydataset\paddydataset.csv")

# Dataset overview
print("Dataset Shape:", df.shape)
print(df.head())

# Column names and data types
print("\nColumn Names:")
print(df.columns.tolist())

print("\nData Types:")
print(df.dtypes)

# Missing values
print("\nMissing Values:")
print(df.isnull().sum())
print("\nTotal Missing Values:", df.isnull().sum().sum())

# Duplicate rows
print("\nTotal Duplicate Rows:", df.duplicated().sum())

# Statistical summary
print("\nStatistical Summary:")
print(df.describe())

# 1. Distribution of Paddy Yield
plt.figure(figsize=(8, 5))
plt.hist(df["Paddy yield(in Kg)"], bins=20, edgecolor="black")
plt.title("Distribution of Paddy Yield")
plt.xlabel("Paddy Yield (in Kg)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

# 2. Correlation Heatmap
cols = [
    "Paddy yield(in Kg)",
    "Hectares ",
    "Seedrate(in Kg)",
    "30DRain( in mm)",
    "Min temp_D1_D30",
    "Max temp_D1_D30",
    "Relative Humidity_D1_D30"
]

plt.figure(figsize=(9, 6))
sns.heatmap(
    df[cols].corr(),
    annot=True,
    cmap="coolwarm",
    fmt=".2f"
)
plt.title("Correlation with Paddy Farming Factors")
plt.tight_layout()
plt.show()

# 3. Paddy Yield by Soil Type
plt.figure(figsize=(10, 6))
sns.boxplot(
    data=df,
    x="Soil Types",
    y="Paddy yield(in Kg)"
)
plt.title("Paddy Yield by Soil Type")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# Categorical columns analysis
print("\nCategorical Columns:")

cat_cols = df.select_dtypes(include="object").columns

for col in cat_cols:
    print("\n", col)
    print(df[col].value_counts().head(10))

print("\nAll Columns:")
for col in df.columns:
    print(col)


# Create yield categories for classification

df["Yield Category"] = pd.qcut(
    df["Paddy yield(in Kg)"],
    q=3,
    labels=["Low", "Medium", "High"]
)

print("\nYield Category Counts:")
print(df["Yield Category"].value_counts())

print("\nYield Category Percentages:")
print(
    (df["Yield Category"].value_counts(normalize=True) * 100).round(2)
)

# Duplicate analysis

print("Total Rows Before:", len(df))

print("Duplicate Rows:", df.duplicated().sum())

df = df.drop_duplicates()

print("Total Rows After:", len(df))

print("Remaining Duplicates:", df.duplicated().sum())

# Recreate target after removing duplicates

df["Yield Category"] = pd.qcut(
    df["Paddy yield(in Kg)"],
    q=3,
    labels=["Low", "Medium", "High"]
)

print("\nFinal Target Distribution:")
print(df["Yield Category"].value_counts())

X = df.drop(
    columns=["Paddy yield(in Kg)", "Yield Category"]
)

y = df["Yield Category"]

print("\nFeatures Shape:", X.shape)
print("Target Shape:", y.shape)

# Identify categorical and numerical columns

cat_cols = X.select_dtypes(include=["object"]).columns
num_cols = X.select_dtypes(include=["number"]).columns

print("Categorical Columns:")
print(cat_cols.tolist())

print("\nNumerical Columns:")
print(num_cols.tolist())

print("\nTotal Categorical Columns:", len(cat_cols))
print("Total Numerical Columns:", len(num_cols))


# Import libraries
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# Identify columns
cat_cols = X.select_dtypes(include=["str", "object"]).columns
num_cols = X.select_dtypes(include=["number"]).columns

# Numerical preprocessing
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])





# Categorical preprocessing
cat_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

# Combine preprocessing
preprocessor = ColumnTransformer([
    ("num", num_pipeline, num_cols),
    ("cat", cat_pipeline, cat_cols)
])

print("Preprocessing Pipeline Created Successfully!")
print("Numerical Columns:", len(num_cols))
print("Categorical Columns:", len(cat_cols))




from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training Data:", X_train.shape)
print("Testing Data:", X_test.shape)

print("\nTraining Target:")
print(y_train.value_counts())

print("\nTesting Target:")
print(y_test.value_counts())



#############
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# SVM Model
svm_model = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", SVC(kernel="rbf"))
])

# Train model
svm_model.fit(X_train, y_train)

# Prediction
svm_pred = svm_model.predict(X_test)

# Evaluation
print("\nSVM Results")
print("Accuracy:", accuracy_score(y_test, svm_pred))

print("\nClassification Report:")
print(classification_report(y_test, svm_pred))

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# Create Logistic Regression model
lr_model = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", LogisticRegression(max_iter=2000))
])

# Train model
lr_model.fit(X_train, y_train)

# Prediction
y_pred = lr_model.predict(X_test)

# Evaluation
print("\nLogistic Regression Results")

print("Accuracy:",
      accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

############

from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline

# Naive Bayes Model
nb_model = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", GaussianNB())
])

# Train model
nb_model.fit(X_train, y_train)

# Prediction
nb_pred = nb_model.predict(X_test)

# Evaluation
print("\nNaive Bayes Results")
print("Accuracy:", accuracy_score(y_test, nb_pred))

print("\nClassification Report:")
print(classification_report(y_test, nb_pred))


###########################################################################
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

# KNN Model
knn_model = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", KNeighborsClassifier(n_neighbors=5))
])

# Train model
knn_model.fit(X_train, y_train)

# Prediction
knn_pred = knn_model.predict(X_test)

# Evaluation
print("\nKNN Results")
print("Accuracy:", accuracy_score(y_test, knn_pred))

print("\nClassification Report:")
print(classification_report(y_test, knn_pred))


###################################################################################





from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# Decision Tree Model
dt_model = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", DecisionTreeClassifier(
        max_depth=8,
        random_state=42
    ))
])

# Train model
dt_model.fit(X_train, y_train)

# Prediction
dt_pred = dt_model.predict(X_test)

# Evaluation
print("\nDecision Tree Results")

print("Accuracy:",
      accuracy_score(y_test, dt_pred))

print("\nClassification Report:")
print(classification_report(y_test, dt_pred))




from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

rf_model = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42
    ))
])

rf_model.fit(X_train, y_train)

rf_pred = rf_model.predict(X_test)

print("\nRandom Forest Results")
print("Accuracy:", accuracy_score(y_test, rf_pred))

print("\nClassification Report:")
print(classification_report(y_test, rf_pred))







#confusion matrix
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(7, 5))

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=["High", "Low", "Medium"],
    yticklabels=["High", "Low", "Medium"]
)

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Logistic Regression - Confusion Matrix")

plt.show()





# Compare all 5 classification models

from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

models = [
    "SVM",
    "Naive Bayes",
    "KNN",
    "Logistic Regression",
    "Decision Tree"
]

accuracies = [
    accuracy_score(y_test, svm_pred),
    accuracy_score(y_test, nb_pred),
    accuracy_score(y_test, knn_pred),
    accuracy_score(y_test, y_pred),
    accuracy_score(y_test, dt_pred)
]

plt.figure(figsize=(10, 6))

plt.bar(models, accuracies)

plt.ylabel("Accuracy")
plt.xlabel("Classification Algorithms")
plt.title("Accuracy Comparison of 5 Classification Models")
plt.ylim(0, 1)

plt.xticks(rotation=20)

for i, value in enumerate(accuracies):
    plt.text(i, value + 0.01, f"{value*100:.2f}%", ha="center")

plt.tight_layout()
plt.show()

print("\nModel Accuracy Results:")

for model, accuracy in zip(models, accuracies):
    print(model, ":", round(accuracy * 100, 2), "%")
